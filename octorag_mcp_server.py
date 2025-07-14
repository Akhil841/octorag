from typing import Any
import httpx
import re
import base64
import os
from mcp.server.fastmcp import FastMCP

from dotenv import load_dotenv

load_dotenv()

server = FastMCP("octorag-mcp")

GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")

LINESEP = "----------------------\n"


async def query_repos(keyword: str) -> Any:
    keyword = keyword.lower()
    keyword = keyword.replace(" ", "_")
    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return f"An error occurred: {e}"


async def format_repos(repos_json: Any, count: int) -> str:
    repos = repos_json["items"][: min(len(repos_json["items"]), count)]
    out = ""
    for r in repos:
        out += LINESEP
        out += f"Repository Name: {r['name']}\n"
        out += f"Repository Owner: {r['owner']['login']}\n"
        out += f"Repository URL: {r['html_url']}\n"
        out += f"Repository Description: {r['description']}\n"
        out += f"Repository Stars: {r['stargazers_count']}\n"
        out += f"Repository License: {r['license']['name'] if r['license'] else 'No license'}\n"
    out += LINESEP
    return out


@server.tool()
async def get_readme(html_url: str) -> str:
    """Returns the README of an input GitHub repository.

    Args:
        html_url: The URL of the repository whose README you want to read. URL should be of the form https://github.com/owner/repo.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    matches = re.match("https?://github\\.com/([^/]+)/([^/]+)/?", html_url)
    owner = ""
    repo = ""
    if matches:
        owner, repo = matches.groups()
    else:
        return "Malformed input URL. Expects a GitHub HTML URL of the form https://github.com/owner/repo"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/README.md"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception:
            return "Repository does not have a readme"


@server.tool()
async def query_for_github_repos(keywords: str, count: int = 1) -> str:
    """Get information about repositories relevant to the keywords you enter. Output sorted by star count.

    Args:
        keywords: List of keywords you want to search for. Keywords can be multiple words long (in which case they must be separated by spaces), but each keyword must be delimited by a comma. A sample query might be `python,computer vision,confidential`, without the backticks.
        count: The number of repositories you want information about (the top `count` repositories). Default 1. If the keywords return less repositories than the inputted value, returns information about all repositories.
    """
    repo_info = await query_repos(keywords)
    repo_output = await format_repos(repo_info, count)
    return repo_output


@server.tool()
async def get_repo_tree(html_url: str) -> str:
    """Get the list of files of a given repository.

    Args:
        html_url: The URL of the repository you want the file list of. Must be of the format `https://github.com/owner/repo`.
    """

    headers = {
        "Accept": "application/vnd.github+json",
        "Bearer": GH_ACCESS_TOKEN,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    matches = re.match("https?://github\\.com/([^/]+)/([^/]+)/?", html_url)
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
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(repo_bare_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            default_branch = data["default_branch"]
        except Exception as e:
            return f"Failed at default branch obtain: {e}"

    get_sha_url = repo_bare_url + f"/branches/{default_branch}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(get_sha_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            tree_sha = data["commit"]["commit"]["tree"]["sha"]
        except Exception as e:
            return f"Failed at default branch SHA obtain: {e}"

    tree_url = url + f"/{tree_sha}?recursive=1"
    tree = None
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(tree_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            tree = data["tree"]
        except Exception as e:
            return f"Repository does not have a tree: {e}"

    out = ""
    out += "File list:\n"
    for v in tree:
        out += f"{str(v['path'])}\n"
    return out


@server.tool()
async def get_file_contents(html_url: str, file_dir: str) -> str:
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
    matches = re.match("https?://github\\.com/([^/]+)/([^/]+)/?", html_url)
    owner = ""
    repo = ""
    if matches:
        owner, repo = matches.groups()
    else:
        return "Malformed input URL. Expects a GitHub HTML URL of the form https://github.com/owner/repo"

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_dir}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content
        except Exception as e:
            return f"Repository {owner}/{repo} does not have file {file_dir}, or file is too big: {e}"


@server.tool()
async def create_repo(repository_name: str = "test-repo") -> str:
    """Creates a new GitHub repository with the given repository name. The repository will be private and have a default description. A random value will be appended to the repository name to ensure uniqueness.

    Args:
        repository_name: The name of the repository to create. Defaults to "test-repo".
    """

    import random

    random_value = random.randint(0x1000000, 0xFFFFFFF)
    repository_name = f"{repository_name}-{hex(random_value)[2:]}"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_ACCESS_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = "https://api.github.com/user/repos"
    data = {
        "name": repository_name,
        "description": "This is a code repository generated by OctoRAG.",
        "private": True,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data, timeout=30.0)
            code = response.status_code
            if code == 403:
                return "The provided GitHub Access Token does not have permission to create repositories."
            response.raise_for_status()
            json = response.json()
            return (
                f"Repository {json['name']} created successfully at {json['html_url']}"
            )
        except Exception as e:
            return f"An error occurred while creating the repository: {e}"


@server.tool()
async def create_file(
    owner: str, repo: str, file_contents: str, filename: str = "code.txt"
) -> str:
    """Creates a file in a GitHub repository with the given contents.

    Args:
        owner: The owner of the repository. For example, if the repository URL is `https://github.com/owner/repo`, the owner would be `owner`.
        repo: The name of the repository. For example, if the repository URL is `https://github.com/owner/repo`, the repo would be `repo`.
        file_contents: The (initial) text contents of the file to create.
        filename: The name of the file to create. Defaults to "code.txt".
    """
    headers = {
        "Authorization": f"Bearer {GH_ACCESS_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"

    data = {
        "message": f"Create file {filename}",
        "content": base64.b64encode(file_contents.encode()).decode(),
        "branch": "main",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(url, headers=headers, json=data, timeout=30.0)
            response.raise_for_status()
            return f"File {repo}/{filename} created successfully."
        except Exception as e:
            return f"An error occurred while creating the file: {e}"


@server.tool()
async def append_to_file(
    owner: str, repo: str, further_content: str, filename: str = "code.txt"
) -> str:
    """Appends data to an existing file on GitHub with the provided further content.

    Args:
        owner: The owner of the repository. For example, if the repository URL is `https://github.com/owner/repo`, the owner would be `owner`.
        repo: The name of the repository. For example, if the repository URL is `https://github.com/owner/repo`, the repo would be `repo`.
        further_content: The text to append to the file.
        filename: The name of the file to append to. Defaults to "code.txt".
    """
    headers = {
        "Authorization": f"Bearer {GH_ACCESS_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get the current file contents and sha
            get_response = await client.get(url, headers=headers, timeout=30.0)
            get_response.raise_for_status()
            file_info = get_response.json()
            existing_content = base64.b64decode(file_info["content"]).decode()
            sha = file_info["sha"]

            # Step 2: Append new content
            updated_content = existing_content + further_content
            encoded_content = base64.b64encode(updated_content.encode()).decode()

            # Step 3: Send a PUT request with the updated content
            data = {
                "message": f"Append to {filename}",
                "content": encoded_content,
                "sha": sha,
                "branch": "main",
            }

            put_response = await client.put(
                url, headers=headers, json=data, timeout=30.0
            )
            put_response.raise_for_status()

            return f"File {repo}/{filename} updated successfully."
        except Exception as e:
            return f"An error occurred while appending to the file: {e}"


if __name__ == "__main__":
    server.run(transport="streamable-http")
