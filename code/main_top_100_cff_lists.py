import os
import pandas as pd
import aiohttp
import asyncio
from tqdm import tqdm

import functions

API_URL = 'https://packages.ecosyste.ms/api/v1/packages/lookup?repository_url='
results_df_sorted = pd.read_csv('github_repo_stars_sorted.csv')

top_100_cff = {}
top_100_cran_cff = {}
top_100_pypi_cff = {}

cff_bar = tqdm(range(100), desc='CFF', position=1)
cran_bar = tqdm(range(100), desc='CRAN', position=2)
pypi_bar = tqdm(range(100), desc='PyPI', position=3)

async def main():
    for entry in tqdm(results_df_sorted.to_dict(orient='records'), desc='Processing Repositories', position=0):
        repo_url = entry['Repository']
        stars = entry['Stars']

        if len(top_100_cff) >= 100 and len(top_100_cran_cff) >= 100 and len(top_100_pypi_cff) >= 100:
            break

        async with aiohttp.ClientSession() as ecosystems_session:
            async with ecosystems_session.get(API_URL + repo_url) as ecosystems_response:
                if ecosystems_response.status == 200:
                    data = await ecosystems_response.json()
                    pypi_data = []
                    cran_data = []
                    cff_data = []

                    for response_data_entry in data:
                        if response_data_entry.get('ecosystem', '') == 'pypi' and response_data_entry.get('downloads', None) is not None:
                            pypi_data.append(response_data_entry)

                    for response_data_entry in data:
                        if response_data_entry.get('ecosystem', '') == 'cran' and response_data_entry.get('downloads', None) is not None:
                            cran_data.append(response_data_entry)

                    for response_data_entry in data:
                        if response_data_entry.get('downloads', None) is not None:
                            cff_data.append(response_data_entry)

                    if pypi_data and len(top_100_pypi_cff) < 100:
                        most_downloaded_pypi = max(pypi_data, key=lambda x: x.get('downloads', 0))
                        name = most_downloaded_pypi.get('name', '')
                        purl = most_downloaded_pypi.get('purl', '')

                        async with aiohttp.ClientSession() as pypi_session:
                            async with pypi_session.get(f"https://pypi.org/pypi/{name}/json") as pypi_response:
                                pypi_data = await pypi_response.json()
                                try:
                                    functions.get_pypi_repo(pypi_data)
                                    top_100_pypi_cff[purl] = {
                                        'Repository': repo_url,
                                        'Stars': stars,
                                        'Ecosystem': most_downloaded_pypi.get('ecosystem', ''),
                                        'Name': name,
                                    }
                                    pypi_bar.update(1)
                                except ValueError:
                                    pass

                    if cran_data and len(top_100_cran_cff) < 100:
                        most_downloaded_cran = max(cran_data, key=lambda x: x.get('downloads', 0))
                        name = most_downloaded_cran.get('name', '')
                        purl = most_downloaded_cran.get('purl', '')

                        async with aiohttp.ClientSession() as cran_session:
                            async with cran_session.get(f"https://crandb.r-pkg.org/{name}") as cran_response:
                                cran_data = await cran_response.json()
                                try:
                                    functions.get_cran_repo(cran_data)
                                    top_100_cran_cff[purl] = {
                                        'Repository': repo_url,
                                        'Stars': stars,
                                        'Ecosystem': most_downloaded_cran.get('ecosystem', ''),
                                        'Name': name,
                                    }
                                    cran_bar.update(1)
                                except ValueError:
                                    pass

                    if len(top_100_cff) < 100:
                        if not data:
                            top_100_cff[repo_url] = {
                                'Repository': repo_url,
                                'Stars': stars,
                                'Ecosystem': None,
                                'Name': None,
                            }
                        elif not cff_data:
                            purl = data[0].get('purl', '')
                            top_100_cff[purl] = {
                                'Repository': repo_url,
                                'Stars': stars,
                                'Ecosystem': None,
                                'Name': None,
                            }
                        else:
                            most_downloaded_cff = max(cff_data, key=lambda x: x.get('downloads', 0))
                            name = most_downloaded_cff.get('name', '')
                            purl = most_downloaded_cff.get('purl', '')

                            if most_downloaded_cff.get('ecosystem', '') == 'pypi':
                                async with aiohttp.ClientSession() as pypi_session:
                                    async with pypi_session.get(f"https://pypi.org/pypi/{name}/json") as pypi_response:
                                        pypi_data = await pypi_response.json()
                                        try:
                                            functions.get_pypi_repo(pypi_data)
                                            top_100_cff[purl] = {
                                                'Repository': repo_url,
                                                'Stars': stars,
                                                'Ecosystem': most_downloaded_cff.get('ecosystem', ''),
                                                'Name': name,
                                            }
                                        except ValueError:
                                            top_100_cff[purl] = {
                                                'Repository': repo_url,
                                                'Stars': stars,
                                                'Ecosystem': None,
                                                'Name': None,
                                            }

                            elif most_downloaded_cff.get('ecosystem', '') == 'cran':
                                async with aiohttp.ClientSession() as cran_session:
                                    async with cran_session.get(f"https://crandb.r-pkg.org/{name}") as cran_response:
                                        cran_data = await cran_response.json()
                                        try:
                                            functions.get_cran_repo(cran_data)
                                            top_100_cff[purl] = {
                                                'Repository': repo_url,
                                                'Stars': stars,
                                                'Ecosystem': most_downloaded_cff.get('ecosystem', ''),
                                                'Name': name,
                                            }
                                        except ValueError:
                                            top_100_cff[purl] = {
                                                'Repository': repo_url,
                                                'Stars': stars,
                                                'Ecosystem': None,
                                                'Name': None,
                                            }

                            else:
                                top_100_cff[purl] = {
                                    'Repository': repo_url,
                                    'Stars': stars,
                                    'Ecosystem': None,
                                    'Name': None,
                                }
                        cff_bar.update(1)
                else:
                    print(f"Error fetching {repo_url}: {ecosystems_response.status_code}")

        pd.DataFrame.from_dict(top_100_cff, orient='index').to_csv('top_100_cff.csv', index=False)
        pd.DataFrame.from_dict(top_100_cran_cff, orient='index').to_csv('top_100_cran_cff.csv', index=False)
        pd.DataFrame.from_dict(top_100_pypi_cff, orient='index').to_csv('top_100_pypi_cff.csv', index=False)

        cff_bar.refresh()
        cran_bar.refresh()
        pypi_bar.refresh()

if __name__ == "__main__":
    asyncio.run(main())
