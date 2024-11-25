import os

import matplotlib.pyplot as plt
import ast
import pandas as pd

def common_authors_plot(file_list, sources, commits):
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
        if commits:
            plt.savefig(f"../docs/bilder/common_authors/1_{source}.svg")
        else:
            plt.savefig(f"../docs/bilder/common_authors_by_files/1_{source}_by_files.svg")
        plt.show()

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

common_authors_plot(file_list, sources, True)

file_list = {"CFF": {"file": "common_authors_by_files/cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "common_authors_by_files/cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "common_authors_by_files/cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "common_authors_by_files/cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "common_authors_by_files/description_authors.csv", "color": "purple"},
             "Readme": {"file": "common_authors_by_files/readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "common_authors_by_files/bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "common_authors_by_files/pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "common_authors_by_files/python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "common_authors_by_files/python_maintainers.csv", "color": "orange"}}

common_authors_plot(file_list, sources, False)

def common_authors_2_plot(file_list, sources, commits):
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
        if commits:
            plt.savefig(f"../docs/bilder/common_authors_2/2_{source}.svg")
        else:
            plt.savefig(f"../docs/bilder/common_authors_2_by_files/2_{source}_by_files.svg")
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

common_authors_2_plot(file_list, sources, True)

file_list = {"CFF": {"file": "common_authors_2_by_files/cff_authors_new.csv", "color": "blue"},
             "CFF preferred citation": {"file": "common_authors_2_by_files/cff_preferred_citation_authors_new.csv", "color": "green"},
             "CRAN Authors": {"file": "common_authors_2_by_files/cran_authors.csv", "color": "red"},
             "CRAN Maintainers": {"file": "common_authors_2_by_files/cran_maintainers.csv", "color": "orange"},
             "Beschreibung": {"file": "common_authors_2_by_files/description_authors.csv", "color": "purple"},
             "Readme": {"file": "common_authors_2_by_files/readme_authors_new.csv", "color": "brown"},
             "BibTeX": {"file": "common_authors_2_by_files/bib_authors_new.csv", "color": "cyan"},
             "PyPI Maintainers": {"file": "common_authors_2_by_files/pypi_maintainers.csv", "color": "olive"},
             "Python Authors": {"file": "common_authors_2_by_files/python_authors.csv", "color": "red"},
             "Python Maintainers": {"file": "common_authors_2_by_files/python_maintainers.csv", "color": "orange"}}

common_authors_2_plot(file_list, sources, False)

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

overall_results = pd.read_csv("overall_results/overall_results.csv", index_col=0)
overall_full_results = pd.read_csv("overall_results/overall_full_results.csv", index_col=0)

# Create a stacked bar chart for each source in the overall_results DataFrame
categories = ['total_valid_cff_cff_init_used', 'total_valid_cff_cff_init_not_used', 'total_invalid_cff_cff_init_used', 'total_invalid_cff_cff_init_not_used']
colors = ['green', 'lightgreen', 'red', 'lightcoral']
names= ['Valide CFF mit CFF init', 'Valide CFF ohne CFF init', 'Invalide CFF mit CFF init', 'Invalide CFF ohne CFF init']

# Plot the stacked bar chart
def get_valid_cff_plot(data, text):
    fig, ax = plt.subplots()

    # Create a bar for each source
    bottom = [0] * len(overall_results)


    for idx, category in enumerate(categories):
        bars = ax.bar(overall_results.index, data[category], bottom=bottom, label=names[idx], color=colors[idx])
        for bar in bars:
            height = bar.get_height()
            if height > 0 and text:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.0f}',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=8
                )
        bottom = [i + j for i, j in zip(bottom, data[category])]

    ax.set_xlabel('Liste')
    ax.set_ylabel('Anzahl')
    ax.legend(loc='upper left')

    plt.tight_layout()
    return plt

overall_data = overall_results[categories]

valid_cff_plot = get_valid_cff_plot(overall_data, True)
valid_cff_plot.savefig(f"../docs/bilder/overall_valid_cff.svg")
valid_cff_plot.show()

overall_full_data = overall_full_results[categories]

valid_cff_full_plot = get_valid_cff_plot(overall_full_data, False)
valid_cff_full_plot.savefig(f"../docs/bilder/overall_full_valid_cff.svg")
valid_cff_full_plot.show()

