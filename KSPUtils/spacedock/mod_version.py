import jsonobject as jo

from KSPUtils.info_extractors.versions import SimpleVersion
from KSPUtils.spacedock import SpacedockError
from KSPUtils.spacedock.common import SPACEDOCK_URL, WithId


class ModVersion(WithId):
    created = jo.DateTimeProperty(required=True)
    changelog = jo.StringProperty(required=True)
    download_path = jo.StringProperty(required=True)
    friendly_version = jo.StringProperty(required=True)
    game_version = jo.StringProperty(required=True)
    downloads = jo.IntegerProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._version = SimpleVersion.from_str(self.friendly_version)
        if self._version is None:
            raise SpacedockError(
                f"Unable to parse mod version: {self.friendly_version}"
            )

    @property
    def version(self) -> SimpleVersion:
        return self._version

    @property
    def download_url(self) -> str:
        return f"{SPACEDOCK_URL}{self.download_path}"
