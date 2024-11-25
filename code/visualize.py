import os

import matplotlib.pyplot as plt
import ast
import pandas as pd

sources = {"PyPI": "pypi", "CRAN": "cran", "CFF": "cff", "PyPI CFF": "pypi_cff", "CRAN CFF": "cran_cff"}

file_list = {"CFF": {"file": "common_authors/cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "common_authors/cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "common_authors/cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "common_authors/cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "common_authors/description_authors.csv", "color": "purple"},
             "Readme": {"file": "common_authors/readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "common_authors/bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "common_authors/pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "common_authors/python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "common_authors/python_maintainers.csv", "color": "orange"}}

for source_name, source in sources.items():
    for file_name, info in file_list.items():
        file_path = f"overall_results/{source}/{info['file']}"
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path)
        common_authors = []
        total_authors = []
        relative = [1]

        for name in df.columns:
            common_authors_package = ast.literal_eval(df[name][0])
            total_authors_package = ast.literal_eval(df[name][1])
            if len(common_authors) == 0:
                common_authors = [0] * len(common_authors_package)
                total_authors = [0] * len(total_authors_package)
            relative_package = [1]

            for index, common_author in enumerate(common_authors_package):
                relative_package.append(common_author/total_authors_package[index])
                common_authors[index] += common_authors_package[index]
                total_authors[index] += total_authors_package[index]

            plt.plot(relative_package, alpha=0.05)


        for index, common_author in enumerate(common_authors):
            relative.append(common_author/total_authors[index])

        plt.plot(relative, label=file_name, color=info["color"])

    plt.xlim(1, 100)
    plt.legend(loc="upper right")
    plt.xlabel("Anzahl der betrachteten Git Autoren")
    plt.ylabel("Verhältnis der genannten Autoren an den Git Autoren")
    plt.tight_layout()
    plt.savefig(f"../docs/bilder/common_authors/1_{source}.svg")
    plt.show()

file_list = {"CFF": {"file": "common_authors_2/cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "common_authors_2/cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "common_authors_2/cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "common_authors_2/cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "common_authors_2/description_authors.csv", "color": "purple"},
             "Readme": {"file": "common_authors_2/readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "common_authors_2/bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "common_authors_2/pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "common_authors_2/python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "common_authors_2/python_maintainers.csv", "color": "orange"}}

for source_name, source in sources.items():
    for file_name, info in file_list.items():
        file_path = f"overall_results/{source}/{info['file']}"
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path)
        common_authors = []
        total_authors = 0
        relative = [0]

        for name in df.columns:
            common_authors_package = ast.literal_eval(df[name][0])
            if len(common_authors) == 0:
                common_authors = [0] * len(common_authors_package)
            total_authors_package = int(df[name][1])
            total_authors += total_authors_package
            relative_package = [0]

            for index, common_author in enumerate(common_authors_package):
                relative_package.append(common_author/total_authors_package)
                common_authors[index] += common_author

            plt.plot(relative_package, alpha=0.05)


        for common_author in common_authors:
            relative.append(common_author/total_authors)

        plt.plot(relative, label=file_name, color=info["color"])

    plt.legend(loc="lower right")
    plt.xlabel("Anzahl der betrachteten Git Autoren")
    plt.ylabel("Verhältnis der genannten Autoren an den Git Autoren")
    plt.tight_layout()
    plt.savefig(f"../docs/bilder/common_authors_2/2_{source}.svg")
    plt.show()

file_list = {"CFF": {"file": "total_authors_no_commits/cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "total_authors_no_commits/cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "total_authors_no_commits/cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "total_authors_no_commits/cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "total_authors_no_commits/description_authors.csv", "color": "purple"},
             "Readme": {"file": "total_authors_no_commits/readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "total_authors_no_commits/bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "total_authors_no_commits/pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "total_authors_no_commits/python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "total_authors_no_commits/python_maintainers.csv", "color": "orange"}}

for source_name, source in sources.items():
    for file_name, info in file_list.items():
        file_path = f"overall_results/{source}/{info['file']}"
        if not os.path.exists(file_path):
            continue
        df = pd.read_csv(file_path)
        total_authors_no_commits = []
        total_authors = 0
        relative = [1]

        for name in df.columns:
            total_authors_no_commits_package = ast.literal_eval(df[name][0])
            if len(total_authors_no_commits) == 0:
                total_authors_no_commits = [0] * len(total_authors_no_commits_package)
            total_authors_package = int(df[name][1])

            if total_authors_package == 0:
                continue

            total_authors += total_authors_package
            relative_package = [1]

            for index, authors in enumerate(total_authors_no_commits_package):
                relative_package.append(authors/total_authors_package)
                total_authors_no_commits[index] += authors

            plt.plot(relative_package, alpha=0.05)

        if total_authors == 0:
            continue

        for authors in total_authors_no_commits:
            relative.append(authors/total_authors)

        plt.plot(relative, label=file_name, color=info["color"])

    plt.gca().invert_xaxis()
    plt.legend(loc="upper left")
    plt.xlabel("Tage")
    plt.ylabel("Verhältnis der Autoren ohne Commits")
    plt.tight_layout()
    plt.savefig(f"../docs/bilder/total_authors_no_commits/3_{source}.svg")
    plt.show()
