import aiohttp
import pandas as pd

import functions
import asyncio
import os
import json
from tqdm import tqdm


async def process_and_save(dataframe: pd.DataFrame, git_contributors_df: pd.DataFrame, package_name: str, filename: str, index: str):
    result = functions.matching(dataframe, git_contributors_df)
    if not result.empty:
        result.to_csv(f'results/{index}/{package_name}/{filename}.csv', index=False)

async def process_general_package(owner: str, repo: str, git_contributors_df, package_name: str, index: str):
    cff_df = functions.get_cff_authors(owner, repo)
    await process_and_save(cff_df, git_contributors_df, package_name, 'cff_authors', index)

    cff_preferred_df = functions.get_cff_preferred_citation_authors(owner, repo)
    await process_and_save(cff_preferred_df, git_contributors_df, package_name, 'cff_preferred_citation_authors', index)

    bib_df = functions.get_bib_authors(owner, repo)
    await process_and_save(bib_df, git_contributors_df, package_name, 'bib_authors', index)

    readme_df = functions.get_readme_authors(owner, repo)
    await process_and_save(readme_df, git_contributors_df, package_name, 'readme_authors', index)

async def process_pypi_package(package):
    package_name = package.strip()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://pypi.org/pypi/{package_name}/json") as response:
                pypi_data = await response.json()

        owner, repo, repo_link = functions.get_pypi_repo(pypi_data)

        os.mkdir(f'results/pypi/{package_name}')

        git_contributors_df = await functions.get_git_contributors(owner, repo, repo_link, package_name)
        git_contributors_df.to_csv(f'results/pypi/{package_name}/git_contributors.csv', index=False)

        # currently not fully accessible through the API -> limiting factor HTTP is limited if this is not used more semaphores possible
        pypi_maintainers_df = await functions.get_pypi_maintainers(package_name)
        await process_and_save(pypi_maintainers_df, git_contributors_df, package_name, 'pypi_maintainers', 'pypi')

        python_authors_df = functions.get_python_authors(pypi_data)
        await process_and_save(python_authors_df, git_contributors_df, package_name, 'python_authors', 'pypi')

        python_maintainers_df = functions.get_python_maintainers(pypi_data)
        await process_and_save(python_maintainers_df, git_contributors_df, package_name, 'python_maintainers', 'pypi')

        description = pypi_data['info']['description']
        description_df = functions.get_description_authors(description)
        await process_and_save(description_df, git_contributors_df, package_name, 'description_authors', 'pypi')

        await process_general_package(owner, repo, git_contributors_df, package_name, 'pypi')
    except Exception as e:
        print(f"Error processing {package_name}: {e}")

async def process_cran_package(package):
    package_name = package.strip()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://crandb.r-pkg.org/{package_name}") as response:
                cran_data = await response.json()

        owner, repo, repo_link = functions.get_cran_repo(cran_data)

        os.mkdir(f'results/cran/{package_name}')

        git_contributors_df = await functions.get_git_contributors(owner, repo, repo_link, package_name)
        git_contributors_df.to_csv(f'results/cran/{package_name}/git_contributors.csv', index=False)

        cran_authors_df = functions.get_cran_authors(cran_data)
        await process_and_save(cran_authors_df, git_contributors_df, package_name, 'cran_authors', 'cran')

        cran_maintainers_df = functions.get_cran_maintainers(cran_data)
        await process_and_save(cran_maintainers_df, git_contributors_df, package_name, 'cran_maintainers', 'cran')

        description = cran_data['Description']
        description_df = functions.get_description_authors(description)
        await process_and_save(description_df, git_contributors_df, package_name, 'description_authors', 'cran')

        await process_general_package(owner, repo, git_contributors_df, package_name, 'cran')
    except Exception as e:
        print(f"Error processing {package_name}: {e}")

async def process_package_semaphore(package_name: str, semaphore: asyncio.Semaphore, function):
    async with semaphore:
        await function(package_name)

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

    pypi_semaphore = asyncio.Semaphore(2)
    cran_semaphore = asyncio.Semaphore(10)

    pypi_tasks = [process_package_semaphore(package['project'], pypi_semaphore, process_pypi_package) for package in pypi_rows]
    cran_tasks = [process_package_semaphore(package['package'], cran_semaphore, process_cran_package) for package in cran_rows]

    for task in tqdm(asyncio.as_completed(pypi_tasks), total=len(pypi_tasks)):
        await task

    for task in tqdm(asyncio.as_completed(cran_tasks), total=len(cran_tasks)):
        await task

if __name__ == "__main__":
    asyncio.run(main())
