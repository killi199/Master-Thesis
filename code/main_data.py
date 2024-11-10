import traceback
from datetime import datetime
from pathlib import Path
from queue import Queue

import aiohttp
import pandas as pd
import functions
import asyncio
import json
from tqdm import tqdm

bar_queue = Queue()

async def process_and_save(dataframe: pd.DataFrame, package_name: str, filename: str, index: str):
    if not dataframe.empty:
        dataframe.to_csv(f'results/{index}/{package_name}/{filename}.csv', index=False, mode='w')

async def process_general_package(owner: str, repo: str, package_name: str, index: str, position: int, git_contributors_df_new: pd.DataFrame):
    cff_authors_df, cff_df = functions.get_cff_data(owner, repo)
    for cff_author_df in cff_authors_df:
        if not cff_author_df[0].empty:
            git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, cff_author_df[1])
            await process_and_save(git_contributors_df, package_name,
                                   cff_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_git_contributors', index)
            result = functions.matching(cff_author_df[0], git_contributors_df)
            result_new = functions.matching(cff_author_df[0], git_contributors_df_new)
            await process_and_save(result, package_name, cff_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_authors', index)
            await process_and_save(result_new, package_name, cff_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_authors_new', index)
    await process_and_save(cff_df, package_name, 'cff', index)

    cff_preferred_authors_df, cff_preferred_df = functions.get_cff_preferred_citation_data(owner, repo)
    for cff_preferred_author_df in cff_preferred_authors_df:
        if not cff_preferred_author_df[0].empty:
            git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, cff_preferred_author_df[1])
            await process_and_save(git_contributors_df, package_name,
                                   cff_preferred_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_git_contributors', index)
            result = functions.matching(cff_preferred_author_df[0], git_contributors_df)
            result_new = functions.matching(cff_preferred_author_df[0], git_contributors_df_new)
            await process_and_save(result, package_name, cff_preferred_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_preferred_citation_authors', index)
            await process_and_save(result_new, package_name, cff_preferred_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_preferred_citation_authors_new', index)
        await process_and_save(cff_preferred_df, package_name, 'cff_preferred_citation', index)

    bib_authors_df, bib_df = functions.get_bib_data(owner, repo)
    for bib_author_df in bib_authors_df:
        if not bib_author_df[0].empty:
            git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, bib_author_df[1])
            await process_and_save(git_contributors_df, package_name,
                                   bib_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_git_contributors', index)
            result = functions.matching(bib_author_df[0], git_contributors_df)
            result_new = functions.matching(bib_author_df[0], git_contributors_df_new)
            await process_and_save(result, package_name, bib_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_bib_authors', index)
            await process_and_save(result_new, package_name, bib_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_bib_authors_new', index)
    await process_and_save(bib_df, package_name, 'bib', index)

    readme_authors_df, readme_df = await asyncio.to_thread(functions.get_readme_authors, owner, repo, position)
    for readme_author_df in tqdm(readme_authors_df, desc=f'{repo} README Git', position=position, dynamic_ncols=True):
        if not readme_author_df[0].empty:
            git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, readme_author_df[1])
            await process_and_save(git_contributors_df, package_name,
                                   readme_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_git_contributors', index)
            result = functions.matching(readme_author_df[0], git_contributors_df)
            result_new = functions.matching(readme_author_df[0], git_contributors_df_new)
            await process_and_save(result, package_name, readme_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_readme_authors', index)
            await process_and_save(result_new, package_name, readme_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_readme_authors_new', index)
    await process_and_save(readme_df, package_name, 'readme', index)

async def process_pypi_package(package, semaphore: asyncio.Semaphore, url: str, index: str, position: int):
    package_name = package.strip()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pypi.org/pypi/{package_name}/json") as response:
                pypi_data = await response.json()

        if not url:
            owner, repo, repo_link = functions.get_pypi_repo(pypi_data)
        else:
            repo_link = url
            owner = repo_link.split('/')[-2]
            repo = repo_link.split('/')[-1]

        Path(f'results/{index}/{package_name}').mkdir(parents=True, exist_ok=True)

        functions.clone_git_repo(owner, repo, repo_link)
        git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, datetime.now())
        await process_and_save(git_contributors_df, package_name, 'git_contributors', index)

        async with semaphore:
            pypi_maintainers_df = await functions.get_pypi_maintainers(package_name)
            result = functions.matching(pypi_maintainers_df, git_contributors_df)
            await process_and_save(result, package_name, 'pypi_maintainers', index)

        python_authors_df = functions.get_python_authors(pypi_data)
        result = functions.matching(python_authors_df, git_contributors_df)
        await process_and_save(result, package_name, 'python_authors', index)

        python_maintainers_df = functions.get_python_maintainers(pypi_data)
        result = functions.matching(python_maintainers_df, git_contributors_df)
        await process_and_save(result, package_name, 'python_maintainers', index)

        description = pypi_data['info']['description']
        description_df = functions.get_description_authors(description)
        result = functions.matching(description_df, git_contributors_df)
        await process_and_save(result, package_name, 'description_authors', index)

        await process_general_package(owner, repo, package_name, index, position, git_contributors_df)
    except ValueError as e:
        print(f"Error processing {package_name}: {e}")
    except Exception:
        print(f"Error processing {package_name}: {traceback.format_exc()}")

async def process_cran_package(package, _: asyncio.Semaphore, url: str, index: str, position: int):
    package_name = package.strip()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://crandb.r-pkg.org/{package_name}") as response:
                cran_data = await response.json()

        if not url:
            owner, repo, repo_link = functions.get_cran_repo(cran_data)
        else:
            repo_link = url
            owner = repo_link.split('/')[-2]
            repo = repo_link.split('/')[-1]

        Path(f'results/{index}/{package_name}').mkdir(parents=True, exist_ok=True)

        functions.clone_git_repo(owner, repo, repo_link)
        git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, datetime.now())
        await process_and_save(git_contributors_df, package_name, 'git_contributors', index)

        cran_authors_df = functions.get_cran_authors(cran_data)
        result = functions.matching(cran_authors_df, git_contributors_df)
        await process_and_save(result, package_name, 'cran_authors', index)

        cran_maintainers_df = functions.get_cran_maintainers(cran_data)
        result = functions.matching(cran_maintainers_df, git_contributors_df)
        await process_and_save(result, package_name, 'cran_maintainers', index)

        description = cran_data['Description']
        description_df = functions.get_description_authors(description)
        result = functions.matching(description_df, git_contributors_df)
        await process_and_save(result, package_name, 'description_authors', index)

        await process_general_package(owner, repo, package_name, index, position, git_contributors_df)
    except ValueError as e:
        print(f"Error processing {package_name}: {e}")
    except Exception:
        print(f"Error processing {package_name}: {traceback.format_exc()}")

async def process_cff_package(package, semaphore: asyncio.Semaphore, _: str, index: str, bar_id: int):
    if package['Ecosystem'] == 'pypi':
        await process_pypi_package(package['Name'], semaphore, package['Repository'], index, bar_id)
    if package['Ecosystem'] == 'cran':
        await process_cran_package(package['Name'], semaphore, package['Repository'], index, bar_id)

async def process_package_semaphore(package_name, semaphore: asyncio.Semaphore, function, pypi_api_semaphore, url: str, index: str):
    async with semaphore:
        bar_id = bar_queue.get()
        await function(package_name, pypi_api_semaphore, url, index, bar_id)
        bar_queue.put(bar_id)

async def main():
    # https://hugovk.github.io/top-pypi-packages/
    with open('top-pypi-packages-30-days.min.json', 'r') as file:
        packages = file.readlines()
        json_object = json.loads(packages[0])
        pypi_rows = json_object['rows'][:100]

    # https://cranlogs.r-pkg.org/top/last-month/100
    with open('top-cran-packages-30-days.min.json', 'r') as file:
        packages = file.readlines()
        json_object = json.loads(packages[0])
        cran_rows = json_object['downloads'][:100]

    cff_df = pd.read_csv('github_repo_stars_sorted_100.csv')
    semaphore_count = 5
    semaphore = asyncio.Semaphore(semaphore_count)
    pypi_api_semaphore = asyncio.Semaphore(1)

    for i in range(1, semaphore_count + 1):
        bar_queue.put(i)

    pypi_tasks = [process_package_semaphore(package['project'], semaphore, process_pypi_package, pypi_api_semaphore, '', 'pypi') for package in pypi_rows]
    cran_tasks = [process_package_semaphore(package['package'], semaphore, process_cran_package, pypi_api_semaphore, '', 'cran') for package in cran_rows]
    cff_tasks = [process_package_semaphore(package, semaphore, process_cff_package, pypi_api_semaphore, '', 'cff') for _, package in cff_df.iterrows()]

    for task in tqdm(asyncio.as_completed(pypi_tasks), total=len(pypi_tasks), desc='PyPI', position=0, dynamic_ncols=True, smoothing=0):
        await task

    for task in tqdm(asyncio.as_completed(cran_tasks), total=len(cran_tasks), desc='CRAN', position=0, dynamic_ncols=True, smoothing=0):
        await task

    for task in tqdm(asyncio.as_completed(cff_tasks), total=len(cff_tasks), desc='CFF', position=0, dynamic_ncols=True, smoothing=0):
        await task

if __name__ == "__main__":
    asyncio.run(main())
