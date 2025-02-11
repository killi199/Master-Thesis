import contextlib
import glob
import os
import re
from datetime import datetime, timedelta, timezone
import cffconvert.cli
import cffconvert.cli.create_citation
import cffconvert.cli.read_from_file
import cffconvert.cli.validate_or_write_output
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
from ruamel.yaml.composer import ComposerError
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError
from thefuzz import fuzz
import spacy
import warnings
from cffconvert import Citation
from jsonschema.exceptions import ValidationError as JsonschemaSchemaError
from pykwalify.errors import SchemaError as PykwalifySchemaError
from tqdm import tqdm
import sys

warnings.filterwarnings("ignore", category=FutureWarning)

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

            if 'name' in df.columns and author["name"] is not None and contributor["name"] is not None:
                contributor_without_brackets = re.sub(r'\(.*?\)', '', contributor["name"].lower()).strip()
                contributor_without_brackets = re.sub(' +', ' ', contributor_without_brackets)
                if (author["name"].lower() in contributor["name"].lower() or contributor["name"].lower() in author["name"].lower() or
                        fuzz.ratio(author["name"].lower(), contributor["name"].lower()) >= 80 or
                        author["name"].lower() in contributor_without_brackets or contributor_without_brackets in author["name"].lower() or
                        fuzz.ratio(author["name"].lower(), contributor_without_brackets) >= 80):
                    counter += 1
                    name_match = True

            if 'email' in df.columns and author["email"] is not None and contributor["email"] is not None:
                if (author["email"].lower() in contributor["email"].lower() or contributor["email"].lower() in author["email"].lower() or
                        fuzz.ratio(author["email"].lower(), contributor["email"].lower()) >= 80 or
                        (not name_match and (
                                author["email"].lower() in contributor["name"].lower() or contributor["name"].lower() in author["email"].lower() or
                                fuzz.ratio(author["email"].lower(), contributor["name"].lower()) >= 80))):
                    counter += 1

            if 'login' in df.columns and author["login"] is not None and contributor["email"] is not None:
                contributor_email_edited_1 = contributor['email'].split('@')[0].lower()

                if len(contributor['email'].split('@')) > 1:
                    contributor_email_edited_2 = contributor['email'].split('@')[1].lower()
                else:
                    contributor_email_edited_2 = contributor['email'].split('@')[0].lower()

                if (author["login"].lower() in contributor_email_edited_1 or contributor_email_edited_1 in author["login"].lower() or
                        fuzz.ratio(author["login"].lower(), contributor_email_edited_1) >= 80 or
                        author["login"].lower() in contributor_email_edited_2 or contributor_email_edited_2 in author["login"].lower() or
                        fuzz.ratio(author["login"].lower(), contributor_email_edited_2) >= 80):
                    counter += 1

            if counter == 0 and 'name' in df.columns and author["name"] is not None and contributor["email"] is not None:
                contributor_email_edited = contributor['email'].split('@')[0].lower()
                if fuzz.ratio(author["name"].lower(), contributor_email_edited) >= 80:
                    counter += 1

            if counter > 0:
                dic.append({
                    "index": contributor_index,
                    "score": counter / matching_columns
                })

        result = max(dic, key=lambda x: x["score"], default=None)
        if result is not None:
            rank.append(result["index"] + 1)
            insertions.append(git_contributors_df.loc[result["index"]]["insertions"])
            deletions.append(git_contributors_df.loc[result["index"]]["deletions"])
            lines_changed.append(git_contributors_df.loc[result["index"]]["lines_changed"])
            files.append(git_contributors_df.loc[result["index"]]["files"])
            commits.append(git_contributors_df.loc[result["index"]]["commits"])
            first_commit.append(git_contributors_df.loc[result["index"]]["first_commit"])
            last_commit.append(git_contributors_df.loc[result["index"]]["last_commit"])
            scores.append(result["score"])
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
    return df.sort_values(by=['rank'], ascending=True)

