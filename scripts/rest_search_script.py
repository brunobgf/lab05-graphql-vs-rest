import requests as req
import pandas as pd
import time
import os
from datetime import datetime

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

def time_since_last_update(last_update_date):
    current_date = datetime.utcnow()
    last_update_date = datetime.strptime(last_update_date, '%Y-%m-%dT%H:%M:%SZ')
    difference = current_date - last_update_date
    days = difference.days
    seconds = difference.seconds
    elapsed_days = days
    elapsed_hours = seconds // 3600
    elapsed_minutes = (seconds % 3600) // 60
    elapsed_seconds = seconds % 60
    return f'{elapsed_days} days {elapsed_hours} hours {elapsed_minutes} minutes {elapsed_seconds} seconds'

def calculate_age(date_of_birth):
    current_date = datetime.utcnow()
    date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%dT%H:%M:%SZ')
    difference = current_date - date_of_birth
    age = difference.days // 365
    return age

def fetch_additional_info(repo):
    owner = repo['owner']['login']
    repo_name = repo['name']

    languages_url = repo['languages_url']
    languages_data, _, _ = get(languages_url)
    primary_language = next(iter(languages_data), None)

    pr_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls?state=closed"
    prs_data, _, _ = get(pr_url)
    pr_count = sum(1 for pr in prs_data if pr['merged_at'] is not None)

    issues_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"
    issues_data, _, _ = get(issues_url)
    total_issues = len(issues_data)
    closed_issues = sum(1 for issue in issues_data if issue['state'] == 'closed')

    releases_url = f"https://api.github.com/repos/{owner}/{repo_name}/releases"
    releases_data, _, _ = get(releases_url)
    total_releases = len(releases_data)
    last_release = releases_data[0]['created_at'] if total_releases > 0 else None
    total_collaborators = len(set(release['author']['login'] for release in releases_data if release['author']))

    return {
        'primary_language': primary_language,
        'pr_count': pr_count,
        'total_issues': total_issues,
        'closed_issues': closed_issues,
        'total_releases': total_releases,
        'last_release': last_release,
        'total_collaborators': total_collaborators
    }

def fetch_repositories():
    repositories = []
    per_page = 1
    page = 1
    query_string = "stars:>20000"
    
    total_time = 0
    total_size = 0
    response_times = []
    response_sizes = []
    
    while len(repositories) < 4:
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

        for repo in data['items']:
            additional_info = fetch_additional_info(repo)
            repo.update(additional_info)
            repositories.append(repo)
        
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
    processed_data['Age'] = [calculate_age(repo.get('created_at')) for repo in repositories]
    processed_data['Last Update'] = [time_since_last_update(repo.get('updated_at')) for repo in repositories]
    processed_data['Primary Language'] = [repo.get('primary_language') for repo in repositories]
    processed_data['Number PR Accepted'] = [repo.get('pr_count') for repo in repositories]
    processed_data['Issues Reason'] = [
        repo.get('closed_issues', 0) / repo.get('total_issues', 1) if repo.get('total_issues', 0) > 0 else None
        for repo in repositories
    ]
    processed_data['Total Releases'] = [repo.get('total_releases', 0) for repo in repositories]
    processed_data['Last Release'] = [repo.get('last_release') for repo in repositories]
    processed_data['Total Collaborators'] = [repo.get('total_collaborators', 1) for repo in repositories]
    processed_data['Forks'] = [repo.get('forks_count', 0) for repo in repositories]

    save_csv(processed_data, response_times, response_sizes, 'most_popular_repos_rest.csv')
    print('The repository list has been created')

    return processed_data

repositories, response_times, response_sizes = fetch_repositories()
process_repositories(repositories, response_times, response_sizes)