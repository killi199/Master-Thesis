import re
from datetime import datetime
import pandas as pd
from git import GitCommandError, Repo
import subprocess
import yaml
import bibtexparser
import bibtexparser.middlewares as m
from pathlib import Path
from xmlrpc.client import ServerProxy
import aiohttp
from bs4 import BeautifulSoup
import rpy2
import asyncio
import concurrent.futures
from pytz import utc
import rpy2.robjects as ro
from rpy2.rinterface_lib._rinterface_capi import RParsingError
from thefuzz import fuzz


def matching(df: pd.DataFrame, git_contributors_df: pd.DataFrame) -> pd.DataFrame:
    rank = []
    insertions = []
    deletions = []
    lines_changed = []
    files = []
    commits = []
    first_commit = []
    last_commit = []
    scores = []
    matching_columns = 0
    if 'name' in df.columns:
        matching_columns += 1
    if 'email' in df.columns:
        matching_columns += 1
    if 'login' in df.columns:
        matching_columns += 1
    
    for _, author in df.iterrows():
        dic = []
        for contributor_index, contributor in git_contributors_df.iterrows():
            counter = 0
            name_match = False
            if 'name' in df.columns and author["name"] is not None and contributor["name"] is not None and (author["name"].lower() in contributor["name"].lower() or contributor["name"].lower() in author["name"].lower() or fuzz.ratio(author["name"].lower(), contributor["name"].lower()) >= 80):
                counter += 1
                name_match = True
            if 'email' in df.columns and author["email"] is not None and contributor["email"] is not None and (author["email"].lower() in contributor["email"].lower() or contributor["email"].lower() in author["email"].lower() or fuzz.ratio(author["email"].lower(), contributor["email"].lower()) >= 80 or (not name_match and (author["email"].lower() in contributor["name"].lower() or contributor["name"].lower() in author["email"].lower() or fuzz.ratio(author["email"].lower(), contributor["name"].lower()) >= 80))):
                counter += 1
            if 'login' in df.columns and author["login"] is not None and contributor["email"] is not None:
                contributor_email_edited = contributor['email'].split('@')[0].lower()
                if author["login"].lower() in contributor_email_edited or contributor_email_edited in author["login"].lower() or fuzz.ratio(author["login"].lower(), contributor_email_edited) >= 80:
                    counter += 1

            if counter > 0:
                dic.append({
                    "index": contributor_index,
                    "score": counter / matching_columns
                })

        test = max(dic, key=lambda x: x["score"], default=None)
        if test is not None:
            rank.append(test["index"] + 1)
            insertions.append(git_contributors_df.loc[test["index"]]["insertions"])
            deletions.append(git_contributors_df.loc[test["index"]]["deletions"])
            lines_changed.append(git_contributors_df.loc[test["index"]]["lines_changed"])
            files.append(git_contributors_df.loc[test["index"]]["files"])
            commits.append(git_contributors_df.loc[test["index"]]["commits"])
            first_commit.append(git_contributors_df.loc[test["index"]]["first_commit"])
            last_commit.append(git_contributors_df.loc[test["index"]]["last_commit"])
            scores.append(test["score"])
        else:
            rank.append(None)
            insertions.append(None)
            deletions.append(None)
            lines_changed.append(None)
            files.append(None)
            commits.append(None)
            first_commit.append(None)
            last_commit.append(None)
            scores.append(0)

    df["rank"] = rank
    df["insertions"] = insertions
    df["deletions"] = deletions
    df["lines_changed"] = lines_changed
    df["files"] = files
    df["commits"] = commits
    df["first_commit"] = first_commit
    df["last_commit"] = last_commit
    df["score"] = scores
    return df.sort_values(by=['commits'], ascending=False)

