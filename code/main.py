import requests
import functions
import asyncio
import os
import json
from tqdm import tqdm

async def process_package(package):
    package_name = package.strip()
    response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
    pypi_data = response.json()

    owner, repo, repo_link = functions.get_pypi_repo(pypi_data)

    os.mkdir(f'results/{package_name}')

    git_contributors_df = functions.get_git_contributors(owner, repo, repo_link)
    git_contributors_df.to_csv(f'results/{package_name}/git_contributors.csv', index=False)

    pypi_maintainers_df = await functions.get_pypi_maintainers(package_name)
    result = functions.matching(pypi_maintainers_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/pypi_maintainers.csv', index=False)

    python_authors_df = functions.get_python_authors(pypi_data)
    result = functions.matching(python_authors_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/python_authors.csv', index=False)

    python_maintainers_df = functions.get_python_maintainers(pypi_data)
    result = functions.matching(python_maintainers_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/python_maintainers.csv', index=False)

    cff_df = functions.get_cff_authors(owner, repo)
    result = functions.matching(cff_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/cff_authors.csv', index=False)

    cff_df = functions.get_cff_preferred_citation_authors(owner, repo)
    result = functions.matching(cff_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/cff_preferred_citation_authors.csv', index=False)

    bib_df = functions.get_bib_authors(owner, repo)
    result = functions.matching(bib_df, git_contributors_df)
    if not result.empty: result.to_csv(f'results/{package_name}/bib_authors.csv', index=False)

async def main():
    # https://hugovk.github.io/top-pypi-packages/
    with open('top-pypi-packages-30-days.min.json', 'r') as file:
        packages = file.readlines()
        json_object = json.loads(packages[0])
        rows = json_object['rows']
        rows = rows[:100]
        for package in tqdm(rows):
            try:
                await process_package(package['project'])
            except Exception as e:
                print(f"Error processing {package['project']}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
