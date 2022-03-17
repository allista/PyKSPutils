from http.cookiejar import CookieJar
from typing import Dict, Optional

import jsonobject as jo
import requests

from KSPUtils.spacedock.api_object import ApiObject
from KSPUtils.spacedock.common import API_URL
from KSPUtils.spacedock.mod import Mod


class User(ApiObject):
    _COOKIES: Optional[CookieJar]
    _PATH = "/user/{username}"

    username = jo.StringProperty(required=True)
    twitterUsername = jo.StringProperty()
    redditUsername = jo.StringProperty()
    ircNick = jo.StringProperty()
    description = jo.StringProperty()
    forumUsername = jo.StringProperty()
    mods = jo.ListProperty(jo.ObjectProperty(Mod))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mod_map: Dict[int, int] = {m.id: i for i, m in enumerate(self.mods)}

    def get_mod(self, mod_id: int, reload=False) -> Optional[Mod]:
        try:
            mod_idx = self._mod_map[mod_id]
            mod: Mod = self.mods[mod_idx]
            if reload:
                mod = mod.reload()
                self.mods[mod_idx] = mod
            return mod
        except KeyError:
            return None

    @classmethod
    def login(cls, username: str, password: str) -> "User":
        res = requests.post(
            f"{API_URL}/login",
            files=(("username", (None, username)), ("password", (None, password))),
        )
        res.raise_for_status()
        cls._set_cookies(res.cookies)
        return cls.get(username)

    @classmethod
    def get(cls, username: str) -> "User":
        return cls._get(cls._url(username=username))
