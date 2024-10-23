import os
import re
import pandas as pd
from datetime import datetime

def check_matches(file_path):
    df = pd.read_csv(file_path)
    matches = (df['score'] > 0).sum()
    non_matches = (df['score'] == 0).sum()
    entries = len(df)
    return matches, non_matches, entries


def process_directory(directory, full=True):
    file_type_percentages = {}

    # Regular expressions to extract timestamp and file type
    file_patterns = {
        'readme_authors.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_readme_authors\.csv'),
        'cff_authors.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_authors\.csv'),
        'cff_preferred_citation_authors.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_cff_preferred_citation_authors\.csv'),
        'bib_authors.csv': re.compile(r'(\d{8}_\d{6}[+-]\d{4})_bib_authors\.csv')
    }

    # Track the latest file for each type
    latest_files_by_folder = {}

    for root, _, files in os.walk(directory):
        folder_name = os.path.basename(root)

        if folder_name not in latest_files_by_folder:
            latest_files_by_folder[folder_name] = {file_type: (None, None) for file_type in file_patterns}

        for file in files:
            # Process non-timestamped common CSV files
            if file in ['pypi_maintainers.csv', 'python_authors.csv', 'python_maintainers.csv',
                        'description_authors.csv', 'cran_authors.csv', 'cran_maintainers.csv']:
                file_path = os.path.join(root, file)
                matches, non_matches, entries = check_matches(file_path)

                file_base = os.path.splitext(file)[0]
                if file_base not in file_type_percentages:
                    file_type_percentages[file_base] = {'matches': 0, 'non_matches': 0, 'entries': 0}
                file_type_percentages[file_base]['matches'] += matches
                file_type_percentages[file_base]['non_matches'] += non_matches
                file_type_percentages[file_base]['entries'] += entries

            # Process timestamped files if 'full' is False, otherwise process all files
            if full:
                # Process all timestamped file types
                for file_type, pattern in file_patterns.items():
                    if file.endswith(file_type):
                        file_path = os.path.join(root, file)
                        matches, non_matches, entries = check_matches(file_path)

                        if file_type not in file_type_percentages:
                            file_type_percentages[file_type] = {'matches': 0, 'non_matches': 0, 'entries': 0}

                        file_type_percentages[file_type]['matches'] += matches
                        file_type_percentages[file_type]['non_matches'] += non_matches
                        file_type_percentages[file_type]['entries'] += entries
            else:
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

    # After the loop, process the latest files if 'full' is False
    if not full:
        for folder, file_data in latest_files_by_folder.items():
            for file_type, (latest_file_path, _) in file_data.items():
                if latest_file_path:
                    matches, non_matches, entries = check_matches(latest_file_path)
                    if file_type not in file_type_percentages:
                        file_type_percentages[file_type] = {'matches': 0, 'non_matches': 0, 'entries': 0}
                    file_type_percentages[file_type]['matches'] += matches
                    file_type_percentages[file_type]['non_matches'] += non_matches
                    file_type_percentages[file_type]['entries'] += entries

    # Convert percentages to tuple format before returning
    file_type_percentages = {ft: (data['matches'], data['non_matches'], data['entries']) for ft, data in
                             file_type_percentages.items()}

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

    cran_file_types = process_directory(cran_dir, full=full)
    pypi_file_types = process_directory(pypi_dir, full=full)
    cff_file_types = process_directory(cff_dir, full=full)

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

    # Calculate total results
    total_matches_result = cran_matches_result + pypi_matches_result + cff_matches_result
    total_non_matches_result = cran_non_matches_result + pypi_non_matches_result + cff_non_matches_result
    total_entries_result = cran_entries_result + pypi_entries_result + cff_entries_result

    print(
        f"Total matches {total_matches_result}/{total_entries_result} ({total_matches_result / total_entries_result * 100:.2f}%) non matches {total_non_matches_result}")


def print_latest():
    print_results('results', full=False)


def print_full():
    print_results('results', full=True)


def main():
    print("Latest results")
    print_latest()
    print("\n\nFull results")
    print_full()

if __name__ == "__main__":
    main()