def parse_contribution_stats(data: str, package_name: str) -> list:
    author_pattern = re.compile(
        r"\s*(.+) <(.+)>:\s*"
        r"insertions:\s*(\d+)\s*\((\d+)%\)\s*"
        r"deletions:\s*(\d+)\s*\((\d+)%\)\s*"
        r"files:\s*(\d+)\s*\((\d+)%\)\s*"
        r"commits:\s*(\d+)\s*\((\d+)%\)\s*"
        r"lines changed:\s*(\d+)\s*\((\d+)%\)\s*"
        r"first commit:\s*(.+)\s*"
        r"last commit:\s*(.+)\s*"
    )

    authors = []
    for match in author_pattern.finditer(data):
        (name, email, insertions, insertions_pct, deletions, deletions_pct, files, files_pct,
         commits, commits_pct, lines_changed, lines_changed_pct, first_commit, last_commit) = match.groups()

        try:
            first_commit_parsed = datetime.strptime(first_commit, '%a %b %d %H:%M:%S %Y %z')
        except ValueError:
            first_commit_parsed = utc.localize(datetime.min)
            print(f'Error parsing author: {name} in {package_name}')

        try:
            last_commit_parsed = datetime.strptime(last_commit, '%a %b %d %H:%M:%S %Y %z')
        except ValueError:
            last_commit_parsed = utc.localize(datetime.max)
            print(f'Error parsing author: {name} in {package_name}')

        authors.append({
            'name': name,
            'email': email,
            'insertions': int(insertions),
            'deletions': int(deletions),
            'files': int(files),
            'commits': int(commits),
            'first_commit': first_commit_parsed,
            'last_commit': last_commit_parsed,
            'lines_changed': int(lines_changed),
        })

    return authors

async def run_git_quick_stat(repo_path: Path) -> str:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        # Doppelte Leute, da unterschiedliche Namen beim commit angegeben → Das Problem besteht beim Benutzen der GitHub API nicht. → Teilweise gelöst mittels group auf E-Mail
        result = await loop.run_in_executor(
            pool,
            lambda: subprocess.run(['git', 'quick-stats', '-T'], capture_output=True, encoding='utf-8',
                                   cwd=str(repo_path))
        )
    return result.stdout

async def get_git_contributors(owner: str, repo: str, repo_link: str, package_name: str) -> pd.DataFrame:
    try:
        Repo.clone_from(repo_link, f'./repos/{owner}/{repo}')
    except GitCommandError as ex:
        if not "already exists and is not an empty directory" in str(ex):
            print(f"Error cloning {repo_link}: {ex}")
        pass

    # Stark unterschiedliche Anzahl der commits abhängig vom Programm
    data = await run_git_quick_stat(Path(f'./repos/{owner}/{repo}'))

    # Parse the data
    authors_data = parse_contribution_stats(data, package_name)

    # Convert authors data to DataFrame
    git_contributors_df = pd.DataFrame(authors_data)
    git_contributors_df['email'] = git_contributors_df['email'].str.lower()
    git_contributors_df = git_contributors_df.groupby(['email']).agg({'name':'sum', 'insertions':'sum', 'deletions':'sum', 'lines_changed':'sum', 'files':'sum', 'commits':'sum', 'first_commit':'min', 'last_commit':'max'}).reset_index()
    git_contributors_df = git_contributors_df.sort_values(by=['commits'], ascending=False)
    git_contributors_df = git_contributors_df.reset_index(drop=True)
    git_contributors_df = git_contributors_df[['name', 'email', 'insertions', 'deletions', 'lines_changed', 'files', 'commits', 'first_commit', 'last_commit']]

    return git_contributors_df

def get_cff_list(authors) -> list[dict[str, str]]:
    authors_dic: list[dict[str, str]] = list()
    for author in authors:
        if "orcid" not in author:
            author["orcid"] = None
        if "email" not in author:
            author["email"] = None

        if "given-names" in author and "family-names" in author:
            authors_dic.append({"name": author["given-names"] + " " + author["family-names"]})
        elif "family-names" in author:
            authors_dic.append({"name": author["family-names"]})
        elif "given-names" in author:
            authors_dic.append({"name": author["given-names"]})
        elif "name" in author:
            authors_dic.append({"name": author["name"]})

        authors_dic[-1]["email"] = author["email"]
        authors_dic[-1]["ORCID"] = author["orcid"]

    return authors_dic

