from typing import List, Optional

from git import InvalidGitRepositoryError, PathLike, Repo, Tag


def get_repo(path: PathLike, search_parents=False) -> Optional[Repo]:
    """
    Get Repo object associated with current directory
    """
    try:
        repo = Repo(path, search_parent_directories=search_parents)
    except InvalidGitRepositoryError:
        return None
    except Exception as e:
        print(f"{e}")
        return None
    return repo


def sorted_tags(repo: Repo) -> List[Tag]:
    """
    Returns tags as a list sorted in descending order by authored datetime
    """
    if not repo.tags:
        return []
    return sorted(repo.tags, reverse=True, key=lambda t: t.commit.authored_datetime)


def latest_tag(repo: Repo) -> Optional[Tag]:
    """
    Returns the latest tag by authored datetime
    """
    tags = sorted_tags(repo)
    return tags[0] if tags else None
