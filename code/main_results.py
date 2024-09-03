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

def main():
    cran_dir = 'results/cran'
    pypi_dir = 'results/pypi'
    total_matches = 0
    total_non_matches = 0

    for root, _, files in os.walk(cran_dir):
        for file in files:
            if file == 'git_contributors.csv':
                continue
            file_path = os.path.join(root, file)
            matches, non_matches = check_matches(file_path)
            total_matches += matches
            total_non_matches += non_matches

    for root, _, files in os.walk(pypi_dir):
        for file in files:
            if file == 'git_contributors.csv':
                continue
            file_path = os.path.join(root, file)
            matches, non_matches = check_matches(file_path)
            total_matches += matches
            total_non_matches += non_matches

    percentage = calculate_percentage(total_matches, total_non_matches)
    print(f"Percentage of matches: {percentage:.2f}%")

if __name__ == "__main__":
    main()