def load_cff_authors_from_path(path: str, key: str) -> pd.DataFrame:
    """Helper function to load authors from a CITATION.cff file."""
    try:
        with open(path, 'r') as file:
            cff = yaml.safe_load(file)
        authors = cff
        for k in key.split('.'):
            authors = authors[k]
        return pd.DataFrame(get_cff_list(authors))
    except (FileNotFoundError, KeyError):
        return pd.DataFrame()

def get_cff_authors(owner: str, repo: str) -> pd.DataFrame:
    path = f'./repos/{owner}/{repo}/CITATION.cff'
    return load_cff_authors_from_path(path, 'authors')

def get_cff_preferred_citation_authors(owner: str, repo: str) -> pd.DataFrame:
    path = f'./repos/{owner}/{repo}/CITATION.cff'
    return load_cff_authors_from_path(path, 'preferred-citation.authors')

def get_bib_authors(owner: str, repo: str) -> pd.DataFrame:
    file = Path(f'./repos/{owner}/{repo}/CITATION.bib')
    if file.is_file():
        authors: list = list()
        layers = [m.NormalizeFieldKeys(), m.SeparateCoAuthors(), m.SplitNameParts()]
        library = bibtexparser.parse_file(f'./repos/{owner}/{repo}/CITATION.bib', append_middleware=layers)
        entries = library.entries[0]['author']

        if entries is not None:
            for entry in entries:
                authors.append(' '.join(entry.first) + " " + ' '.join(entry.last))
        return pd.DataFrame(authors, columns=['name'])
    else:
        return pd.DataFrame()
    
async def get_pypi_maintainers(package_name: str) -> pd.DataFrame:
    pypi_maintainers = ServerProxy("https://pypi.org/pypi").package_roles(package_name)
    pypi_maintainers_names = []
    assert isinstance(pypi_maintainers, list)
    for maintainer in pypi_maintainers:
        assert isinstance(maintainer, list)
        user_name = maintainer[1]
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://pypi.org/user/{user_name}/') as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, features="html.parser")
                    h1 = soup.find_all("h1", {"class": "author-profile__name"})
                    if h1:
                        name = h1[0].string
                        pypi_maintainers_names.append([user_name, name])
                    else:
                        pypi_maintainers_names.append([user_name, None])

    return pd.DataFrame(pypi_maintainers_names, columns=['login', 'name'])

def extract_names_and_emails(data: dict, name_key: str, email_key: str) -> pd.DataFrame:
    """Helper function to extract and combine names and emails from PyPI data."""
    names = data.get(name_key, "")
    emails = data.get(email_key, "")

    name_list = names.split(", ") if names else []
    email_list = emails.split(", ") if emails else []

    return combine_name_email(name_list, email_list)

def get_python_authors(pypi_data) -> pd.DataFrame:
    """Extract authors from PyPI data."""
    return extract_names_and_emails(pypi_data["info"], "author", "author_email")

def get_python_maintainers(pypi_data) -> pd.DataFrame:
    """Extract maintainers from PyPI data."""
    return extract_names_and_emails(pypi_data["info"], "maintainer", "maintainer_email")

