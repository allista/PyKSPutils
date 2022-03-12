from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional

from KSPUtils.info_extractors.file_extractor import StrPath
from KSPUtils.info_extractors.yaml_extractor import YamlExtractor

MOD_CONFIG_FILENAME = "modconfig.yaml"


@dataclass(frozen=True)
class ModConfig(YamlExtractor):
    change_log: str = "ChangeLog.md"
    search_paths: List[str] = field(default_factory=list)
    dll_path: Optional[str] = None
    archive_path: Optional[str] = None
    github_url: Optional[str] = None
    spacedock_url: Optional[str] = None

    @classmethod
    def default(cls, path: StrPath, **kwargs: Any) -> "ModConfig":
        try:
            return cls.from_file(Path(path) / MOD_CONFIG_FILENAME, **kwargs)
        except FileNotFoundError:
            return cls(**kwargs)
