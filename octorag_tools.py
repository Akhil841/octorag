from typing import Any
import httpx
import re
import base64
import os

GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")

LINESEP = "----------------------\n"


def query_repos(keyword: str) -> Any:
    keyword = keyword.lower()
    keyword = keyword.replace(" ", "_")
    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars"
    with httpx.Client() as client:
        try:
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"An error occured: {e}")


def format_repos(repos_json: Any, count: int) -> str:
    repos = repos_json["items"][: min(len(repos_json["items"]), count)]
    out = ""
    for r in repos:
        out += LINESEP
        out += f"Repository Name: {r['name']}\n"
        out += f"Repository Owner: {r['owner']['login']}\n"
        out += f"Repository URL: {r['html_url']}\n"
        out += f"Repository Description: {r['description']}\n"
        out += f"Repository Stars: {r['stargazers_count']}\n"
    out += LINESEP
    return out


def get_readme(html_url: str) -> str:
    """Returns the README of an input GitHub repository.

    Args:
        html_url: The URL of the repository whose README you want to read. URL should be of the form https://github.com/owner/repo.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    matches = re.match("https?://github\.com/([^/]+)/([^/]+)/?", html_url)
    owner = ""
    repo = ""
    if matches:
        owner, repo = matches.groups()
    else:
        return "Malformed input URL. Expects a GitHub HTML URL of the form https://github.com/owner/repo"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
    with httpx.Client() as client:
        try:
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception:
            return "Repository does not have a readme"


def query_for_github_repos(keywords: str, count: int = 1) -> str:
    """Get information about repositories relevant to the keywords you enter. Output sorted by star count.

    Args:
        keywords: List of keywords you want to search for. Keywords can be multiple words long (in which case they must be separated by spaces), but each keyword must be delimited by a comma. A sample query might be `python,computer vision,confidential`, without the backticks.
        count: The number of repositories you want information about (the top `count` repositories). Default 1. If the keywords return less repositories than the inputted value, returns information about all repositories.
    """
    repo_info = query_repos(keywords)
    repo_output = format_repos(repo_info, count)
    return repo_output


def get_repo_tree(html_url: str) -> str:
    """Get the list of files of a given repository.

    Args:
        html_url: The URL of the repository you want the file list of. Must be of the format `https://github.com/owner/repo`.
    """

    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    matches = re.match("https?://github\.com/([^/]+)/([^/]+)/?", html_url)
    owner = ""
    repo = ""
    if matches:
        owner, repo = matches.groups()
    else:
        return "Malformed input URL. Expects a GitHub HTML URL of the form https://github.com/owner/repo"
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees"
    repo_bare_url = f"https://api.github.com/repos/{owner}/{repo}"
    default_branch = ""
    tree_sha = ""
    with httpx.Client() as client:
        try:
            response = client.get(repo_bare_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            default_branch = data["default_branch"]
        except Exception as e:
            print(e)
            return "Failed at default branch obtain"

    get_sha_url = repo_bare_url + f"/branches/{default_branch}"
    with httpx.Client() as client:
        try:
            response = client.get(get_sha_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            tree_sha = data["commit"]["commit"]["tree"]["sha"]
        except Exception as e:
            print(e)
            return "Failed at default branch SHA obtain"

    tree_url = url + f"/{tree_sha}?recursive=1"
    tree = None
    with httpx.Client() as client:
        try:
            response = client.get(tree_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            tree = data["tree"]
        except Exception as e:
            print(e)
            return "Repository does not have a tree"

    out = ""
    out += "File list:\n"
    for v in tree:
        out += f"{str(v['path'])}\n"
    return out


def get_file_contents(html_url: str, file_dir: str) -> str:
    """Returns the contents of a file in a GitHub repository.

    Args:
        html_url: The URL of the repository you want the file list of. Must be of the format `https://github.com/owner/repo`.
        file_dir: The location of the file you want to read within the repository. For example, if the file is located at `ROOT/path/to/file`, where `ROOT` is the root of the repository, you would input 'path/to/file'.
    """

    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    matches = re.match("https?://github\.com/([^/]+)/([^/]+)/?", html_url)
    owner = ""
    repo = ""
    if matches:
        owner, repo = matches.groups()
    else:
        return "Malformed input URL. Expects a GitHub HTML URL of the form https://github.com/owner/repo"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_dir}"
    with httpx.Client() as client:
        try:
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception:
            return f"Repository {owner}/{repo} does not have file {file_dir}, or file is too big."
