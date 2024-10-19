import pandas as pd
results_df = pd.read_csv('github_repo_stars.csv')
results_df = results_df.sort_values('Stars', ascending=False)
results_df.to_csv('github_repo_stars_sorted.csv', index=False)
