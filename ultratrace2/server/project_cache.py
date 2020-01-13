from functools import lru_cache

from ..model.project import Project


@lru_cache(maxsize=16)
def get_project_by_path(path: str) -> Project:
    return Project.get_by_path(path)
