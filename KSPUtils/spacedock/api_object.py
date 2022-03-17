from dataclasses import make_dataclass
from http.cookiejar import CookieJar
from typing import Any, Optional, Type, TypeVar

import jsonobject as jo
import requests

from KSPUtils.spacedock import SpacedockError
from KSPUtils.spacedock.common import API_URL


def make_dataclass_object(class_name, members):
    klass = make_dataclass(class_name, [(k, type(v)) for k, v in members.items()])
    return klass(**members)


SchemaObjectType = TypeVar("SchemaObjectType", bound=jo.JsonObject)


class ApiObject(jo.JsonObject):
    _COOKIES: Optional[CookieJar] = None
    _PATH: str

    @classmethod
    def _set_cookies(cls, cookies: Optional[CookieJar]) -> None:
        ApiObject._COOKIES = cookies

    @classmethod
    def logout(cls) -> None:
        cls._set_cookies(None)

    @classmethod
    def _url(cls, **kwargs: Any) -> str:
        return f"{API_URL}{cls._PATH.format(**kwargs)}"

    @classmethod
    def _get(
        cls: Type[SchemaObjectType], url, params: Optional[dict] = None, **kwargs: Any
    ) -> SchemaObjectType:
        if cls._COOKIES:
            kwargs.setdefault("cookies", cls._COOKIES)
        try:
            res = requests.get(url, params, **kwargs)
            res.raise_for_status()
            return cls(res.json())
        except Exception as e:
            raise SpacedockError(f"Unable to get: {url}", e)
