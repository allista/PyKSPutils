from typing import BinaryIO, Union

import gnupg

from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.utils.path import search_upward

GPG_ID_FILE = ".gpg-id"


class GpgException(Exception):
    """Generic GPG exception"""


def get_gpg() -> gnupg.GPG:
    return gnupg.GPG(use_agent=True)


def _crypt_to_data(crypt: gnupg.Crypt) -> str:
    if crypt.ok:
        return str(crypt)
    raise GpgException(crypt.status)


def get_gpg_id(path: StrPath) -> str:
    gpg_id_file = search_upward(GPG_ID_FILE, path)
    if gpg_id_file:
        return gpg_id_file.read_text().strip()
    raise GpgException(f"No {GPG_ID_FILE} found")


def encrypt(data: Union[str, bytes, BinaryIO]) -> str:
    gpg_id = get_gpg_id("..")
    if isinstance(data, (str, bytes)):
        return _crypt_to_data(get_gpg().encrypt(data, gpg_id))
    return _crypt_to_data(get_gpg().encrypt_file(data, gpg_id))


def decrypt(data: Union[str, bytes, BinaryIO]) -> str:
    if isinstance(data, (str, bytes)):
        return _crypt_to_data(get_gpg().decrypt(data))
    return _crypt_to_data(get_gpg().decrypt_file(data))