def get_citation_counts_plot(citation_counts, text):
    citation_data = pd.DataFrame(citation_counts.tolist(), index=overall_results.index).fillna(0)

    fig, ax = plt.subplots()

    bottom = [0] * len(citation_data)

    for column in citation_data.columns:
        bars = ax.bar(citation_data.index, citation_data[column], bottom=bottom, label=column)
        for bar in bars:
            height= bar.get_height()
            if height > 0 and text:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.0f}',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=6
                )
        bottom = [i + j for i, j in zip(bottom, citation_data[column])]

    ax.set_xlabel('Source')
    ax.set_ylabel('Number of Citations')
    ax.legend(loc='upper left')

    plt.tight_layout()

    return plt

def show_and_safe_citation_counts(results, text):
    citation_counts_cff = results['citation_counts_cff'].apply(eval)
    citation_counts_preferred_citation_cff = results['citation_counts_preferred_citation_cff'].apply(eval)
    citation_counts_bib = results['citation_counts_bib'].apply(eval)

    if text:
        citation_counts_cff_plot = get_citation_counts_plot(citation_counts_cff, text)
        citation_counts_cff_plot.savefig(f"../docs/bilder/citation_counts_cff.svg")
        citation_counts_preferred_citation_cff_plot = get_citation_counts_plot(citation_counts_preferred_citation_cff, text)
        citation_counts_preferred_citation_cff_plot.savefig(f"../docs/bilder/citation_counts_preferred_citation_cff.svg")
        citation_counts_bib_plot = get_citation_counts_plot(citation_counts_bib, text)
        citation_counts_bib_plot.savefig(f"../docs/bilder/citation_counts_bib.svg")
    else:
        citation_counts_cff_plot = get_citation_counts_plot(citation_counts_cff, text)
        citation_counts_cff_plot.savefig(f"../docs/bilder/citation_counts_full_cff.svg")
        citation_counts_preferred_citation_cff_plot = get_citation_counts_plot(citation_counts_preferred_citation_cff, text)
        citation_counts_preferred_citation_cff_plot.savefig(f"../docs/bilder/citation_counts_full_preferred_citation_cff.svg")
        citation_counts_bib_plot = get_citation_counts_plot(citation_counts_bib, text)
        citation_counts_bib_plot.savefig(f"../docs/bilder/citation_counts_full_bib.svg")

    citation_counts_cff_plot.show()
    citation_counts_preferred_citation_cff_plot.show()
    citation_counts_bib_plot.show()

show_and_safe_citation_counts(overall_results, True)
show_and_safe_citation_counts(overall_full_results, False)

def get_removed_added_authors_plt(added_data, removed_data):
    bar_width = 0.35
    index = range(len(added_data))

    fig, ax = plt.subplots()

    bottom_added = [0] * len(added_data)
    bottom_removed = [0] * len(removed_data)

    colors_added = ['blue', 'orange', 'green', 'olive']
    colors_removed = ['pink', 'gray', 'brown', 'cyan']

    for idx, column in enumerate(added_data.columns):
        bars_added = ax.bar(index, added_data[column], bar_width, bottom=bottom_added,
                            label=f'Hinzugefügte {column} Autoren', color=colors_added[idx])
        bottom_added = [i + j for i, j in zip(bottom_added, added_data[column])]

    for idx, column in enumerate(removed_data.columns):
        bars_removed = ax.bar([i + bar_width for i in index], removed_data[column], bar_width,
                              bottom=bottom_removed, label=f'Gelöschte {column} Autoren', color=colors_removed[idx])
        bottom_removed = [i + j for i, j in zip(bottom_removed, removed_data[column])]

    ax.set_xlabel('Liste')
    ax.set_ylabel('Anzahl der Autoren')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(added_data.index)
    ax.legend(loc='upper left')

    plt.tight_layout()

    return plt

