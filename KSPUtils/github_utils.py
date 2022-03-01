from pathlib import Path

from github import Github

from KSPUtils.exception_chain import ExceptionChain
from KSPUtils.gpg_utils import decrypt, encrypt
from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.path_utils import search_upward

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
        raise GithubError(f"Unable to get github token", e)


def set_github_token(token: str, path: StrPath) -> None:
    try:
        data = encrypt(token)
        (Path(path) / GITHUB_AUTH_FILE).write_text(data, encoding="utf8")
    except Exception as e:
        raise GithubError(f"Unable to set github token", e)


def get_github(path: StrPath) -> Github:
    return Github(get_github_token(path))