def parse_contribution_stats(data: str) -> list:
    author_pattern = re.compile(
        r"\s*(.+) <(.+)>:\s*"
        r"insertions:\s*(\d+)\s*\((\d+)%\)\s*"
        r"(?:deletions:\s*(\d+)\s*\((\d+)%\)\s*)?"
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
            first_commit_parsed = datetime.strptime(first_commit[:-7], '%a %b %d %H:%M:%S %Y')
            first_commit_parsed = first_commit_parsed.replace(tzinfo=utc)
            pass

        try:
            last_commit_parsed = datetime.strptime(last_commit, '%a %b %d %H:%M:%S %Y %z')
        except ValueError:
            last_commit_parsed = datetime.strptime(last_commit[:-7], '%a %b %d %H:%M:%S %Y')
            last_commit_parsed = last_commit_parsed.replace(tzinfo=utc)
            pass

        authors.append({
            'name': name,
            'email': email,
            'insertions': int(insertions),
            'deletions': int(0 if deletions is None else deletions),
            'files': int(files),
            'commits': int(commits),
            'first_commit': first_commit_parsed,
            'last_commit': last_commit_parsed,
            'lines_changed': int(lines_changed),
        })

    return authors

async def run_git_quick_stat(repo_path: Path, timestamp: datetime) -> str:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        # Doppelte Leute, da unterschiedliche Namen beim commit angegeben → Das Problem besteht beim Benutzen der GitHub API nicht. → Teilweise gelöst mittels group auf E-Mail
        timestamp = timestamp + timedelta(minutes=1, hours=2)
        time_string = timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
        result = await loop.run_in_executor(
            pool,
            lambda: subprocess.run(['git', 'quick-stats', '-T'], capture_output=True, encoding='utf-8',
                                   cwd=str(repo_path), env={'_GIT_UNTIL':time_string})
        )
    return result.stdout

def clone_git_repo(owner: str, repo: str, repo_link: str):
    try:
        Repo.clone_from(repo_link, f'./repos/{owner}/{repo}')
    except GitCommandError as ex:
        if not "already exists and is not an empty directory" in str(ex):
            print(f"Error cloning {repo_link}: {ex}")
        pass

async def get_git_contributors(owner: str, repo: str, timestamp: datetime) -> pd.DataFrame:
    # Stark unterschiedliche Anzahl der commits abhängig vom Programm
    data = await run_git_quick_stat(Path(f'./repos/{owner}/{repo}'), timestamp)

    # Parse the data
    authors_data = parse_contribution_stats(data)

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
        if "given-names" not in author or "family-names" not in author:
            continue

        if "orcid" not in author:
            author["orcid"] = None
        if "email" not in author:
            author["email"] = None

        if "given-names" in author and "family-names" in author and author["given-names"] and author["family-names"]:
            authors_dic.append({"name": author["given-names"] + " " + author["family-names"]})
        elif "family-names" in author and author["family-names"]:
            authors_dic.append({"name": author["family-names"]})
        elif "given-names" in author and author["given-names"]:
            authors_dic.append({"name": author["given-names"]})

        authors_dic[-1]["email"] = author["email"]
        authors_dic[-1]["ORCID"] = author["orcid"]

    return authors_dic

def load_cff_data(content: str) -> dict:
    try:
        return yaml.safe_load(content)
    except (yaml.YAMLError, ValueError):
        return {}

def load_cff_authors_from_data(cff: dict, key: str) -> pd.DataFrame:
    try:
        authors = cff
        for k in key.split('.'):
            authors = authors[k]
        authors_df = pd.DataFrame(get_cff_list(authors))
        return authors_df
    except KeyError:
        return pd.DataFrame()
    
def get_file_path(owner: str, repo: str, pattern: str) -> str:
    target_dir = os.path.join('./repos/', owner, repo)

    for root, _, _ in os.walk(target_dir):
        full_pattern = os.path.join(root, pattern)
        matched_files = glob.glob(full_pattern)
        
        if matched_files:
            return matched_files[0]

    return ""

def validate_cff(cff_path: str, cff_data: str) -> bool:
    with contextlib.redirect_stderr(open(os.devnull, "w")):
        try:
            citation = Citation(cff_data, src=cff_path)
            citation.validate()
            return True
        except (PykwalifySchemaError, JsonschemaSchemaError, ValueError, DuplicateKeyError, ParserError, ScannerError, ComposerError):
            return False

def cff_init_used(cff_data: str) -> bool:
    return "This CITATION.cff file was generated with cffinit." in cff_data
    
def get_cff_data(owner: str, repo: str) -> tuple[list[tuple[pd.DataFrame, datetime | None]], pd.DataFrame]:
    cff_path = get_file_path(owner, repo, '*CITATION.cff')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*citation.cff')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*CITATION.CFF')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*citation.CFF')

    if cff_path:
        file_data = []
        authors_data: list[tuple[pd.DataFrame, datetime | None]] = list()
        path_parts = cff_path.split('/')
        print_file = '/'.join(path_parts[4:])
        git_repo = Repo(f'./repos/{owner}/{repo}')
        commits_for_file = list(git_repo.iter_commits(all=True, paths=print_file))
        for commit_for_file in commits_for_file:
            try:
                tree = commit_for_file.tree
                blob = tree[print_file]
                cff_string = blob.data_stream.read().decode()
                cff_yaml_data = load_cff_data(cff_string)
                stderr = sys.stderr
                stdout = sys.stdout
                valid = validate_cff(cff_path, cff_string)
                sys.stderr = stderr
                sys.stdout = stdout
                cff_init = cff_init_used(cff_string)

                file_data.append({
                        'cff_valid': valid,
                        'cff_init': cff_init,
                        'type': cff_yaml_data.get('type', 'software'),
                        'date-released': cff_yaml_data.get('date-released', None),
                        'doi': cff_yaml_data.get('doi', None),
                        'identifier-doi': next((item['value'] for item in cff_yaml_data.get('identifiers', []) or [] if item['type'] == 'doi'), None),
                        'committed_datetime': str(commit_for_file.committed_datetime),
                        'authored_datetime': str(commit_for_file.authored_datetime)})
                authors_data.append((load_cff_authors_from_data(cff_yaml_data, 'authors'), commit_for_file.committed_datetime))
            except KeyError:
                pass
            except AttributeError:
                pass
            except UnicodeDecodeError:
                file_data.append({'cff_valid': False})
                pass

        return authors_data, pd.DataFrame(file_data)
    else:
        return [(pd.DataFrame(), None)], pd.DataFrame()