def get_added_authors_plt(added_data):
    index = range(len(added_data))

    fig, ax = plt.subplots()

    bottom_added = [0] * len(added_data)

    colors_added = ['blue', 'orange', 'green', 'olive']

    for idx, column in enumerate(added_data.columns):
        bars_added = ax.bar(index, added_data[column], bottom=bottom_added,
                            label=f'Hinzugefügte {column} Autoren', color=colors_added[idx])
        bottom_added = [i + j for i, j in zip(bottom_added, added_data[column])]

    ax.set_xlabel('Liste')
    ax.set_ylabel('Anzahl der Autoren')
    ax.set_xticks(range(len(added_data.index)))
    ax.set_xticklabels(added_data.index)
    ax.legend(loc='upper left')

    plt.tight_layout()

    return plt

added_authors = overall_full_results['authors_added'].apply(eval)
removed_authors = overall_full_results['authors_removed'].apply(eval)

added_authors_data = pd.DataFrame(added_authors.tolist(), index=overall_full_results.index).fillna(0)
removed_authors_data = pd.DataFrame(removed_authors.tolist(), index=overall_full_results.index).fillna(0)

columns = {'readme_authors_new.csv': 'README',
           'cff_authors_new.csv': 'CFF',
           'cff_preferred_citation_authors_new.csv': 'CFF preferred citation',
           'bib_authors_new.csv': 'BibTeX'}

added_authors_data.rename(columns=columns, inplace=True)
removed_authors_data.rename(columns=columns, inplace=True)

added_authors_data = added_authors_data[['CFF', 'CFF preferred citation', 'BibTeX', 'README']]
removed_authors_data = removed_authors_data[['CFF', 'CFF preferred citation', 'BibTeX', 'README']]

added_removed_authors_plt = get_removed_added_authors_plt(added_authors_data, removed_authors_data)
added_removed_authors_plt.savefig(f"../docs/bilder/added_removed_authors.svg")
added_removed_authors_plt.show()

added_authors_data = added_authors_data.drop(columns=['README'])
removed_authors_data = removed_authors_data.drop(columns=['README'])

added_removed_authors_plt = get_removed_added_authors_plt(added_authors_data, removed_authors_data)
added_removed_authors_plt.savefig(f"../docs/bilder/added_removed_authors_without_readme.svg")
added_removed_authors_plt.show()

added_authors = overall_full_results['authors_added_without_first_timestamp'].apply(eval)

added_authors_data = pd.DataFrame(added_authors.tolist(), index=overall_full_results.index).fillna(0)

columns = {'readme_authors_new.csv': 'README',
           'cff_authors_new.csv': 'CFF',
           'cff_preferred_citation_authors_new.csv': 'CFF preferred citation',
           'bib_authors_new.csv': 'BibTeX'}

added_authors_data.rename(columns=columns, inplace=True)

added_authors_data = added_authors_data[['CFF', 'CFF preferred citation', 'BibTeX', 'README']]

added_authors_plt = get_added_authors_plt(added_authors_data)
added_authors_plt.savefig(f"../docs/bilder/added_authors_without_first_timestamp.svg")
added_authors_plt.show()

added_authors_data = added_authors_data.drop(columns=['README'])

added_authors_plt = get_added_authors_plt(added_authors_data)
added_authors_plt.savefig(f"../docs/bilder/added_authors_without_readme_without_first_timestamp.svg")
added_authors_plt.show()

def get_cff_doi_plt(results):
    total_cff = results['total_cff']
    doi_cff = results['doi_cff']
    identifier_doi_cff = results['identifier_doi_cff']

    without_doi_cff = total_cff - doi_cff
    without_identifier_doi_cff = total_cff - identifier_doi_cff

    bar_width = 0.35
    index = range(len(total_cff))

    fig, ax = plt.subplots()

    bars_doi = ax.bar(index, doi_cff, bar_width, label='DOI', color='blue')

    bars_identifier = ax.bar([i + bar_width for i in index], identifier_doi_cff, bar_width, label='Identifier DOI', color='green')

    bars_without_doi = ax.bar(index, without_doi_cff, bar_width, bottom=doi_cff, label='Ohne DOI', color='lightblue')
    bars_without_identifier_doi = ax.bar([i + bar_width for i in index], without_identifier_doi_cff, bar_width, bottom=identifier_doi_cff, label='Ohne Identifier DOI', color='lightgreen')

    ax.set_xlabel('Liste')
    ax.set_ylabel('CFF Anzahl')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(results.index)
    ax.legend()

    plt.tight_layout()
    return plt

