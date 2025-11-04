import os, time, requests

ACCOUNTS = "https://accounts.zoho.eu"
CRM_BASE  = "https://www.zohoapis.eu/crm/v3"
CID = os.getenv("ZOHO_CLIENT_ID")
CSC = os.getenv("ZOHO_CLIENT_SECRET")
RFT = os.getenv("ZOHO_REFRESH_TOKEN")

_cache = {"tok": None, "exp": 0}

def access_token():
    import time
    if _cache["tok"] and _cache["exp"] > time.time() + 60:
        return _cache["tok"]
    r = requests.post(f"{ACCOUNTS}/oauth/v2/token", params={
        "grant_type":"refresh_token","refresh_token":RFT,
        "client_id":CID,"client_secret":CSC
    }, timeout=20)
    r.raise_for_status()
    data = r.json()
    _cache["tok"] = data["access_token"]
    _cache["exp"] = time.time() + int(data.get("expires_in",3600))
    return _cache["tok"]

def crm_get(path, params=None):
    t = access_token()
    h = {"Authorization": f"Zoho-oauthtoken {t}"}
    return requests.get(f"{CRM_BASE}/{path.lstrip('/')}", headers=h, params=params or {}, timeout=30)

def crm_whoami():
    # einfacher Test: eigene Benutzerinfos abrufen
    return crm_get("users", {"type":"CurrentUser"}).json()
