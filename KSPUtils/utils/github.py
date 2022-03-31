from pathlib import Path

from github import Github

from KSPUtils.exception_chain import ExceptionChain
from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.utils.gpg import decrypt, encrypt
from KSPUtils.utils.path import search_upward

GITHUB_AUTH_FILE = ".github.gpg"


class GithubError(ExceptionChain):
    """Generic github-related error"""


def get_github_token(path: StrPath) -> str:
    token_file = search_upward(GITHUB_AUTH_FILE, path)
    if not token_file:
        raise GithubError(f"No {GITHUB_AUTH_FILE} found")
    try:
        with token_file.open("rb") as inp:
            return decrypt(inp)
    except Exception as e:
        raise GithubError("Unable to get github token", e) from e


def set_github_token(token: str, path: StrPath) -> None:
    try:
        data = encrypt(token)
        (Path(path) / GITHUB_AUTH_FILE).write_text(data, encoding="utf8")
    except Exception as e:
        raise GithubError("Unable to set github token", e) from e


def get_github(path: StrPath) -> Github:
    return Github(get_github_token(path))
