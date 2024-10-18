import os
import pandas as pd
import requests
import time
from tqdm import tqdm  # Import tqdm for progress bar

# Load GitHub personal access token from a file
def load_github_token(token_file='github_token.txt'):
    with open(token_file, 'r') as file_content:
        return file_content.read().strip()

# Load the token
GITHUB_TOKEN = load_github_token()
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'}
API_URL = 'https://api.github.com/repos/'

# Function to get stars for a repository
def get_repo_stars(repo_url):
    try:
        repo_name = repo_url.split('/')[-2] + '/' + repo_url.split('/')[-1]
        response = requests.get(API_URL + repo_name, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            return data.get('stargazers_count', 0)
        elif response.status_code == 404:
            print(f"Repository not found: {repo_url}")
            return None
        else:
            print(f"Error fetching {repo_url}: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


# Read the repository links from the text file
with open('github_repos_with_cffs.txt', 'r') as file:
    repos = [line.strip() for line in file.readlines()]

# Check if results file exists to load existing data
if os.path.exists('github_repo_stars.csv'):
    results_df = pd.read_csv('github_repo_stars.csv')
    existing_repos = set(results_df['Repository'])
else:
    results_df = pd.DataFrame(columns=['Repository', 'Stars'])
    existing_repos = set()

# Initialize a list to hold new results
results = results_df.to_dict(orient='records')  # Start with existing results

# Iterate over the repository links with a progress bar
with tqdm(total=len(repos), desc='Processing Repositories') as pbar:
    for repo_url in repos:
        if repo_url in existing_repos:
            pbar.update(1)  # Update progress bar
            print(f"Skipping already processed repo: {repo_url}")
            continue  # Skip already processed repos

        stars = get_repo_stars(repo_url)

        if stars is not None:
            # Append the result to the results list
            results.append({'Repository': repo_url, 'Stars': stars})

            # Save the current results to CSV, overwriting the file
            pd.DataFrame(results).to_csv('github_repo_stars.csv', index=False)

        # Rate limit handling
        if len(results) % 5000 == 0:
            print("Reached 5000 API calls, waiting for the next hour...")
            time.sleep(3600)  # Sleep for an hour if limit is reached

        pbar.update(1)  # Update progress bar for each processed repository

print("Data collection complete.")