def get_preferred_citation_doi_plt(results):
    total_preferred_citation_cff = results['total_preferred_citation_cff']
    doi_preferred_citation_cff = results['doi_preferred_citation_cff']
    identifier_doi_preferred_citation_cff = results['identifier_doi_preferred_citation_cff']
    collection_doi_preferred_citation_cff = results['collection_doi_preferred_citation_cff']

    without_doi_preferred_citation_cff = total_preferred_citation_cff - doi_preferred_citation_cff
    without_identifier_doi_preferred_citation_cff = total_preferred_citation_cff - identifier_doi_preferred_citation_cff
    without_collection_doi_preferred_citation_cff = total_preferred_citation_cff - collection_doi_preferred_citation_cff

    bar_width = 0.25
    index = range(len(total_preferred_citation_cff))

    fig, ax = plt.subplots()

    bars_doi = ax.bar(index, doi_preferred_citation_cff, bar_width, label='DOI', color='blue')

    bars_identifier = ax.bar([i + bar_width for i in index], identifier_doi_preferred_citation_cff, bar_width, label='Identifier DOI', color='green')

    bars_collection = ax.bar([i + 2 * bar_width for i in index], collection_doi_preferred_citation_cff, bar_width, label='Collection DOI', color='red')

    bars_without_doi = ax.bar(index, without_doi_preferred_citation_cff, bar_width, bottom=doi_preferred_citation_cff, label='Ohne DOI', color='lightblue')
    bars_without_identifier_doi = ax.bar([i + bar_width for i in index], without_identifier_doi_preferred_citation_cff, bar_width, bottom=identifier_doi_preferred_citation_cff, label='Ohne Identifier DOI', color='lightgreen')
    bars_without_collection_doi = ax.bar([i + 2 * bar_width for i in index], without_collection_doi_preferred_citation_cff, bar_width, bottom=collection_doi_preferred_citation_cff, label='Ohne Collection DOI', color='lightcoral')

    ax.set_xlabel('Liste')
    ax.set_ylabel('Preferred Citation CFF Anzahl')
    ax.set_xticks([i + bar_width for i in index])
    ax.set_xticklabels(overall_results.index)
    ax.legend()

    plt.tight_layout()
    return plt

def get_bib_doi_plt(results):
    total_bib = results['total_bib']
    doi_bib = results['doi_bib']

    without_doi_bib = total_bib - doi_bib

    index = range(len(total_bib))

    fig, ax = plt.subplots()

    bars_doi = ax.bar(index, doi_bib, label='DOI', color='blue')

    bars_without_doi = ax.bar(index, without_doi_bib, bottom=doi_bib, label='Ohne DOI', color='lightblue')

    ax.set_xlabel('Liste')
    ax.set_ylabel('BibTeX Anzahl')
    ax.set_xticks(range(len(results.index)))
    ax.set_xticklabels(results.index)
    ax.legend()

    plt.tight_layout()
    return plt

cff_doi_plt = get_cff_doi_plt(overall_results)
cff_doi_plt.savefig(f"../docs/bilder/cff_doi.svg")
cff_doi_plt.show()

preferred_citation_doi_plt = get_preferred_citation_doi_plt(overall_results)
preferred_citation_doi_plt.savefig(f"../docs/bilder/preferred_citation_doi.svg")
preferred_citation_doi_plt.show()

bib_doi_plt = get_bib_doi_plt(overall_results)
bib_doi_plt.savefig(f"../docs/bilder/bib_doi.svg")
bib_doi_plt.show()

cff_doi_plt_full = get_cff_doi_plt(overall_full_results)
cff_doi_plt_full.savefig(f"../docs/bilder/cff_doi_full.svg")
cff_doi_plt_full.show()

preferred_citation_doi_plt_full = get_preferred_citation_doi_plt(overall_full_results)
preferred_citation_doi_plt_full.savefig(f"../docs/bilder/preferred_citation_doi_full.svg")
preferred_citation_doi_plt_full.show()

bib_doi_plt_full = get_bib_doi_plt(overall_full_results)
bib_doi_plt_full.savefig(f"../docs/bilder/bib_doi_full.svg")
bib_doi_plt_full.show()
