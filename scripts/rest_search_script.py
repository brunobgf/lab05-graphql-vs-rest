import requests as req
import pandas as pd
import time
import os

tokens = ['TOKEN 1', 'TOKEN 2']
current_token_index = 0
MIN_SLEEP = 60
MS_SLEEP = 0.1

def get_current_token():
    global current_token_index
    return tokens[current_token_index]

def switch_token():
    global current_token_index
    current_token_index = (current_token_index + 1) % len(tokens)

def get(url):
    token = get_current_token()
    start_time = time.time()
    response = req.get(url, headers={'Authorization': f'token {token}'})
    end_time = time.time()
    response_time = end_time - start_time
    response_size = len(response.content)

    if response.status_code == 200:
        return response.json(), response_time, response_size
    else:
        raise Exception(f'Request error: {response.status_code} \n {response.text}')

def fetch_repositories():
    repositories = []
    per_page = 1
    page = 1
    query_string = "stars:>0"
    
    total_time = 0
    total_size = 0
    response_times = []
    response_sizes = []
    
    while len(repositories) < 1000:
        url = f'https://api.github.com/search/repositories?q={query_string}&sort=stars&order=desc&per_page={per_page}&page={page}'
        
        try:
            data, response_time, response_size = get(url)
            response_times.append(response_time - MS_SLEEP)
            response_sizes.append(response_size)
            total_time += response_time - MS_SLEEP
            total_size += response_size
        except Exception as e:
            print(e)
            print("Waiting for 60 seconds before retrying...")
            time.sleep(MIN_SLEEP)
            continue
        
        switch_token()
        
        if 'errors' in data:
            print("API request failed:", data['errors'])
            continue

        print(f"Received {len(data['items'])} repositories in this batch.")

        repositories.extend(data['items'])
        
        if len(data['items']) < per_page:
            break
        
        page += 1
        time.sleep(MS_SLEEP)

    print()
    print(f"Total response time: {total_time:.3f} seconds")
    print(f"Total response size: {total_size} bytes")

    return repositories, response_times, response_sizes

def save_csv(data, response_times, response_sizes, filename):
    directory = '../scripts/dataset'

    if not os.path.exists(directory):
        os.makedirs(directory)

    filepath = os.path.join(directory, filename)

    if os.path.exists(filepath):
        existing_data = pd.read_csv(filepath, sep=';')
        updated_data = pd.concat([existing_data, data], ignore_index=True)
    else:
        updated_data = data

    updated_data['Response Time'] = response_times[:len(updated_data)]
    updated_data['Response Size'] = response_sizes[:len(updated_data)]
    updated_data.to_csv(filepath, index=False, sep=';')

def process_repositories(repositories, response_times, response_sizes):
    processed_data = pd.DataFrame()
    processed_data['Repository URL'] = [repo['html_url'] for repo in repositories]
    processed_data['Repository name'] = [repo.get('name') for repo in repositories]
    processed_data['Repository owner'] = [repo.get('owner', {}).get('login') for repo in repositories]
    processed_data['Stars'] = [repo.get('stargazers_count', 0) if isinstance(repo, dict) else 0 for repo in repositories]
    processed_data['Created At'] = [repo.get('created_at') for repo in repositories]
    processed_data['Updated At'] = [repo.get('updated_at') for repo in repositories]
    
    save_csv(processed_data, response_times, response_sizes, 'most_popular_repos_rest.csv')
    print('The repository list has been created')

    return processed_data

repositories, response_times, response_sizes = fetch_repositories()
process_repositories(repositories, response_times, response_sizes)