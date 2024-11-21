import os

import matplotlib.pyplot as plt
import ast
import pandas as pd

sources = {"PyPI": "pypi", "CRAN": "cran", "CFF": "cff", "PyPI CFF": "pypi_cff", "CRAN CFF": "cran_cff"}

file_list = {"CFF": {"file": "common_authors_2_cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "common_authors_2_cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "common_authors_2_cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "common_authors_2_cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "common_authors_2_description_authors.csv", "color": "purple"},
             "Readme": {"file": "common_authors_2_readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "common_authors_2_bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "common_authors_2_pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "common_authors_2_python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "common_authors_2_python_maintainers.csv", "color": "orange"}}

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

            plt.plot(relative_package, alpha=0.1)


        for common_author in common_authors:
            relative.append(common_author/total_authors)

        plt.plot(relative, label=file_name, color=info["color"])

    plt.legend()
    plt.title(f"Anteil der {source_name} Autoren an den Git Autoren")
    plt.xlabel("Anzahl der betrachteten Git Autoren")
    plt.ylabel("Anteil der gemeinsamen Autoren")
    plt.show()
