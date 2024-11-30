import asyncio
import os
import re
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from tqdm import tqdm
from datetime import datetime
from pandas._libs.missing import NAType

def check_matches(df: pd.DataFrame):
    matches = (df['score'] > 0).sum()
    non_matches = (df['score'] <= 0).sum()
    entries = len(df)
    return matches, non_matches, entries

def get_git_contributors_df(root) -> pd.DataFrame:
    git_contributors_df = pd.read_csv(os.path.join(root, 'git_contributors.csv'))
    git_contributors_df['first_commit'] = pd.to_datetime(git_contributors_df['first_commit'], utc=True, format='%Y-%m-%d %H:%M:%S%z')
    git_contributors_df['last_commit'] = pd.to_datetime(git_contributors_df['last_commit'], utc=True, format='%Y-%m-%d %H:%M:%S%z')
    return git_contributors_df

def get_authors_df(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df['first_commit'] = pd.to_datetime(df['first_commit'], utc=True, format='%Y-%m-%d %H:%M:%S%z')
    df['last_commit'] = pd.to_datetime(df['last_commit'], utc=True, format='%Y-%m-%d %H:%M:%S%z')
    return df

def get_common_authors(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    common_fields = ['insertions', 'deletions', 'lines_changed', 'files', 'commits', 'first_commit', 'last_commit']
    merged_df = pd.merge(df1, df2, on=common_fields, how='inner')
    return merged_df

'''
Im ersten wird gezeigt, welcher Anteil von Top Committer über alle
Projekte auch in der CFF genannt werden. Da es immer wieder Committer
gibt, die nicht in der CFF auftauchen, kann diese Kurve 1 nicht erreichen.
'''
def get_common_authors_count(git_contributors_df: pd.DataFrame, df: pd.DataFrame, common_authors: dict, file: str, package: str, commits: bool) -> dict:
    if file not in common_authors:
        common_authors[file] = {}
    if package not in common_authors[file]:
        common_authors[file][package] = ([], [])

    df = df.drop_duplicates(subset=['commits'])

    for i in range(1, 101):
        if commits:
            most_commits_entry = git_contributors_df.loc[git_contributors_df['commits'].nlargest(i).index]
        else:
            most_commits_entry = git_contributors_df.loc[git_contributors_df['lines_changed'].nlargest(i).index]

        common_authors_entry = get_common_authors(most_commits_entry, df)
        common_authors[file][package][0].append(len(common_authors_entry))
        common_authors[file][package][1].append(len(most_commits_entry))

    return common_authors

'''
Im zweiten Plot wird pro Projekt gezeigt, welchen Anteil der in der CFF
genannten Autoren unter den n Top Committern ist. Dieser Graph kann 1
erreichen, wenn alle Autoren tatsächlich was zum Projekt beigetragen
haben (aber nicht notwendigerweise die n Top Committer sind.)
'''
def get_common_authors_count_2(git_contributors_df: pd.DataFrame, df: pd.DataFrame, common_authors: dict, file: str, package: str, commits: bool) -> dict[str, dict[str, tuple[list, int]]]:
    if file not in common_authors:
        common_authors[file] = {}
    if package not in common_authors[file]:
        common_authors[file][package] = ([], len(df))

    for i in range(1, 201):
        if commits:
            most_commits_entry = git_contributors_df.loc[git_contributors_df['commits'].nlargest(i).index]
        else:
            most_commits_entry = git_contributors_df.loc[git_contributors_df['lines_changed'].nlargest(i).index]
        common_authors_entry = get_common_authors(most_commits_entry, df)
        common_authors[file][package][0].append(len(common_authors_entry))
    return common_authors

def get_total_authors_no_commits(git_contributors_df: pd.DataFrame, df: pd.DataFrame, total_authors_no_commits: dict, file: str, package: str) -> dict:
    if file not in total_authors_no_commits:
        total_authors_no_commits[file] = {}
    if package not in total_authors_no_commits[file]:
        total_authors_no_commits[file][package] = ([], len(df[df['score'] > 0]))

    for i in range(1, 3651):
        total_authors_no_commits[file][package][0].append(len(df[df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=i)]))

    return total_authors_no_commits

def calculate_similarity_with_non_matches(df_list: list[pd.DataFrame]) -> NAType | float:
    similarities = []
    for i in range(len(df_list)):
        for j in range(i + 1, len(df_list)):
            first_df = df_list[i]
            second_df = df_list[j]
            first_df = first_df[first_df['commits'].notna()]
            second_df = second_df[second_df['commits'].notna()]
            common_authors = get_common_authors(first_df, second_df)
            if len(df_list[i]) >= len(df_list[j]):
                similarity = len(common_authors) / len(df_list[i])
                similarities.append(similarity)
            else:
                similarity = len(common_authors) / len(df_list[j])
                similarities.append(similarity)

    if len(similarities) == 0:
        return pd.NA

    return sum(similarities) / len(similarities)

def calculate_similarity_without_non_matches(df_list: list[pd.DataFrame]) -> NAType | float:
    similarities = []
    for i in range(len(df_list)):
        for j in range(i + 1, len(df_list)):
            first_df = df_list[i]
            second_df = df_list[j]
            first_df = first_df[first_df['commits'].notna()]
            second_df = second_df[second_df['commits'].notna()]
            common_authors = get_common_authors(first_df, second_df)
            if len(first_df) >= len(second_df) and len(first_df) > 0:
                similarity = len(common_authors) / len(first_df)
                similarities.append(similarity)
            elif len(second_df) > 0:
                similarity = len(common_authors) / len(second_df)
                similarities.append(similarity)

    if len(similarities) == 0:
        return pd.NA

    return sum(similarities) / len(similarities)

def process_directory(directory, position: int, full=True):
    # CFF
    total_cff = 0
    total_cff_full = 0
    total_valid_cff_cff_init_used = 0
    total_valid_cff_cff_init_used_full = 0
    total_valid_cff_cff_init_not_used = 0
    total_valid_cff_cff_init_not_used_full = 0
    total_invalid_cff_cff_init_used = 0
    total_invalid_cff_cff_init_used_full = 0
    total_invalid_cff_cff_init_not_used = 0
    total_invalid_cff_cff_init_not_used_full = 0
    doi_cff = 0
    doi_cff_full = 0
    identifier_doi_cff = 0
    identifier_doi_cff_full = 0
    citation_counts_cff = {}
    citation_counts_cff_full = {}
    average_time_between_updates_cff = []
    difference_last_update_cff_list = []

    # Preferred citation CFF
    total_preferred_citation_cff = 0
    total_preferred_citation_cff_full = 0
    doi_preferred_citation_cff = 0
    identifier_doi_preferred_citation_cff = 0
    collection_doi_preferred_citation_cff = 0
    citation_counts_preferred_citation_cff = {}

    # Bib
    total_bib = 0
    total_bib_full = 0
    doi_bib = 0
    average_time_between_updates_bib = []
    difference_last_update_bib_list = []
    citation_counts_bib = {}

    # Readme
    average_time_between_updates_readme = []
    difference_last_update_readme_list = []

    file_type_percentages = {}
    total_authors_no_commits = {}
    common_authors = {}
    common_authors_by_lines = {}
    common_authors_2: dict[str, dict[str, tuple[list, int]]] = {}
    common_authors_2_by_lines = {}
    dfs = {}
    authors = {}
    similarity_with_non_matches = []
    similarity_without_non_matches = []

    # Regular expressions to extract timestamp and file type
    file_patterns = {
        'readme_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_readme_authors_new\.csv'),
        'cff_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_authors_new\.csv'),
        'cff_preferred_citation_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_preferred_citation_authors_new\.csv'),
        'bib_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_bib_authors_new\.csv')
    }

    # Track the latest file for each type
    latest_files_by_folder = {}

    folder_count = -1
    for root, _, files in os.walk(directory):
        folder_count += 1

    for root, dirs, files in tqdm(os.walk(directory), total=folder_count, position=position, desc=directory.split('/')[-1]):
        folder_name = os.path.basename(root)
        last_timed_df = {}

        if folder_name not in latest_files_by_folder:
            latest_files_by_folder[folder_name] = {file_type: (None, None) for file_type in file_patterns}

        for file in sorted(files):
            if full:
                for file_type, pattern in file_patterns.items():
                    match = pattern.search(file)
                    if match:
                        timestamp_str = match.group(1)
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S%z')

                        file_path = str(os.path.join(root, file))
                        df = get_authors_df(file_path)

                        if file_type not in authors:
                            authors[file_type] = {}

                        if folder_name not in authors[file_type]:
                            authors[file_type][folder_name] = {}
                            for name in df['name'].tolist():
                                authors[file_type][folder_name][name] = {"timestamps_added": [timestamp], "timestamps_removed": []}
                            last_timed_df[file_type] = df
                        else:
                            # Matche über den Namen was natürlich dazu führt, dass namensänderungen neue Autoren sind falls kein Abgleich stattgefunden haben sollte in der Datenbeschaffung
                            df_matched = df[df['score'] > 0]
                            last_timed_df_matched = last_timed_df[file_type][last_timed_df[file_type]['score'] > 0]
                            common_authors_in_time_with_git = get_common_authors(last_timed_df_matched, df_matched)
                            common_authors_in_time_with_name = pd.merge(last_timed_df[file_type], df, on=['name'], how='inner')
                            common_authors_in_time_with_git.rename(columns={'name_x': 'name'}, inplace=True)
                            common_authors_in_time = pd.merge(common_authors_in_time_with_git, common_authors_in_time_with_name, on=['name'], how='outer')
                            removed_authors = last_timed_df[file_type][~last_timed_df[file_type].name.isin(common_authors_in_time['name'])]
                            common_authors_in_time.rename(columns={'name': 'name_x'}, inplace=True)
                            common_authors_in_time.rename(columns={'name_y': 'name'}, inplace=True)
                            common_authors_in_time['name'] = common_authors_in_time['name'].fillna(common_authors_in_time['name_x'])
                            added_authors = df[~df.name.isin(common_authors_in_time['name'])]
                            for author in removed_authors['name'].tolist():
                                if author in authors[file_type][folder_name]:
                                    authors[file_type][folder_name][author]["timestamps_removed"].append(timestamp)
                            for author in added_authors['name'].tolist():
                                if author not in authors[file_type][folder_name]:
                                    authors[file_type][folder_name][author] = {"timestamps_added": [timestamp], "timestamps_removed": []}
                                else:
                                    authors[file_type][folder_name][author]["timestamps_added"].append(timestamp)


                            last_timed_df[file_type] = df
                        matches, non_matches, entries = check_matches(df)

                        if file_type not in file_type_percentages:
                            file_type_percentages[file_type] = {'matches': 0, 'non_matches': 0, 'entries': 0}

                        file_type_percentages[file_type]['matches'] += matches
                        file_type_percentages[file_type]['non_matches'] += non_matches
                        file_type_percentages[file_type]['entries'] += entries

                if file == 'cff.csv':
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    total_cff_full += len(df)
                    total_valid_cff_cff_init_used_full += df[(df['cff_valid'] == True) & (df['cff_init'] == True)].shape[0]
                    total_valid_cff_cff_init_not_used_full += df[(df['cff_valid'] == True) & (df['cff_init'] == False)].shape[0]
                    total_invalid_cff_cff_init_used_full += df[(df['cff_valid'] == False) & (df['cff_init'] == True)].shape[0]
                    total_invalid_cff_cff_init_not_used_full += df[(df['cff_valid'] == False) & (df['cff_init'] == False)].shape[0]
                    doi_cff_full += df['doi'].notna().sum()
                    identifier_doi_cff_full += df['identifier-doi'].notna().sum()
                    for key, value in df['type'].value_counts().to_dict().items():
                        citation_counts_cff_full[key] = citation_counts_cff_full.get(key, 0) + value
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime')
                    average_time_between_updates_cff.append(df_sorted['committed_datetime'].diff().dropna().mean())

                if file == 'bib.csv':
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    total_bib_full += len(df)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime')
                    average_time_between_updates_bib.append(df_sorted['committed_datetime'].diff().dropna().mean())

                if file == 'readme.csv':
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime')
                    average_time_between_updates_readme.append(df_sorted['committed_datetime'].diff().dropna().mean())

                if file == 'cff_preferred_citation.csv':
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    total_preferred_citation_cff_full += len(df)
            else:
                if file in ['pypi_maintainers.csv', 'python_authors.csv', 'python_maintainers.csv',
                            'description_authors.csv', 'cran_authors.csv', 'cran_maintainers.csv']:
                    file_path = str(os.path.join(root, file))
                    df = get_authors_df(file_path)

                    #shuffled_authors_df = df.sample(frac=1).reset_index(drop=True)
                    #shuffled_authors_df['checked'] = 0
                    #Path(f"results_manually_checked/{directory.split('/')[-1]}/{folder_name}").mkdir(parents=True, exist_ok=True)
                    #shuffled_authors_df.to_csv(f"results_manually_checked/{directory.split('/')[-1]}/{folder_name}/{file}", index=False)

                    if folder_name not in dfs:
                        dfs[folder_name] = list()

                    dfs[folder_name].append(df)
                    matches, non_matches, entries = check_matches(df)

                    file_base = os.path.splitext(file)[0]
                    if file_base not in file_type_percentages:
                        file_type_percentages[file_base] = {'matches': 0, 'non_matches': 0, 'entries': 0}
                    file_type_percentages[file_base]['matches'] += matches
                    file_type_percentages[file_base]['non_matches'] += non_matches
                    file_type_percentages[file_base]['entries'] += entries

                    git_contributors_df = get_git_contributors_df(root)
                    #git_contributors_df.to_csv(f"results_manually_checked/{directory.split('/')[-1]}/{folder_name}/git_contributors.csv", index=False)

                    total_authors_no_commits = get_total_authors_no_commits(git_contributors_df, df, total_authors_no_commits, file, folder_name)

                    common_authors = get_common_authors_count(git_contributors_df, df, common_authors, file, folder_name, True)
                    common_authors_by_lines = get_common_authors_count(git_contributors_df, df, common_authors_by_lines, file, folder_name, False)
                    common_authors_2 = get_common_authors_count_2(git_contributors_df, df, common_authors_2, file, folder_name, True)
                    common_authors_2_by_lines = get_common_authors_count_2(git_contributors_df, df, common_authors_2_by_lines, file, folder_name, False)

                # Process only the latest timestamped files
                for file_type, pattern in file_patterns.items():
                    match = pattern.search(file)
                    if match:
                        timestamp_str = match.group(1)
                        timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S%z')

                        # Update latest file if the current one is more recent
                        _, latest_time = latest_files_by_folder[folder_name][file_type]
                        if latest_time is None or timestamp > latest_time:
                            latest_files_by_folder[folder_name][file_type] = (os.path.join(root, file), timestamp)

                if file == 'cff.csv':
                    git_contributors_df = get_git_contributors_df(root)
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime', ascending=False)
                    total_cff += 1
                    if df_sorted.iloc[0]['cff_valid'] and df_sorted.iloc[0]['cff_init']:
                        total_valid_cff_cff_init_used += 1
                    if df_sorted.iloc[0]['cff_valid'] and not df_sorted.iloc[0]['cff_init']:
                        total_valid_cff_cff_init_not_used += 1
                    if not df_sorted.iloc[0]['cff_valid'] and df_sorted.iloc[0]['cff_init']:
                        total_invalid_cff_cff_init_used += 1
                    if not df_sorted.iloc[0]['cff_valid'] and not df_sorted.iloc[0]['cff_init']:
                        total_invalid_cff_cff_init_not_used += 1
                    if not pd.isna(df_sorted.iloc[0]['doi']):
                        doi_cff += 1
                    if not pd.isna(df_sorted.iloc[0]['identifier-doi']):
                        identifier_doi_cff += 1
                    key = df_sorted.iloc[0]['type']
                    citation_counts_cff[key] = citation_counts_cff.get(key, 0) + 1
                    difference_last_update_cff_list.append(git_contributors_df['last_commit'].max() - df_sorted.iloc[0]['committed_datetime'])

                if file == 'cff_preferred_citation.csv':
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime', ascending=False)
                    total_preferred_citation_cff += 1
                    if not pd.isna(df_sorted.iloc[0]['doi']):
                        doi_preferred_citation_cff += 1
                    if not pd.isna(df_sorted.iloc[0]['identifier-doi']):
                        identifier_doi_preferred_citation_cff += 1
                    if not pd.isna(df_sorted.iloc[0]['collection-doi']):
                        collection_doi_preferred_citation_cff += 1
                    key = df_sorted.iloc[0]['type']
                    citation_counts_preferred_citation_cff[key] = citation_counts_preferred_citation_cff.get(key, 0) + 1

                if file == 'bib.csv':
                    git_contributors_df = get_git_contributors_df(root)
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime', ascending=False)
                    total_bib += 1
                    if not pd.isna(df_sorted.iloc[0]['doi']):
                        doi_bib += 1
                    difference_last_update_bib_list.append(git_contributors_df['last_commit'].max() - df_sorted.iloc[0]['committed_datetime'])
                    key = df_sorted.iloc[0]['type']
                    citation_counts_bib[key] = citation_counts_bib.get(key, 0) + 1

                if file == 'readme.csv':
                    git_contributors_df = get_git_contributors_df(root)
                    file_path = str(os.path.join(root, file))
                    df = pd.read_csv(file_path)
                    df['committed_datetime'] = pd.to_datetime(df['committed_datetime'], utc=True)
                    df_sorted = df.sort_values(by='committed_datetime', ascending=False)
                    difference_last_update_readme_list.append(git_contributors_df['last_commit'].max() - df_sorted.iloc[0]['committed_datetime'])

    # After the loop, process the latest files if 'full' is False
    if not full:
        for folder, file_data in latest_files_by_folder.items():
            for file_type, (latest_file_path, _) in file_data.items():
                if latest_file_path:
                    authors_df = get_authors_df(latest_file_path)

                    #shuffled_authors_df = authors_df.sample().reset_index(drop=True)
                    #shuffled_authors_df['checked'] = 0
                    #Path(f"results_manually_checked/{directory.split('/')[-1]}/{folder}").mkdir(parents=True, exist_ok=True)
                    #shuffled_authors_df.to_csv(f"results_manually_checked/{directory.split('/')[-1]}/{folder}/{os.path.basename(latest_file_path)}", index=False)

                    if folder not in dfs:
                        dfs[folder] = list()

                    dfs[folder].append(authors_df)
                    matches, non_matches, entries = check_matches(authors_df)
                    if file_type not in file_type_percentages:
                        file_type_percentages[file_type] = {'matches': 0, 'non_matches': 0, 'entries': 0}

                    file_type_percentages[file_type]['matches'] += matches
                    file_type_percentages[file_type]['non_matches'] += non_matches
                    file_type_percentages[file_type]['entries'] += entries

                    git_contributors_df = get_git_contributors_df(os.path.dirname(latest_file_path))
                    #git_contributors_df.to_csv(f"results_manually_checked/{directory.split('/')[-1]}/{folder}/git_contributors.csv", index=False)
                    total_authors_no_commits = get_total_authors_no_commits(git_contributors_df, authors_df, total_authors_no_commits, file_type, folder)

                    common_authors = get_common_authors_count(git_contributors_df, authors_df, common_authors, file_type, folder, True)
                    common_authors_by_lines = get_common_authors_count(git_contributors_df, authors_df, common_authors_by_lines, file_type, folder, False)
                    common_authors_2 = get_common_authors_count_2(git_contributors_df, authors_df, common_authors_2, file_type, folder, True)
                    common_authors_2_by_lines = get_common_authors_count_2(git_contributors_df, authors_df, common_authors_2_by_lines, file_type, folder, False)

        for folder, df_list in dfs.items():
            if len(df_list) > 1:
                similarity_with_non_matches_results = calculate_similarity_with_non_matches(df_list)
                similarity_without_non_matches_result = calculate_similarity_without_non_matches(df_list)

                if not pd.isna(similarity_with_non_matches_results):
                    similarity_with_non_matches.append(similarity_with_non_matches_results)
                if not pd.isna(similarity_without_non_matches_result):
                    similarity_without_non_matches.append(similarity_without_non_matches_result)

    # Convert percentages to tuple format before returning
    file_type_percentages = {ft: (data['matches'], data['non_matches'], data['entries']) for ft, data in
                             file_type_percentages.items()}

    if full:
        authors_added_results = {}
        authors_added_without_first_timestamp_results = {}
        authors_removed_results = {}
        lifespans_results = {}

        for file_type, value in authors.items():
            authors_added = 0
            authors_added_without_first_timestamp = 0
            authors_removed = 0
            lifespans = []
            for package in value:
                authors_added += len([author for author in value[package] if value[package][author]["timestamps_added"]])
                authors_added_without_first_timestamp += len([author for author in value[package] if len(value[package][author]["timestamps_added"]) > 1])
                authors_removed += len([author for author in value[package] if value[package][author]["timestamps_removed"]])
                for name, timestamps in value[package].items():
                    for index, added in enumerate(timestamps['timestamps_added']):
                        if len(timestamps['timestamps_removed']) < len(timestamps['timestamps_added']):
                            continue
                        if len(timestamps['timestamps_removed']) > index and timestamps['timestamps_removed'][index]:
                            lifespans.append((timestamps['timestamps_removed'][index] - added).days)

            authors_added_results[file_type] = authors_added
            authors_added_without_first_timestamp_results[file_type] = authors_added_without_first_timestamp
            authors_removed_results[file_type] = authors_removed
            lifespans_results[file_type] = pd.Series(lifespans).mean()

        overall_results = {"total_cff": total_cff_full,
                            "total_valid_cff_cff_init_used": total_valid_cff_cff_init_used_full,
                            "total_valid_cff_cff_init_not_used": total_valid_cff_cff_init_not_used_full,
                            "total_invalid_cff_cff_init_used": total_invalid_cff_cff_init_used_full,
                            "total_invalid_cff_cff_init_not_used": total_invalid_cff_cff_init_not_used_full,
                            "doi_cff": doi_cff_full,
                            "identifier_doi_cff": identifier_doi_cff_full,
                            "total_preferred_citation_cff": total_preferred_citation_cff_full,
                            "average_time_between_updates_cff": pd.Series(average_time_between_updates_cff).mean(),
                            "average_time_between_updates_bib": pd.Series(average_time_between_updates_bib).mean(),
                            "average_time_between_updates_readme": pd.Series(average_time_between_updates_readme).mean(),
                            "total_bib": total_bib_full,
                            "citation_counts_cff": citation_counts_cff_full,
                            "authors_added": authors_added_results,
                            "authors_added_without_first_timestamp": authors_added_without_first_timestamp_results,
                            "authors_removed": authors_removed_results,
                            "average_lifespans": lifespans_results}
    else:
        overall_results = {"total_cff": total_cff,
                            "total_valid_cff_cff_init_used": total_valid_cff_cff_init_used,
                            "total_valid_cff_cff_init_not_used": total_valid_cff_cff_init_not_used,
                            "total_invalid_cff_cff_init_used": total_invalid_cff_cff_init_used,
                            "total_invalid_cff_cff_init_not_used": total_invalid_cff_cff_init_not_used,
                            "doi_cff": doi_cff,
                            "identifier_doi_cff": identifier_doi_cff,
                            "total_preferred_citation_cff": total_preferred_citation_cff,
                            "doi_preferred_citation_cff": doi_preferred_citation_cff,
                            "identifier_doi_preferred_citation_cff": identifier_doi_preferred_citation_cff,
                            "collection_doi_preferred_citation_cff": collection_doi_preferred_citation_cff,
                            "doi_bib": doi_bib,
                            "average_time_last_update_cff": pd.Series(difference_last_update_cff_list).mean(),
                            "average_time_last_update_bib": pd.Series(difference_last_update_bib_list).mean(),
                            "average_time_last_update_readme": pd.Series(difference_last_update_readme_list).mean(),
                            "total_bib": total_bib,
                            "citation_counts_cff": citation_counts_cff,
                            "citation_counts_preferred_citation_cff": citation_counts_preferred_citation_cff,
                            "citation_counts_bib": citation_counts_bib,
                            "similarity_with_non_matches": similarity_with_non_matches,
                            "similarity_without_non_matches": similarity_without_non_matches}

        for file, total_authors_no_commits_data in total_authors_no_commits.items():
            Path(f"overall_results/{directory.split('/')[-1]}/total_authors_no_commits").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(total_authors_no_commits_data).to_csv(f"overall_results/{directory.split('/')[-1]}/total_authors_no_commits/{file}", index=False)

        for file, common_authors_data in common_authors.items():
            Path(f"overall_results/{directory.split('/')[-1]}/common_authors").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(common_authors_data).to_csv(f"overall_results/{directory.split('/')[-1]}/common_authors/{file}", index=False)

        for file, common_authors_by_lines_data in common_authors_by_lines.items():
            Path(f"overall_results/{directory.split('/')[-1]}/common_authors_by_lines").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(common_authors_by_lines_data).to_csv(f"overall_results/{directory.split('/')[-1]}/common_authors_by_lines/{file}", index=False)

        for file, common_authors_2_data in common_authors_2.items():
            Path(f"overall_results/{directory.split('/')[-1]}/common_authors_2").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(common_authors_2_data).to_csv(f"overall_results/{directory.split('/')[-1]}/common_authors_2/{file}", index=False)

        for file, common_authors_2_by_lines_data in common_authors_2_by_lines.items():
            Path(f"overall_results/{directory.split('/')[-1]}/common_authors_2_by_lines").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(common_authors_2_by_lines_data).to_csv(f"overall_results/{directory.split('/')[-1]}/common_authors_2_by_lines/{file}", index=False)

    return file_type_percentages, overall_results


