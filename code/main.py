import aiohttp
import functions
import asyncio
import os
import json
from tqdm import tqdm

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

        async def process_and_save(dataframe, filename):
            result = functions.matching(dataframe, git_contributors_df)
            if not result.empty:
                result.to_csv(f'results/pypi/{package_name}/{filename}.csv', index=False)

        # currently not fully accessible through the API -> limiting factor HTTP is limited if this is not used more semaphores possible
        pypi_maintainers_df = await functions.get_pypi_maintainers(package_name)
        await process_and_save(pypi_maintainers_df, 'pypi_maintainers')

        python_authors_df = functions.get_python_authors(pypi_data)
        await process_and_save(python_authors_df, 'python_authors')

        python_maintainers_df = functions.get_python_maintainers(pypi_data)
        await process_and_save(python_maintainers_df, 'python_maintainers')

        cff_df = functions.get_cff_authors(owner, repo)
        await process_and_save(cff_df, 'cff_authors')

        cff_preferred_df = functions.get_cff_preferred_citation_authors(owner, repo)
        await process_and_save(cff_preferred_df, 'cff_preferred_citation_authors')

        bib_df = functions.get_bib_authors(owner, repo)
        await process_and_save(bib_df, 'bib_authors')
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
        rows = json_object['rows'][:100]

    semaphore = asyncio.Semaphore(2)

    tasks = [process_package_semaphore(package['project'], semaphore, process_pypi_package) for package in rows]

    for task in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        await task

if __name__ == "__main__":
    asyncio.run(main())
