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
            if 'name' in df.columns and author["name"] is not None and contributor["name"] is not None and author["name"].lower() in contributor["name"].lower():
                counter += 1
            if 'email' in df.columns and author["email"] is not None and contributor["email"] is not None and author["email"].lower() in contributor["email"].lower():
                counter += 1
            if 'login' in df.columns and author["login"] is not None and contributor["email"] is not None and author["login"].lower() in contributor["email"].lower():
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

def parse_contribution_stats(data: str) -> list:
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
        authors.append({
            'name': name,
            'email': email,
            'insertions': int(insertions),
            'deletions': int(deletions),
            'files': int(files),
            'commits': int(commits),
            'first_commit': datetime.strptime(first_commit, '%a %b %d %H:%M:%S %Y %z'),
            'last_commit': datetime.strptime(last_commit, '%a %b %d %H:%M:%S %Y %z'),
            'lines_changed': int(lines_changed),
        })

    return authors

def get_git_contributors(owner: str, repo: str, repo_link: str) -> pd.DataFrame:
    try:
        Repo.clone_from(repo_link, f'./repos/{owner}/{repo}')
    except GitCommandError as ex:
        print("Repo already exists")
        print(ex)

    # Stark unterschiedliche Anzahl der commits abhängig vom Programm
    git_quick_stat = subprocess.run(['git', 'quick-stats', '-T'], capture_output=True, encoding='utf-8', cwd=f'.\\repos\\{owner}\\{repo}')
    
    # Doppelte Leute, da unterschiedliche Namen beim commiten angegeben -> Das Problem besteht beim benutzen der GitHub API nicht. -> Teilweise Gelöst mittels group auf E-Mail
    data = git_quick_stat.stdout

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

def get_cff_authors(owner: str, repo: str) -> pd.DataFrame:
    try:
        with open(f'./repos/{owner}/{repo}/CITATION.cff', 'r') as file:
            cff = yaml.safe_load(file)
        cff_authors = cff["authors"]
        list = get_cff_list(cff_authors)
        return pd.DataFrame(list)
    except FileNotFoundError:
        return pd.DataFrame()

def get_cff_preferred_citation_authors(owner: str, repo: str) -> pd.DataFrame:
    try:
        with open(f'./repos/{owner}/{repo}/CITATION.cff', 'r') as file:
            cff = yaml.safe_load(file)
        cff_preferred_citation_authors = cff["preferred-citation"]["authors"]
        list = get_cff_list(cff_preferred_citation_authors)
        cff_df = pd.DataFrame(list)
    except FileNotFoundError:
        cff_df = pd.DataFrame()
    return cff_df

def get_bib_authors(owner: str, repo: str) -> pd.DataFrame:
    file = Path(f'./repos/{owner}/{repo}/CITATION.bib')
    if(file.is_file()):
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

def get_python_authors(pypi_data) -> pd.DataFrame:
    python_author_email = pypi_data["info"]["author_email"]
    if python_author_email == '' or python_author_email == None:
        python_author_emails = []
    else:
        python_author_emails = python_author_email.split(", ")

    python_author = pypi_data["info"]["author"]
    if python_author == '' or python_author == None:
        python_authors = []
    else:
        python_authors = python_author.split(", ")

    return combine_name_email(python_authors, python_author_emails)

def get_python_maintainers(pypi_data) -> pd.DataFrame:
    python_maintainer_email = pypi_data["info"]["maintainer_email"]
    if python_maintainer_email == '' or python_maintainer_email == None:
        python_maintainer_emails = []
    else:
        python_maintainer_emails = python_maintainer_email.split(", ")

    python_maintainer = pypi_data["info"]["maintainer"]
    if python_maintainer == '' or python_maintainer == None:
        python_maintainers = []
    else:
        python_maintainers = python_maintainer.split(", ")

    return combine_name_email(python_maintainers, python_maintainer_emails)

def get_cran_authors(cran_data) -> pd.DataFrame:
    import rpy2.robjects as ro
    cran_author = cran_data["Authors@R"]
    authors = ro.r(f'''eval(parse(text = '{cran_author}'))''')

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
    repo_link = pypi_data["info"]["project_urls"].get("Source code") or pypi_data["info"]["project_urls"].get("GitHub: repo") or pypi_data["info"]["project_urls"].get("Source") or pypi_data["info"]["project_urls"].get("Download")
    owner = repo_link.split("/")[3]
    repo = repo_link.split("/")[4]
    repo_link = repo_link.split("/")[:5]
    repo_link = '/'.join(str(x) for x in repo_link)
    return owner, repo, repo_link

def get_cran_repo(cran_data) -> tuple[str, str, str]:
    url = cran_data["URL"]
    urls = [x.strip() for x in url.split(',')]
    repo_link = [url for url in urls if "github" in url][0]
    owner = repo_link.split("/")[3]
    repo = repo_link.split("/")[4]
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
