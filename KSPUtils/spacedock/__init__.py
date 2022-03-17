from pathlib import Path

from KSPUtils.gpg_utils import decrypt, encrypt
from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.path_utils import search_upward
from KSPUtils.spacedock.errors import SpacedockError
from KSPUtils.spacedock.user import User

SPACEDOCK_AUTH_FILE = ".spacedock.gpg"


def login(path: StrPath) -> User:
    auth_file = search_upward(SPACEDOCK_AUTH_FILE, path)
    if not auth_file:
        raise SpacedockError(f"No {SPACEDOCK_AUTH_FILE} found")
    try:
        with auth_file.open("rb") as inp:
            data = decrypt(inp)
        return User.login(*data.splitlines())
    except Exception as e:
        raise SpacedockError("Unable to login", e)


def set_auth(username: str, password: str, path: StrPath) -> None:
    try:
        data = encrypt(f"{username}\n{password}")
        (Path(path) / SPACEDOCK_AUTH_FILE).write_text(data, encoding="utf8")
    except Exception as e:
        raise SpacedockError("Unable to encrypt spacedock auth", e)