def get_cff_preferred_citation_data(owner: str, repo: str) -> tuple[list[tuple[pd.DataFrame, datetime | None]], pd.DataFrame]:
    cff_path = get_file_path(owner, repo, '*CITATION.cff')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*citation.cff')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*CITATION.CFF')

    if not cff_path:
        cff_path = get_file_path(owner, repo, '*citation.CFF')

    if cff_path:
        file_data = []
        authors_data: list[tuple[pd.DataFrame, datetime | None]] = list()
        path_parts = cff_path.split('/')
        print_file = '/'.join(path_parts[4:])
        git_repo = Repo(f'./repos/{owner}/{repo}')
        commits_for_file = list(git_repo.iter_commits(all=True, paths=print_file))
        for commit_for_file in commits_for_file:
            try:
                tree = commit_for_file.tree
                blob = tree[print_file]
                cff_string = blob.data_stream.read().decode()
                cff_yaml_data = load_cff_data(cff_string)
                valid = validate_cff(cff_path, cff_string)
                cff_init = cff_init_used(cff_string)

                if cff_yaml_data.get('preferred-citation', None) is None:
                    continue

                file_data.append({
                                    'cff_valid': valid,
                                    'cff_init': cff_init,
                                    'type': cff_yaml_data.get('preferred-citation', {}).get('type', None),
                                    'date-released': cff_yaml_data.get('preferred-citation', {}).get('date-released', None),
                                    'date-published': cff_yaml_data.get('preferred-citation', {}).get('date-published', None),
                                    'year': cff_yaml_data.get('preferred-citation', {}).get('year', None),
                                    'month': cff_yaml_data.get('preferred-citation', {}).get('month', None),
                                    'doi': cff_yaml_data.get('preferred-citation', {}).get('doi', None),
                                    'collection-doi': cff_yaml_data.get('preferred-citation', {}).get('collection-doi', None),
                                    'identifier-doi': next((item['value'] for item in cff_yaml_data.get('preferred-citation', {}).get('identifiers', []) if item['type'] == 'doi'), None),
                                    'committed_datetime': str(commit_for_file.committed_datetime),
                                    'authored_datetime': str(commit_for_file.authored_datetime)})
                authors_data.append((load_cff_authors_from_data(cff_yaml_data, 'preferred-citation.authors'), commit_for_file.committed_datetime))
            except KeyError:
                pass
            except AttributeError:
                pass
            except UnicodeDecodeError:
                file_data.append({'cff_valid': False})
                pass

        return authors_data, pd.DataFrame(file_data)
    else:
        return [(pd.DataFrame(), None)], pd.DataFrame()
    
