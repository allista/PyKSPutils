import jsonobject as jo

SPACEDOCK_URL = "https://spacedock.info"
API_URL = f"{SPACEDOCK_URL}/api"

REQUEST_TIMEOUT = 60


class WithId(jo.JsonObject):
    id = jo.IntegerProperty(required=True)
