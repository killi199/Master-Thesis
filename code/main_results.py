import os
import pandas as pd

def check_matches(file_path):
    df = pd.read_csv(file_path)
    matches = (df['score'] > 0).sum()
    non_matches = (df['score'] == 0).sum()
    entries = len(df)
    return matches, non_matches, entries

def process_directory(directory):
    file_type_percentages = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('authors.csv') or file.endswith('maintainers.csv'):
                continue
            file_path = os.path.join(root, file)
            matches, non_matches, entries = check_matches(file_path)

            file = os.path.splitext(file)[0]
            if file not in file_type_percentages:
                file_type_percentages[file] = {'matches': 0, 'non_matches': 0, 'entries': 0}
            file_type_percentages[file]['matches'] += matches
            file_type_percentages[file]['non_matches'] += non_matches
            file_type_percentages[file]['entries'] += entries

    file_type_percentages = {ft: (data['matches'], data['non_matches'], data['entries']) for ft, data in file_type_percentages.items()}

    return file_type_percentages

def main():
    cran_dir = 'results/cran'
    pypi_dir = 'results/pypi'

    cran_file_types = process_directory(cran_dir)
    pypi_file_types = process_directory(pypi_dir)

    entries_result = 0
    matches_result = 0
    non_matches_result = 0
    pypi_entries_result = 0
    pypi_matches_result = 0
    pypi_non_matches_result = 0
    cran_entries_result = 0
    cran_matches_result = 0
    cran_non_matches_result = 0

    for file_type, matches in cran_file_types.items():
        print(f"CRAN {file_type} {matches[0]}/{matches[2]} ({matches[0]/matches[2] * 100:.2f}%) non matches {matches[1]}")
        entries_result += matches[2]
        non_matches_result += matches[1]
        matches_result += matches[0]
        cran_entries_result += matches[2]
        cran_non_matches_result += matches[1]
        cran_matches_result += matches[0]

    print(f"CRAN total matches {cran_matches_result}/{cran_entries_result} ({cran_matches_result/cran_entries_result * 100:.2f}%) non matches {cran_non_matches_result}")

    print()

    for file_type, matches in pypi_file_types.items():
        print(f"PyPi {file_type} {matches[0]}/{matches[2]} ({matches[0]/matches[2] * 100:.2f}%) non matches {matches[1]}")
        entries_result += matches[2]
        non_matches_result += matches[1]
        matches_result += matches[0]
        pypi_entries_result += matches[2]
        pypi_non_matches_result += matches[1]
        pypi_matches_result += matches[0]

    print(f"PyPi total matches {pypi_matches_result}/{pypi_entries_result} ({pypi_matches_result / pypi_entries_result * 100:.2f}%) non matches {pypi_non_matches_result}")

    print()

    print(f"Total matches {matches_result}/{entries_result} ({matches_result/entries_result * 100:.2f}%) non matches {non_matches_result}")

if __name__ == "__main__":
    main()
