from pathlib import Path

from KSPUtils.path_utils import get_search_paths


def test_get_search_paths_one_path():
    first_path = Path("some/path")
    all_paths = get_search_paths(first_path)
    assert all_paths == [first_path]


def test_get_search_paths_multiple_paths():
    first_path = Path("some/path")
    all_paths = get_search_paths(first_path, "one", "two", "three")
    assert all_paths == [
        first_path,
        first_path / "one",
        first_path / "two",
        first_path / "three",
    ]
