from pathlib import Path
from typing import List


def get_search_paths(base_path: Path, *add_paths: str) -> List[Path]:
    return [base_path, *(base_path / p for p in add_paths)]
