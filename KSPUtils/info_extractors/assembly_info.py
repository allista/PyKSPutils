from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from KSPUtils.info_extractors.file_extractor import FileExtractor, StrPath
from KSPUtils.info_extractors.titles import AssemblyTitle
from KSPUtils.info_extractors.versions import (
    AssemblyVersion,
    KSPAssemblyVersion,
    MaxKSPVersion,
    MinKSPVersion,
)


@dataclass(frozen=True, repr=False)
class AssemblyInfo(FileExtractor):
    date: datetime
    title: AssemblyTitle
    assembly_version: AssemblyVersion
    ksp_assembly_version: Optional[KSPAssemblyVersion]
    min_ksp_version: Optional[MinKSPVersion]
    max_ksp_version: Optional[MaxKSPVersion]

    def __str__(self):
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
        return "\n".join(info)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_file(cls, filename: StrPath) -> "AssemblyInfo":
        text, mod_time = cls._read_path(filename)
        return cls(
            mod_time,
            AssemblyTitle.from_str(text),
            AssemblyVersion.from_str(text, date=mod_time),
            KSPAssemblyVersion.from_str(text, date=mod_time),
            MinKSPVersion.from_str(text, date=mod_time),
            MaxKSPVersion.from_str(text, date=mod_time),
        )
