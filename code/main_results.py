import os
import re
from pathlib import Path

import pandas as pd
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

def get_common_authors_count(git_contributors_df: pd.DataFrame, df: pd.DataFrame, common_authors: dict, file: str) -> dict:
    if file not in common_authors:
        common_authors[file] = {}
        for i in range(1, 101):
            common_authors[file][i] = (0, 0)

    for i in range(1, 101):
        most_commits_entry = git_contributors_df.loc[git_contributors_df['commits'].nlargest(i).index]
        common_authors_entry = get_common_authors(most_commits_entry, df)
        common_authors[file][i] = common_authors[file][i][0] + len(common_authors_entry), common_authors[file][i][1] + len(most_commits_entry)

    return common_authors

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

def process_directory(directory, full=True):
    # CFF
    total_cff = 0
    total_cff_full = 0
    total_valid_cff = 0
    total_valid_cff_full = 0
    total_cff_init_used = 0
    total_cff_init_used_full = 0
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
    doi_preferred_citation_cff_full = 0
    identifier_doi_preferred_citation_cff = 0
    identifier_doi_preferred_citation_cff_full = 0
    collection_doi_preferred_citation_cff = 0
    collection_doi_preferred_citation_cff_full = 0
    citation_counts_preferred_citation_cff = {}
    citation_counts_preferred_citation_cff_full = {}

    # Bib
    total_bib = 0
    total_bib_full = 0
    average_time_between_updates_bib = []
    difference_last_update_bib_list = []
    citation_counts_bib = {}
    citation_counts_bib_full = {}

    # Readme
    average_time_between_updates_readme = []
    difference_last_update_readme_list = []

    file_type_percentages = {}
    total_authors = {}
    total_authors_no_commits = {}
    common_authors = {}
    dfs = {}

    # Regular expressions to extract timestamp and file type
    file_patterns = {
        'readme_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_readme_authors_new\.csv'),
        'cff_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_authors_new\.csv'),
        'cff_preferred_citation_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_preferred_citation_authors_new\.csv'),
        'bib_authors_new.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_bib_authors_new\.csv')
    }

    # Track the latest file for each type
    latest_files_by_folder = {}

    for root, _, files in os.walk(directory):
        folder_name = os.path.basename(root)

        if folder_name not in latest_files_by_folder:
            latest_files_by_folder[folder_name] = {file_type: (None, None) for file_type in file_patterns}

        for file in files:
            # Process timestamped files if 'full' is False, otherwise process all files
            if full:
                # Process all timestamped file types
                for file_type, pattern in file_patterns.items():
                    if file.endswith(file_type):
                        file_path = str(os.path.join(root, file))
                        df = get_authors_df(file_path)
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
                    total_valid_cff_full += df['cff_valid'].sum()
                    total_cff_init_used_full += df['cff_init'].sum()
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
                    for key, value in df['type'].value_counts().to_dict().items():
                        citation_counts_bib_full[key] = citation_counts_bib_full.get(key, 0) + value
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
                    doi_preferred_citation_cff_full += df['doi'].notna().sum()
                    identifier_doi_preferred_citation_cff_full += df['identifier-doi'].notna().sum()
                    collection_doi_preferred_citation_cff_full += df['collection-doi'].notna().sum()
                    for key, value in df['type'].value_counts().to_dict().items():
                        citation_counts_preferred_citation_cff_full[key] = citation_counts_preferred_citation_cff_full.get(key, 0) + value
            else:
                if file in ['pypi_maintainers.csv', 'python_authors.csv', 'python_maintainers.csv',
                            'description_authors.csv', 'cran_authors.csv', 'cran_maintainers.csv']:
                    file_path = str(os.path.join(root, file))
                    df = get_authors_df(file_path)

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

                    if file not in total_authors:
                        total_authors[file] = 0
                        total_authors_no_commits[file] = {'1_year': 0, '2_years': 0, '5_years': 0}

                    total_authors[file] += len(df[df['score'] > 0])
                    total_authors_no_commits[file]['1_year'] += len(df[df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365)])
                    total_authors_no_commits[file]['2_years'] += len(df[df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365*2)])
                    total_authors_no_commits[file]['5_years'] += len(df[df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365*5)])

                    common_authors = get_common_authors_count(git_contributors_df, df, common_authors, file)

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
                    if df_sorted.iloc[0]['cff_valid']:
                        total_valid_cff += 1
                    if df_sorted.iloc[0]['cff_init']:
                        total_cff_init_used += 1
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
                    if file_type not in total_authors:
                        total_authors[file_type] = 0
                        total_authors_no_commits[file_type] = {'1_year': 0, '2_years': 0, '5_years': 0}

                    total_authors[file_type] += len(authors_df[authors_df['score'] > 0])
                    total_authors_no_commits[file_type]['1_year'] += len(authors_df[authors_df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365)])
                    total_authors_no_commits[file_type]['2_years'] += len(authors_df[authors_df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365*2)])
                    total_authors_no_commits[file_type]['5_years'] += len(authors_df[authors_df['last_commit'] < git_contributors_df['last_commit'].max() - pd.Timedelta(days=365*5)])

                    common_authors = get_common_authors_count(git_contributors_df, authors_df, common_authors, file_type)

        similarity_with_non_matches = []
        similarity_without_non_matches = []
        for folder, df_list in dfs.items():
            if len(df_list) > 1:
                similarity_with_non_matches.append(calculate_similarity_with_non_matches(df_list))
                similarity_without_non_matches.append(calculate_similarity_without_non_matches(df_list))

    # Convert percentages to tuple format before returning
    file_type_percentages = {ft: (data['matches'], data['non_matches'], data['entries']) for ft, data in
                             file_type_percentages.items()}

    if full:
        print(f"Total valid {directory.split('/')[-1]} CFF: {total_valid_cff_full}/{total_cff_full}")
        print(f"Total cff_init used {directory.split('/')[-1]} CFF: {total_cff_init_used_full}/{total_cff_full}")
        print(f"Total valid CFF cff_init used {directory.split('/')[-1]} CFF: {total_valid_cff_cff_init_used_full}/{total_cff_full}")
        print(f"Total valid CFF cff_init not used {directory.split('/')[-1]} CFF: {total_valid_cff_cff_init_not_used_full}/{total_cff_full}")
        print(f"Total invalid CFF cff_init used {directory.split('/')[-1]} CFF: {total_invalid_cff_cff_init_used_full}/{total_cff_full}")
        print(f"Total invalid CFF cff_init not used {directory.split('/')[-1]} CFF: {total_invalid_cff_cff_init_not_used_full}/{total_cff_full}")
        print(f"DOI {directory.split('/')[-1]} CFF: {doi_cff_full}/{total_cff_full}")
        print(f"Identifier DOI {directory.split('/')[-1]} CFF: {identifier_doi_cff_full}/{total_cff_full}")
        print(f"DOI preferred citation {directory.split('/')[-1]} CFF: {doi_preferred_citation_cff_full}/{total_preferred_citation_cff_full}")
        print(f"Identifier DOI preferred citation {directory.split('/')[-1]} CFF: {identifier_doi_preferred_citation_cff_full}/{total_preferred_citation_cff_full}")
        print(f"Collection DOI preferred citation {directory.split('/')[-1]} CFF: {collection_doi_preferred_citation_cff_full}/{total_preferred_citation_cff_full}")
        for key, value in citation_counts_cff_full.items():
            print(f"Citation counts for {key} CFF: {value}/{total_cff_full}")
        for key, value in citation_counts_preferred_citation_cff_full.items():
            print(f"Citation counts for preferred citation {key} CFF: {value}/{total_preferred_citation_cff_full}")
        for key, value in citation_counts_bib_full.items():
            print(f"Citation counts for {key} Bib: {value}/{total_bib_full}")
        average_time_between_updates_cff = pd.Series(average_time_between_updates_cff).mean()
        print(f"Average time between updates for {directory.split('/')[-1]} CFF: {average_time_between_updates_cff}")
        average_time_between_updates_bib = pd.Series(average_time_between_updates_bib).mean()
        print(f"Average time between updates for {directory.split('/')[-1]} Bib: {average_time_between_updates_bib}")
        average_time_between_updates_readme = pd.Series(average_time_between_updates_readme).mean()
        print(f"Average time between updates for {directory.split('/')[-1]} Readme: {average_time_between_updates_readme}")
        print()
    else:
        print(f"Total valid {directory.split('/')[-1]} CFF: {total_valid_cff}/{total_cff}")
        print(f"Total cff_init used {directory.split('/')[-1]} CFF: {total_cff_init_used}/{total_cff}")
        print(f"Total valid CFF cff_init used {directory.split('/')[-1]} CFF: {total_valid_cff_cff_init_used}/{total_cff}")
        print(f"Total valid CFF cff_init not used {directory.split('/')[-1]} CFF: {total_valid_cff_cff_init_not_used}/{total_cff}")
        print(f"Total invalid CFF cff_init used {directory.split('/')[-1]} CFF: {total_invalid_cff_cff_init_used}/{total_cff}")
        print(f"Total invalid CFF cff_init not used {directory.split('/')[-1]} CFF: {total_invalid_cff_cff_init_not_used}/{total_cff}")
        print(f"DOI {directory.split('/')[-1]} CFF: {doi_cff}/{total_cff}")
        print(f"Identifier DOI {directory.split('/')[-1]} CFF: {identifier_doi_cff}/{total_cff}")
        print(f"DOI preferred citation {directory.split('/')[-1]} CFF: {doi_preferred_citation_cff}/{total_preferred_citation_cff}")
        print(f"Identifier DOI preferred citation {directory.split('/')[-1]} CFF: {identifier_doi_preferred_citation_cff}/{total_preferred_citation_cff}")
        print(f"Collection DOI preferred citation {directory.split('/')[-1]} CFF: {collection_doi_preferred_citation_cff}/{total_preferred_citation_cff}")
        for key, value in citation_counts_cff.items():
            print(f"Citation counts for {key} CFF: {value}/{total_cff}")
        for key, value in citation_counts_preferred_citation_cff.items():
            print(f"Citation counts for preferred citation {key} CFF: {value}/{total_preferred_citation_cff}")
        for key, value in citation_counts_bib.items():
            print(f"Citation counts for {key} Bib: {value}/{total_bib}")
        average_time_last_update_cff = pd.Series(difference_last_update_cff_list).mean()
        print(f"Average time between last update and last commit for {directory.split('/')[-1]} CFF: {average_time_last_update_cff}")
        average_time_last_update_bib = pd.Series(difference_last_update_bib_list).mean()
        print(f"Average time between last update and last commit for {directory.split('/')[-1]} Bib: {average_time_last_update_bib}")
        average_time_last_update_readme = pd.Series(difference_last_update_readme_list).mean()
        print(f"Average time between last update and last commit for {directory.split('/')[-1]} Readme: {average_time_last_update_readme}")
        for total_authors_no_commits_key, total_authors_no_commits_value in total_authors_no_commits.items():
            print(f"Total authors with no commits in the last year or longer for {directory.split('/')[-1]} {total_authors_no_commits_key}: {total_authors_no_commits_value['1_year']}/{total_authors[total_authors_no_commits_key]}")
            print(f"Total authors with no commits in the last 2 years or longer for {directory.split('/')[-1]} {total_authors_no_commits_key}: {total_authors_no_commits_value['2_years']}/{total_authors[total_authors_no_commits_key]}")
            print(f"Total authors with no commits in the last 5 years or longer for {directory.split('/')[-1]} {total_authors_no_commits_key}: {total_authors_no_commits_value['5_years']}/{total_authors[total_authors_no_commits_key]}")#

        for file, common_authors_data in common_authors.items():
            Path(f"overall_results/{directory.split('/')[-1]}").mkdir(parents=True, exist_ok=True)
            pd.DataFrame(common_authors_data).to_csv(f"overall_results/{directory.split('/')[-1]}/common_authors_{file}.csv", index=False)

        if similarity_with_non_matches:
            print(f"Similarity between the latest files with non-matches: {pd.Series(similarity_with_non_matches).mean() * 100:.2f}%")

        if similarity_without_non_matches:
            print(f"Similarity between the latest files without non-matches: {pd.Series(similarity_without_non_matches).mean() * 100:.2f}%")
        print()

    return file_type_percentages


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


def print_results(directory, full):
    cran_dir = os.path.join(directory, 'cran')
    pypi_dir = os.path.join(directory, 'pypi')
    cff_dir = os.path.join(directory, 'cff')
    pypi_cff_dir = os.path.join(directory, 'pypi_cff')
    cran_cff_dir = os.path.join(directory, 'cran_cff')

    cran_file_types = process_directory(cran_dir, full=full)
    pypi_file_types = process_directory(pypi_dir, full=full)
    cff_file_types = process_directory(cff_dir, full=full)
    pypi_cff_file_types = process_directory(pypi_cff_dir, full=full)
    cran_cff_file_types = process_directory(cran_cff_dir, full=full)

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


def print_latest():
    print_results('results', full=False)


def print_full():
    print_results('results', full=True)


def main():
    print("Latest results")
    print_latest()
    print("\n\nResults over time")
    print_full()

if __name__ == "__main__":
    main()
