from pathlib import Path
from typing import List

from KSPUtils.info_extractors.file_extractor import StrPath


def get_search_paths(base_path: Path, *add_paths: StrPath) -> List[Path]:
    return [base_path, *(base_path / p for p in add_paths)]
