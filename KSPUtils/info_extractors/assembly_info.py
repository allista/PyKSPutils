from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TextIO, Type

from KSPUtils.file_saver_mixin import FileSaverMixin
from KSPUtils.info_extractors.file_extractor import (
    FileExtractor,
    FileExtractorType,
    StrPath,
)
from KSPUtils.info_extractors.regex_extractor import GroupType, RegexExtractorType
from KSPUtils.info_extractors.titles import AssemblyTitle
from KSPUtils.info_extractors.versions import (
    AssemblyVersion,
    KSPAssemblyVersion,
    MaxKSPVersion,
    MinKSPVersion,
)


class AssemblyInfo(FileSaverMixin, FileExtractor):
    def __init__(self, filepath: Path, date: datetime, content: TextIO) -> None:
        super().__init__(filepath)
        self.date = date
        self._content = [line.rstrip("\n\r") for line in content]
        self._line_by_entity_id: Dict[int, int] = {}
        self.title = self._extract_from_content(AssemblyTitle)
        self.assembly_version = self._extract_from_content(AssemblyVersion, date=date)
        self.ksp_assembly_version = self._extract_from_content(
            KSPAssemblyVersion, date=date
        )
        self.min_ksp_version = self._extract_from_content(MinKSPVersion, date=date)
        self.max_ksp_version = self._extract_from_content(MaxKSPVersion, date=date)

    def _extract_from_content(
        self, extractor: Type[RegexExtractorType], **kwargs: Any
    ) -> Optional[RegexExtractorType]:
        for i, line in enumerate(self._content):
            data = extractor.from_str(line, **kwargs)
            if data:
                self._line_by_entity_id[id(data)] = i
                return data
        return None

    def __str__(self):
        return "\n".join(self._content)

    def replace(self, entity_name: str, replacement: str, group: GroupType = 1) -> bool:
        try:
            entity = getattr(self, entity_name)
        except AttributeError as e:
            raise AttributeError(f"Unknown entity: {entity_name}") from e
        if entity is None:
            return False
        line_num = self._line_by_entity_id.get(id(entity))
        if line_num is None:
            return False
        old_line = self._content[line_num]
        new_line = entity.replace(self._content[line_num], replacement, group)
        if old_line == new_line:
            return False
        new_entity = entity.from_str(new_line)
        if not new_entity:
            raise ValueError(
                f"Replacement does not match entity pattern:\n{new_line}\n{entity.pattern()}"
            )
        self._content[line_num] = new_line
        self._line_by_entity_id[id(new_entity)] = line_num
        setattr(self, entity_name, new_entity)
        del self._line_by_entity_id[id(entity)]
        self._dirty = True
        return True

    def summary(self):
        info = [
            f"Date:         {self.date:%Y-%m-%d %H:%M:%S %z}",
            f"Title:        {self.title}",
            f"Assembly:     {self.assembly_version}",
        ]
        if self.ksp_assembly_version:
            info.append(f"KSP Assembly: {self.ksp_assembly_version}")
        if self.min_ksp_version:
            if self.max_ksp_version and self.min_ksp_version != self.max_ksp_version:
                info += [
                    f"Min KSP:      {self.min_ksp_version}",
                    f"Max KSP:      {self.max_ksp_version}",
                ]
            else:
                info.append(f"KSP:          {self.min_ksp_version}")
        if self._dirty:
            info.append("WARNING: changes are not saved to disk")
        return "\n".join(info)

    def __repr__(self):
        return self.summary()

    @classmethod
    def from_file(
        cls: Type[FileExtractorType], filename: StrPath, **kwargs: Any
    ) -> Optional[FileExtractorType]:
        filepath, mod_time = cls._resolve_path(filename)
        with filepath.open("rt", encoding="utf8") as inp:
            return cls(filepath=filepath, date=mod_time, content=inp)
