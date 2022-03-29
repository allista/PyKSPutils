from pathlib import Path
from typing import Dict, Optional

import jsonobject as jo
import requests

from KSPUtils.info_extractors.versions import VersionBase
from KSPUtils.spacedock import SpacedockError
from KSPUtils.spacedock.api_object import ApiObject
from KSPUtils.spacedock.common import WithId
from KSPUtils.spacedock.mod_version import ModVersion


class Mod(WithId, ApiObject):
    _PATH = "/mod/{id}"

    url = jo.StringProperty(required=True)
    name = jo.StringProperty(required=True)
    game = jo.StringProperty(required=True)
    game_id = jo.IntegerProperty(required=True)
    author = jo.StringProperty(required=True)
    shared_authors = jo.ListProperty(jo.StringProperty())
    license = jo.StringProperty()
    website = jo.StringProperty()
    source_code = jo.StringProperty()
    short_description = jo.StringProperty()
    description = jo.StringProperty()
    downloads = jo.IntegerProperty()
    followers = jo.IntegerProperty()
    donations = jo.StringProperty()
    background = jo.StringProperty()
    bg_offset_x = jo.IntegerProperty()
    bg_offset_y = jo.IntegerProperty()
    default_version_id = jo.IntegerProperty()
    versions = jo.ListProperty(jo.ObjectProperty(ModVersion))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._version_by_id: Dict[int, int] = {
            v.id: i for i, v in enumerate(self.versions)
        }
        self._version_by_fv: Dict[VersionBase, int] = {
            v.version: i for i, v in enumerate(self.versions)
        }

    @property
    def default_version(self) -> Optional[ModVersion]:
        return self.get_version_by_id(self.default_version_id)

    def get_version_by_id(self, version_id: int) -> Optional[ModVersion]:
        try:
            return self.versions[self._version_by_id[version_id]]
        except KeyError:
            return None

    def get_version(self, version: VersionBase) -> Optional[ModVersion]:
        try:
            return self.versions[self._version_by_fv[version]]
        except KeyError:
            return None

    @classmethod
    def get(cls, mod_id: int) -> "Mod":
        return cls._get(cls._url(id=mod_id))

    def reload(self) -> "Mod":
        return self.get(self.id)

    # pylint: disable=too-many-arguments
    def update(
        self,
        version: str,
        changelog: str,
        game_version: str,
        zipball: Path,
        notify_followers=True,
    ) -> None:
        if not self._COOKIES:
            raise SpacedockError("Updating requires authentication")
        try:
            res = requests.post(
                f"{self._url(id=self.id)}/update",
                files=(
                    ("version", (None, version)),
                    ("changelog", (None, changelog)),
                    ("game-version", (None, game_version)),
                    ("notify-followers", (None, "yes" if notify_followers else "no")),
                    ("zipball", (zipball.name, zipball.read_bytes())),
                ),
            )
            res.raise_for_status()
        except Exception as e:
            raise SpacedockError(
                f"Unable to update mod {self.name} to {version}", e
            ) from e