def get_cran_authors(cran_data) -> pd.DataFrame:
    cran_author = cran_data.get("Authors@R")

    if cran_author is None:
        return get_cran_author(cran_data)
    
    try:
        authors = ro.r(f'''eval(parse(text = '{cran_author}'))''')
    except RParsingError:
        return get_cran_author(cran_data)

    cran_authors_df = pd.DataFrame(columns=["name", "email", "ORCID"])

    for author in authors:
        if "aut" in author[2]:
            if type(author[0]) == rpy2.rinterface_lib.sexp.NULLType and type(author[1]) == rpy2.rinterface_lib.sexp.NULLType:
                name = None
            elif type(author[0]) == rpy2.rinterface_lib.sexp.NULLType:
                name = author[1][0]
            elif type(author[1]) == rpy2.rinterface_lib.sexp.NULLType:
                name = author[0][0]
            else:
                name = f"{author[0][0]} {author[1][0]}"
            
            
            if type(author[3]) == rpy2.rinterface_lib.sexp.NULLType:
                email = None
            else:
                email = author[3][0]

            if type(author[4]) == rpy2.rinterface_lib.sexp.NULLType:
                orcid = None
            else:
                orcid = author[4][0]

            cran_authors_df = pd.concat([cran_authors_df, pd.DataFrame({"name": name, "email": email, "ORCID": orcid}, index=[0])], ignore_index=True)

    return cran_authors_df

def get_cran_author(cran_data) -> pd.DataFrame:
    cran_author = cran_data["Author"]

    orcid_pattern = re.compile(r'\s*\(<https://orcid.org/[^>]+>\)')

    cran_author = re.sub(orcid_pattern, '', cran_author)

    pattern = re.compile(r"(?P<name>[^,\[\]]+)(?:\s*\[(?P<roles>[^\]]*)\])?\s*(?:,\s*ORCID:\s*(?P<orcid>[^\s,]+))?")

    # List to hold parsed data
    parsed_data = []

    # Find all matches in the data string
    for match in pattern.finditer(cran_author):
        name = match.group('name').strip()
        roles = match.group('roles')

        if roles is not None:
            if "aut" in roles:
                parsed_data.append({
                    'name': name,
                })

    return pd.DataFrame(parsed_data)

def get_cran_maintainers(cran_data) -> pd.DataFrame:
    cran_maintainer = cran_data["Maintainer"]

    match = re.match(r"^(.*?)\s*<(.+)>$", cran_maintainer)
    if match:
        name = match.group(1)
        email = match.group(2)
    else:
        name = None
        email = None

    data = {'name': [name], 'email': [email]}

    return pd.DataFrame(data)

def get_pypi_repo(pypi_data) -> tuple[str, str, str]:
    repo_link = None

    for url in pypi_data["info"]["project_urls"].values():
        if "github.com" in url:
            repo_link = url

    if repo_link is None:
        raise ValueError(f"No GitHub repository found in PyPI data.")

    owner = repo_link.split("/")[3]
    repo = repo_link.split("/")[4]
    repo_link = repo_link.split("/")[:5]
    repo_link = '/'.join(str(x) for x in repo_link)
    return owner, repo, repo_link

def get_cran_repo(cran_data) -> tuple[str, str, str]:
    url = cran_data.get("URL")

    if not url:
        raise ValueError(f"No GitHub repository found in CRAN data.")

    urls = [x.strip() for x in url.split(',')]

    repo_link = [url for url in urls if "github.com" in url]
    if not repo_link:
        raise ValueError(f"No GitHub repository found in CRAN data.")
    
    repo_link = repo_link[0]
    repo_link = repo_link.split("#")[0]
    owner = repo_link.split("/")[3]
    repo = repo_link.split("/")[4]
    repo_link = repo_link.split("/")[:5]
    repo_link = '/'.join(str(x) for x in repo_link)

    return owner, repo, repo_link

def combine_name_email(names: list[str], emails: list[str]) -> pd.DataFrame:
    dic = []

    if len(names) >= len(emails):
        i = 0
        while i < len(names):
            if i >= len(emails):
                dic.append({
                    "name": names[i],
                    "email": None
                })
            else:
                dic.append({
                    "name": names[i],
                    "email": emails[i]
                })
            i += 1
    else:
        i = 0
        while i < len(emails):
            if i >= len(names):
                dic.append({
                    "name": None,
                    "email": emails[i]
                })
            else:
                dic.append({
                    "name": names[i],
                    "email": emails[i]
                })
            i += 1

    return pd.DataFrame(dic)
