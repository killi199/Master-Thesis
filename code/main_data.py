import shutil
import traceback
from datetime import datetime
from pathlib import Path
from queue import Queue
import pandas as pd
import functions
import asyncio
from tqdm import tqdm

bar_queue = Queue()

async def process_and_save(dataframe: pd.DataFrame, package_name: str, filename: str, index: str):
    if not dataframe.empty:
        dataframe.to_csv(f'results/{index}/{package_name}/{filename}.csv', index=False, mode='w')

async def process_general_package(owner: str, repo: str, package_name: str, index: str, git_contributors_df_new: pd.DataFrame):
    cff_authors_df, cff_df = functions.get_cff_data(owner, repo)
    for cff_author_df in cff_authors_df:
        if not cff_author_df[0].empty:
            result_new = functions.matching(cff_author_df[0], git_contributors_df_new)
            await process_and_save(result_new, package_name, cff_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_authors_new', index)
    await process_and_save(cff_df, package_name, 'cff', index)

    cff_preferred_authors_df, cff_preferred_df = functions.get_cff_preferred_citation_data(owner, repo)
    for cff_preferred_author_df in cff_preferred_authors_df:
        if not cff_preferred_author_df[0].empty:
            result_new = functions.matching(cff_preferred_author_df[0], git_contributors_df_new)
            await process_and_save(result_new, package_name, cff_preferred_author_df[1].strftime("%Y%m%d_%H%M%S%z") + '_cff_preferred_citation_authors_new', index)
        await process_and_save(cff_preferred_df, package_name, 'cff_preferred_citation', index)

async def process_cff_package(url: str, index):
    package_name = ''
    try:
        repo_link = url
        owner = repo_link.split('/')[-2]
        repo = repo_link.split('/')[-1]
        package_name = f'{owner}_{repo}'

        Path(f'./results/{index}/{package_name}').mkdir(parents=True, exist_ok=True)

        functions.clone_git_repo(owner, repo, repo_link)
        git_contributors_df = await functions.get_git_contributors(owner, repo, package_name, datetime.now())
        await process_and_save(git_contributors_df, package_name, 'git_contributors', index)
        await process_general_package(owner, repo, package_name, index, git_contributors_df)
        shutil.rmtree(f'./repos/{owner}/{repo}')
    except ValueError as e:
        print(f"Error processing {package_name}: {e}")
    except Exception:
        print(f"Error processing {package_name}: {traceback.format_exc()}")

async def process_package_semaphore(semaphore: asyncio.Semaphore, function, url: str, index: str):
    async with semaphore:
        await function(url, index)

async def main():
    cff_df = pd.read_csv('github_repo_stars.csv')
    semaphore_count = 1
    semaphore = asyncio.Semaphore(semaphore_count)

    cff_tasks = [process_package_semaphore(semaphore, process_cff_package,  package['Repository'], 'cff_full') for _, package in cff_df.iterrows()]

    for task in tqdm(asyncio.as_completed(cff_tasks), total=len(cff_tasks), desc='CFF', position=0, dynamic_ncols=True):
        await task

if __name__ == "__main__":
    asyncio.run(main())
