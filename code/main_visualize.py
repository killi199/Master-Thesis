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
colors = ['#b2df8a', '#33a02c', '#a6cee3', '#1f78b4']
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


def get_cff_doi_plt(results):
    total_cff = results['total_cff']
    doi_cff = results['doi_cff']
    identifier_doi_cff = results['identifier_doi_cff']

    without_doi_cff = total_cff - doi_cff
    without_identifier_doi_cff = total_cff - identifier_doi_cff

    bar_width = 0.35
    index = range(len(total_cff))

    fig, ax = plt.subplots()

    bars_doi = ax.bar(index, doi_cff, bar_width, label='DOI', color='#1f78b4')
    bars_identifier = ax.bar([i + bar_width for i in index], identifier_doi_cff, bar_width, label='Identifier DOI', color='#33a02c')
    bars_without_doi = ax.bar(index, without_doi_cff, bar_width, bottom=doi_cff, label='Ohne DOI', color='#a6cee3')
    bars_without_identifier_doi = ax.bar([i + bar_width for i in index], without_identifier_doi_cff, bar_width, bottom=identifier_doi_cff, label='Ohne Identifier DOI', color='#b2df8a')

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

    bars_doi = ax.bar(index, doi_preferred_citation_cff, bar_width, label='DOI', color='#1f78b4')
    bars_identifier = ax.bar([i + bar_width for i in index], identifier_doi_preferred_citation_cff, bar_width, label='Identifier DOI', color='#33a02c')
    bars_collection = ax.bar([i + 2 * bar_width for i in index], collection_doi_preferred_citation_cff, bar_width, label='Collection DOI', color='#e31a1c')
    bars_without_doi = ax.bar(index, without_doi_preferred_citation_cff, bar_width, bottom=doi_preferred_citation_cff, label='Ohne DOI', color='#a6cee3')
    bars_without_identifier_doi = ax.bar([i + bar_width for i in index], without_identifier_doi_preferred_citation_cff, bar_width, bottom=identifier_doi_preferred_citation_cff, label='Ohne Identifier DOI', color='#b2df8a')
    bars_without_collection_doi = ax.bar([i + 2 * bar_width for i in index], without_collection_doi_preferred_citation_cff, bar_width, bottom=collection_doi_preferred_citation_cff, label='Ohne Collection DOI', color='#fb9a99')

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
            label='Valide CFF mit CFF init', color='#b2df8a')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_valid_cff_cff_init_not_used'],
            label='Valide CFF ohne CFF init', color='#33a02c')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_invalid_cff_cff_init_used'],
            label='Invalide CFF mit CFF init', color='#a6cee3')
    ax.plot(to_timestamp_data['timestamp'], to_timestamp_data['total_invalid_cff_cff_init_not_used'],
            label='Invalide CFF ohne CFF init', color='#1f78b4')

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
