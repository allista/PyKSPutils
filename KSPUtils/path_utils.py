from pathlib import Path
from typing import List, Optional

from KSPUtils.info_extractors.file_extractor import StrPath


def get_search_paths(base_path: Path, *add_paths: StrPath) -> List[Path]:
    return [base_path, *(base_path / p for p in add_paths)]


def search_upward(filename: str, path: StrPath) -> Optional[Path]:
    cwd = Path(path).resolve()

    def filepath():
        return cwd / filename

    while not filepath().is_file():
        if cwd == cwd.parent:
            return None
        cwd = cwd.parent
    return filepath()
