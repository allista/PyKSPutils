from typing import Any, Optional, Type

from yaml import safe_load

from KSPUtils.info_extractors.file_extractor import (
    FileExtractor,
    FileExtractorType,
    StrPath,
)


class YamlExtractor(FileExtractor):
    @classmethod
    def from_file(
        cls: Type[FileExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[FileExtractorType]:
        filepath, _mod_time = cls._resolve_path(filename)
        with filepath.open("rt", encoding="utf8") as inp:
            data = safe_load(inp) or {}
            return cls(**data, **kwargs)
