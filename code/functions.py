import re
from datetime import datetime
import pandas as pd
from git import Repo
import subprocess

def matching(df: pd.DataFrame, git_contributors_df: pd.DataFrame) -> pd.DataFrame:
    rank = []
    insertions = []
    deletions = []
    lines_changed = []
    files = []
    commits = []
    first_commit = []
    last_commit = []
    scores = []
    matching_columns = 0
    if 'name' in df.columns:
        matching_columns += 1
    if 'email' in df.columns:
        matching_columns += 1
    if 'login' in df.columns:
        matching_columns += 1
    
    for _, author in df.iterrows():
        dic = []
        for contributor_index, contributor in git_contributors_df.iterrows():
            counter = 0
            if 'name' in df.columns and author["name"] is not None and contributor["name"] is not None and author["name"].lower() in contributor["name"].lower():
                counter += 1
            if 'email' in df.columns and author["email"] is not None and contributor["email"] is not None and author["email"].lower() in contributor["email"].lower():
                counter += 1
            if 'login' in df.columns and author["login"] is not None and contributor["email"] is not None and author["login"].lower() in contributor["email"].lower():
                counter += 1

            if counter > 0:
                dic.append({
                    "index": contributor_index,
                    "score": counter / matching_columns
                })

        test = max(dic, key=lambda x: x["score"], default=None)
        if test is not None:
            rank.append(test["index"] + 1)
            insertions.append(git_contributors_df.loc[test["index"]]["insertions"])
            deletions.append(git_contributors_df.loc[test["index"]]["deletions"])
            lines_changed.append(git_contributors_df.loc[test["index"]]["lines_changed"])
            files.append(git_contributors_df.loc[test["index"]]["files"])
            commits.append(git_contributors_df.loc[test["index"]]["commits"])
            first_commit.append(git_contributors_df.loc[test["index"]]["first_commit"])
            last_commit.append(git_contributors_df.loc[test["index"]]["last_commit"])
            scores.append(test["score"])
        else:
            rank.append(None)
            insertions.append(None)
            deletions.append(None)
            lines_changed.append(None)
            files.append(None)
            commits.append(None)
            first_commit.append(None)
            last_commit.append(None)
            scores.append(0)

    df["rank"] = rank
    df["insertions"] = insertions
    df["deletions"] = deletions
    df["lines_changed"] = lines_changed
    df["files"] = files
    df["commits"] = commits
    df["first_commit"] = first_commit
    df["last_commit"] = last_commit
    df["score"] = scores
    return df

def parse_contribution_stats(data: str) -> list:
    author_pattern = re.compile(
        r"\s*(.+) <(.+)>:\s*"
        r"insertions:\s*(\d+)\s*\((\d+)%\)\s*"
        r"deletions:\s*(\d+)\s*\((\d+)%\)\s*"
        r"files:\s*(\d+)\s*\((\d+)%\)\s*"
        r"commits:\s*(\d+)\s*\((\d+)%\)\s*"
        r"lines changed:\s*(\d+)\s*\((\d+)%\)\s*"
        r"first commit:\s*(.+)\s*"
        r"last commit:\s*(.+)\s*"
    )

    authors = []
    for match in author_pattern.finditer(data):
        (name, email, insertions, insertions_pct, deletions, deletions_pct, files, files_pct, 
         commits, commits_pct, lines_changed, lines_changed_pct, first_commit, last_commit) = match.groups()
        authors.append({
            'name': name,
            'email': email,
            'insertions': int(insertions),
            'deletions': int(deletions),
            'files': int(files),
            'commits': int(commits),
            'first_commit': datetime.strptime(first_commit, '%a %b %d %H:%M:%S %Y %z'),
            'last_commit': datetime.strptime(last_commit, '%a %b %d %H:%M:%S %Y %z'),
            'lines_changed': int(lines_changed),
        })

    return authors

def get_git_contributors(owner: str, repo: str, repo_link: str) -> pd.DataFrame:
    Repo.clone_from(repo_link, f'./repos/{owner}/{repo}')

    # Stark unterschiedliche Anzahl der commits abhängig vom Programm
    git_quick_stat = subprocess.run(['git-quick-stats', '-T'], capture_output=True, text=True, cwd=f'./repos/{owner}/{repo}')
    
    # Doppelte Leute, da unterschiedliche Namen beim commiten angegeben -> Das Problem besteht beim benutzen der GitHub API nicht. -> Teilweise Gelöst mittels group auf E-Mail
    data = git_quick_stat.stdout

    # Parse the data
    authors_data = parse_contribution_stats(data)

    # Convert authors data to DataFrame
    git_contributors_df = pd.DataFrame(authors_data)
    git_contributors_df['email'] = git_contributors_df['email'].str.lower()
    git_contributors_df = git_contributors_df.groupby(['email']).agg({'name':'sum', 'insertions':'sum', 'deletions':'sum', 'lines_changed':'sum', 'files':'sum', 'commits':'sum', 'first_commit':'min', 'last_commit':'max'}).reset_index()
    git_contributors_df = git_contributors_df.sort_values(by=['commits'], ascending=False)
    git_contributors_df = git_contributors_df.reset_index(drop=True)
    git_contributors_df = git_contributors_df[['name', 'email', 'insertions', 'deletions', 'lines_changed', 'files', 'commits', 'first_commit', 'last_commit']]

    return git_contributors_df