def get_bib_data(owner: str, repo: str) -> tuple[list[tuple[pd.DataFrame, datetime | None]], pd.DataFrame]:
    bib_path = get_file_path(owner, repo, '*CITATION.bib')

    if not bib_path:
        bib_path = get_file_path(owner, repo, '*citation.bib')

    if not bib_path:
        bib_path = get_file_path(owner, repo, '*CITATION.BIB')

    if not bib_path:
        bib_path = get_file_path(owner, repo, '*citation.BIB')
    
    if bib_path:
        file_data = []
        authors_data: list[tuple[pd.DataFrame, datetime | None]] = list()
        path_parts = bib_path.split('/')
        print_file = '/'.join(path_parts[4:])
        git_repo = Repo(f'./repos/{owner}/{repo}')
        commits_for_file = list(git_repo.iter_commits(all=True, paths=print_file))
        for commit_for_file in commits_for_file:
            try:
                tree = commit_for_file.tree
                blob = tree[print_file]
                bib_string = blob.data_stream.read().decode()
                layers = [m.NormalizeFieldKeys(), m.SeparateCoAuthors(), m.SplitNameParts()]
                library = bibtexparser.parse_string(bib_string, append_middleware=layers)
                
                entry_type = library.entries[0].entry_type
                entry_year = library.entries[0].get('year', None)
                entry_month = library.entries[0].get('month', None)
                entry_doi = library.entries[0].get('doi', None)
                entry_isbn = library.entries[0].get('isbn', None)

                if entry_year is not None:
                    entry_year = entry_year.value

                if entry_month is not None:
                    entry_month = entry_month.value

                if entry_doi is not None:
                    entry_doi = entry_doi.value

                if entry_isbn is not None:
                    entry_isbn = entry_isbn.value

                file_data.append({'type': entry_type,
                                  'year': entry_year,
                                  'month': entry_month,
                                  'doi': entry_doi,
                                  'isbn': entry_isbn,
                                  'committed_datetime': str(commit_for_file.committed_datetime),
                                  'authored_datetime': str(commit_for_file.authored_datetime)})

                authors_data.append((get_bib_authors(library), commit_for_file.committed_datetime))
            except KeyError:
                pass
            
        return authors_data, pd.DataFrame(file_data)
    else:
        return [(pd.DataFrame(), None)], pd.DataFrame()

def get_bib_authors(library: bibtexparser.Library) -> pd.DataFrame:
    authors: list = list()

    entries = library.entries[0]['author']

    if entries is not None:
        for entry in entries:
            authors.append(' '.join(entry.first) + " " + ' '.join(entry.last))

    authors_df = pd.DataFrame(authors, columns=['name'])

    return authors_df
    
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

    if len(parsed_data) == 0:
        for match in pattern.finditer(cran_author):
            name = match.group('name').strip()
            
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
    if not pypi_data["info"]["project_urls"]:
        raise ValueError(f"No GitHub repository found in PyPI data.")

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
        url = cran_data.get("BugReports")
        if not url:
            raise ValueError(f"No GitHub repository found in CRAN data.")

        urls = [x.strip() for x in url.split(',')]

        repo_link = [url for url in urls if "github.com" in url]
        if not repo_link:
            url = cran_data.get("BugReports")
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

def get_description_authors(description: str) -> pd.DataFrame:
    nlp = spacy.load("en_core_web_trf")
    doc = nlp(description)
    authors: list = list()
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.text not in authors:
                authors.append(ent.text)

    return pd.DataFrame(authors, columns=['name'])

def get_readme_authors(owner: str, repo: str, position: int) -> tuple[list[tuple[pd.DataFrame, datetime | None]], pd.DataFrame]:
    file = Path(f'./repos/{owner}/{repo}/README.md')
    if file.is_file():
        file_data = []
        authors_data: list[tuple[pd.DataFrame, datetime | None]] = list()
        print_file = 'README.md'
        git_repo = Repo(f'./repos/{owner}/{repo}')
        commits_for_file = list(git_repo.iter_commits(paths=print_file, max_count=50))
        for commit_for_file in tqdm(commits_for_file, desc=f'{repo} README', position=position, dynamic_ncols=True):
            try:
                tree = commit_for_file.tree
                blob = tree[print_file]
                readme_string = blob.data_stream.read().decode()

                file_data.append({'committed_datetime': str(commit_for_file.committed_datetime),
                                  'authored_datetime': str(commit_for_file.authored_datetime)})

                authors_data.append((get_description_authors(readme_string), commit_for_file.committed_datetime))
            except KeyError:
                pass
        return authors_data, pd.DataFrame(file_data)
    else:
        return [(pd.DataFrame(), None)], pd.DataFrame()
