import os
import pandas as pd

def check_matches(file_path):
    df = pd.read_csv(file_path)
    matches = (df['score'] > 0).sum()
    non_matches = (df['score'] == 0).sum()
    return matches, non_matches

def calculate_percentage(matches, non_matches):
    total = matches + non_matches
    if total == 0:
        return 0
    return (matches / total) * 100

def process_directory(directory):
    file_type_percentages = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file == 'git_contributors.csv':
                continue
            file_path = os.path.join(root, file)
            matches, non_matches = check_matches(file_path)

            file = os.path.splitext(file)[0]
            if file not in file_type_percentages:
                file_type_percentages[file] = {'matches': 0, 'non_matches': 0}
            file_type_percentages[file]['matches'] += matches
            file_type_percentages[file]['non_matches'] += non_matches

    file_type_percentages = {ft: (data['matches'], data['non_matches'] + data['matches']) for ft, data in file_type_percentages.items()}

    return file_type_percentages

def main():
    cran_dir = 'results/cran'
    pypi_dir = 'results/pypi'

    cran_file_types = process_directory(cran_dir)
    pypi_file_types = process_directory(pypi_dir)

    for file_type, percentage in cran_file_types.items():
        print(f"CRAN {file_type} {percentage[0]}/{percentage[1]}")

    for file_type, percentage in pypi_file_types.items():
        print(f"PyPi {file_type} {percentage[0]}/{percentage[1]}")

if __name__ == "__main__":
    main()