def process_results(file_types, source_name):
    entries_result = 0
    matches_result = 0
    non_matches_result = 0

    for file_type, matches in file_types.items():
        print(
            f"{source_name} {file_type} {matches[0]}/{matches[2]} ({matches[0] / matches[2] * 100:.2f}%) non matches {matches[1]}")
        entries_result += matches[2]
        non_matches_result += matches[1]
        matches_result += matches[0]

    print(
        f"{source_name} total matches {matches_result}/{entries_result} ({matches_result / entries_result * 100:.2f}%) non matches {non_matches_result}")
    return matches_result, non_matches_result, entries_result

async def run_in_executor(executor, func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, func, *args)

async def print_results(directory, full):
    # Define directories and their parameters
    subdirectories = [
        (os.path.join(directory, 'cran'), 0),
        (os.path.join(directory, 'pypi'), 1),
        (os.path.join(directory, 'cff'), 2),
        (os.path.join(directory, 'pypi_cff'), 3),
        (os.path.join(directory, 'cran_cff'), 4),
    ]

    # Create a ProcessPoolExecutor for multiprocessing
    with ProcessPoolExecutor() as executor:
        # Run all tasks concurrently
        tasks = [run_in_executor(executor, process_directory, dir_path, index, full) for dir_path, index in
                 subdirectories]
        results = await asyncio.gather(*tasks)
        results, overall_results = zip(*results)

    # Handle results
    cran_file_types, pypi_file_types, cff_file_types, pypi_cff_file_types, cran_cff_file_types = results
    cran_overall_results, pypi_overall_results, cff_overall_results, pypi_cff_overall_results, cran_cff_overall_results = overall_results

    combined_overall_results = pd.DataFrame([cran_overall_results, pypi_overall_results, cff_overall_results, pypi_cff_overall_results, cran_cff_overall_results])
    combined_overall_results.index = ['CRAN', 'PyPi', 'CFF', 'PyPi CFF', 'CRAN CFF']

    Path(f"overall_results").mkdir(parents=True, exist_ok=True)

    if full:
        combined_overall_results.to_csv(f"overall_results/overall_full_results.csv", index_label="source")
    else:
        combined_overall_results.to_csv(f"overall_results/overall_results.csv", index_label="source")

    print()

    # Process and print CRAN results
    cran_matches_result, cran_non_matches_result, cran_entries_result = process_results(cran_file_types, "CRAN")
    print()

    # Process and print PyPi results
    pypi_matches_result, pypi_non_matches_result, pypi_entries_result = process_results(pypi_file_types, "PyPi")
    print()

    # Process and print CFF results
    cff_matches_result, cff_non_matches_result, cff_entries_result = process_results(cff_file_types, "CFF")
    print()

    # Process and print PyPi CFF results
    pypi_cff_matches_result, pypi_cff_non_matches_result, pypi_cff_entries_result = process_results(pypi_cff_file_types, "PyPi CFF")
    print()

    # Process and print CRAN CFF results
    cran_cff_matches_result, cran_cff_non_matches_result, cran_cff_entries_result = process_results(cran_cff_file_types, "CRAN CFF")
    print()

    # Calculate total results
    total_matches_result = cran_matches_result + pypi_matches_result + cff_matches_result + pypi_cff_matches_result + cran_cff_matches_result
    total_non_matches_result = cran_non_matches_result + pypi_non_matches_result + cff_non_matches_result + pypi_cff_non_matches_result + cran_cff_non_matches_result
    total_entries_result = cran_entries_result + pypi_entries_result + cff_entries_result + pypi_cff_entries_result + cran_cff_entries_result

    print(
        f"Total matches {total_matches_result}/{total_entries_result} ({total_matches_result / total_entries_result * 100:.2f}%) non matches {total_non_matches_result}")


async def print_latest():
    await print_results('results', full=False)


async def print_full():
    await print_results('results', full=True)


async def main():
    print("Latest results")
    await print_latest()
    print("\n\nResults over time")
    await print_full()

if __name__ == "__main__":
    asyncio.run(main())
