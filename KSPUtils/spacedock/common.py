import jsonobject as jo

SPACEDOCK_URL = "https://spacedock.info"
API_URL = f"{SPACEDOCK_URL}/api"


class WithId(jo.JsonObject):
    id = jo.IntegerProperty(required=True)
