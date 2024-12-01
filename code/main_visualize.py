import glob
import os

import matplotlib.pyplot as plt
import ast
import pandas as pd
from datetime import datetime
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
from tqdm import tqdm

sources = {"Alle CFF": "cff_full"}

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
valid_cff_plot.savefig(f"../docs/bilder/overall_valid_cff_full.svg")
valid_cff_plot.show()

def get_citation_counts_plot(citation_counts):
    citation_data = pd.DataFrame(citation_counts.tolist(), index=overall_results.index).fillna(0)

    fig, ax = plt.subplots()

    bottom = [0] * len(citation_data)

    for column in citation_data.columns:
        bars = ax.bar(citation_data.index, citation_data[column], bottom=bottom, label=column)
        for bar in bars:
            height= bar.get_height()
            if height > 0:
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

    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()

    return plt

def show_and_safe_citation_counts(results):
    citation_counts_cff = results['citation_counts_cff'].apply(eval)
    citation_counts_preferred_citation_cff = results['citation_counts_preferred_citation_cff'].apply(eval)

    citation_counts_cff_plot = get_citation_counts_plot(citation_counts_cff)
    citation_counts_cff_plot.savefig(f"../docs/bilder/citation_counts_cff_full.svg")
    citation_counts_preferred_citation_cff_plot = get_citation_counts_plot(citation_counts_preferred_citation_cff)
    citation_counts_preferred_citation_cff_plot.savefig(f"../docs/bilder/citation_counts_preferred_citation_cff_full.svg")

    citation_counts_cff_plot.show()
    citation_counts_preferred_citation_cff_plot.show()

show_and_safe_citation_counts(overall_results)


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

    for bars in [bars_doi, bars_identifier, bars_without_doi, bars_without_identifier_doi]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.0f}',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=6
                )

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

    for bars in [bars_doi, bars_identifier, bars_collection, bars_without_doi, bars_without_identifier_doi, bars_without_collection_doi]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.0f}',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=6
                )

    ax.set_xlabel('Liste')
    ax.set_ylabel('Preferred Citation CFF Anzahl')
    ax.set_xticks([i + bar_width for i in index])
    ax.set_xticklabels(overall_results.index)
    ax.legend()

    plt.tight_layout()
    return plt

cff_doi_plt = get_cff_doi_plt(overall_results)
cff_doi_plt.savefig(f"../docs/bilder/full_cff_doi.svg")
cff_doi_plt.show()

preferred_citation_doi_plt = get_preferred_citation_doi_plt(overall_results)
preferred_citation_doi_plt.savefig(f"../docs/bilder/full_preferred_citation_doi.svg")
preferred_citation_doi_plt.show()

total_valid_cff = overall_full_results['total_valid_cff']
for index, value in total_valid_cff.items():
    to_timestamp_data = []
    total_valid_cff = pd.DataFrame(ast.literal_eval(value))
    total_valid_cff['timestamp'] = pd.to_datetime(total_valid_cff['timestamp'], utc=True)
    total_valid_cff = total_valid_cff.sort_values(by='timestamp')
    for list_index, row in tqdm(total_valid_cff.iterrows(), total=total_valid_cff.shape[0]):
        total_valid_cff_until_timestamp = total_valid_cff[total_valid_cff['timestamp'] <= row['timestamp']]
        total_valid_cff_without_duplicates = total_valid_cff_until_timestamp.drop_duplicates(subset=['package'], keep='last')
        total_valid_cff_cff_init_used = total_valid_cff_without_duplicates[(total_valid_cff_without_duplicates['cff_init'] == True) & (total_valid_cff_without_duplicates['cff_valid'] == True)].shape[0]
        total_valid_cff_cff_init_not_used = total_valid_cff_without_duplicates[(total_valid_cff_without_duplicates['cff_init'] == False) & (total_valid_cff_without_duplicates['cff_valid'] == True)].shape[0]
        total_invalid_cff_cff_init_used = total_valid_cff_without_duplicates[(total_valid_cff_without_duplicates['cff_init'] == True) & (total_valid_cff_without_duplicates['cff_valid'] == False)].shape[0]
        total_invalid_cff_cff_init_not_used = total_valid_cff_without_duplicates[(total_valid_cff_without_duplicates['cff_init'] == False) & (total_valid_cff_without_duplicates['cff_valid'] == False)].shape[0]

        to_timestamp_data.append({'timestamp': row['timestamp'],
                                  'total_valid_cff_cff_init_used': total_valid_cff_cff_init_used,
                                  'total_valid_cff_cff_init_not_used': total_valid_cff_cff_init_not_used,
                                  'total_invalid_cff_cff_init_used': total_invalid_cff_cff_init_used,
                                  'total_invalid_cff_cff_init_not_used': total_invalid_cff_cff_init_not_used})

    to_timestamp_data = pd.DataFrame(to_timestamp_data)
    fig, ax = plt.subplots()
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_valid_cff_cff_init_used'],
            label='Valid CFF with CFF init', color='green')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_valid_cff_cff_init_not_used'],
            label='Valid CFF without CFF init', color='lightgreen')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_invalid_cff_cff_init_used'],
            label='Invalid CFF with CFF init', color='red')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_invalid_cff_cff_init_not_used'],
            label='Invalid CFF without CFF init', color='lightcoral')

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    plt.xticks(rotation=45)

    ax.set_xlabel('Zeit')
    ax.set_ylabel('Anzahl')
    ax.legend()
    plt.tight_layout()
    index = index.lower().replace(' ', '_')
    plt.savefig(f"../docs/bilder/valid_cff_by_time/overall_valid_cff_{index}.svg")
    plt.show()

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

columns = {'cff_authors_new.csv': 'CFF',
           'cff_preferred_citation_authors_new.csv': 'CFF preferred citation'}

added_authors_data.rename(columns=columns, inplace=True)
removed_authors_data.rename(columns=columns, inplace=True)

added_authors_data = added_authors_data[['CFF', 'CFF preferred citation']]
removed_authors_data = removed_authors_data[['CFF', 'CFF preferred citation']]

added_removed_authors_plt = get_removed_added_authors_plt(added_authors_data, removed_authors_data)
added_removed_authors_plt.savefig(f"../docs/bilder/added_removed_authors_without_readme_full.svg")
added_removed_authors_plt.show()

added_authors = overall_full_results['authors_added_without_first_timestamp'].apply(eval)

added_authors_data = pd.DataFrame(added_authors.tolist(), index=overall_full_results.index).fillna(0)

columns = {'cff_authors_new.csv': 'CFF',
           'cff_preferred_citation_authors_new.csv': 'CFF preferred citation',}

added_authors_data.rename(columns=columns, inplace=True)

added_authors_data = added_authors_data[['CFF', 'CFF preferred citation']]

added_authors_plt = get_added_authors_plt(added_authors_data)
added_authors_plt.savefig(f"../docs/bilder/added_authors_without_readme_without_first_timestamp_full.svg")
added_authors_plt.show()
