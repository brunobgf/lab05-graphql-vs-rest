import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

graphql_df = pd.read_csv('dataset/most_popular_repos_graphql.csv', delimiter=';')
rest_df = pd.read_csv('dataset/most_popular_repos_rest.csv', delimiter=';')

graphql_df['API Type'] = 'GraphQL'
rest_df['API Type'] = 'REST'
combined_df = pd.concat([graphql_df, rest_df])


lower_quantile = 0.01
upper_quantile = 0.99

filtered_combined_df = combined_df[(combined_df['Response Time'] > combined_df['Response Time'].quantile(lower_quantile)) & 
                                   (combined_df['Response Time'] < combined_df['Response Time'].quantile(upper_quantile))]

filtered_combined_df = filtered_combined_df[(filtered_combined_df['Response Size'] > filtered_combined_df['Response Size'].quantile(lower_quantile)) & 
                                            (filtered_combined_df['Response Size'] < filtered_combined_df['Response Size'].quantile(upper_quantile))]

sns.set(style="whitegrid")

# Histograma do Tempo de Resposta para GraphQL e REST 
plt.figure(figsize=(8, 6))
sns.histplot(data=filtered_combined_df, x='Response Time', hue='API Type', kde=True, bins=20)
plt.title('Tempo de Resposta: GraphQL vs REST', fontsize=28, fontweight='bold', pad=20)
plt.xlabel('Tempo de Resposta (segundos)', fontsize=22)
plt.ylabel('Frequência', fontsize=22)
plt.xticks(fontsize=24)
plt.yticks(fontsize=24)
plt.show()

# Gráfico de barras do GraphQL x REST para tamanho
sns.set(style="whitegrid")
plt.figure(figsize=(8, 6))
sns.barplot(data=filtered_combined_df, x='API Type', y='Response Size', ci=None, palette="viridis")
plt.title('Tamanho da Resposta: GraphQL vs REST', fontsize=28, fontweight='bold', pad=20)
plt.xlabel('API Type', fontsize=22)
plt.ylabel('Tamanho da Resposta (bytes)', fontsize=22)
plt.xticks(fontsize=24)
plt.yticks(fontsize=24)
plt.show()