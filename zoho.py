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
def crm_list_leads(limit=10):
    return crm_get("Leads", {"per_page": limit}).json()

def crm_add_note(module, record_id, title, content):
    # Notes sind eigenes Modul; parent_id verknüpft die Notiz mit dem Datensatz
    url = f"{CRM_BASE}/Notes"
    payload = {
        "data": [{
            "Note_Title": title,
            "Note_Content": content,
            "Parent_Id": record_id,
            "se_module": module  # z.B. "Leads", "Contacts", "Deals"
        }]
    }
    t = access_token()
    h = {"Authorization": f"Zoho-oauthtoken {t}"}
    return requests.post(url, headers=h, json=payload, timeout=30).json()

def crm_create_task(module, record_id, subject, due_in_days=3):
    # Aufgaben = "Tasks" (Activities)
    url = f"{CRM_BASE}/Tasks"
    from datetime import datetime, timedelta
    due_date = (datetime.utcnow() + timedelta(days=due_in_days)).strftime("%Y-%m-%d")
    payload = {
        "data": [{
            "Subject": subject,
            "What_Id": record_id,   # Verknüpfung z. B. mit Lead/Deal
            "$se_module": module,   # "Leads", "Deals", "Contacts"
            "Due_Date": due_date,
            "Status": "Not Started",
            "Priority": "High"
        }]
    }
    t = access_token()
    h = {"Authorization": f"Zoho-oauthtoken {t}"}
    return requests.post(url, headers=h, json=payload, timeout=30).json()

def crm_convert_lead(lead_id):
    # Standard-Konvertierung: erstellt Account+Contact und optional Deal
    url = f"{CRM_BASE}/Leads/{lead_id}/actions/convert"
    payload = {
        "data": [{
            "overwrite": True,
            "notify_lead_owner": False,
            "notify_new_entity_owner": False,
            "Deals": {
                "Deal_Name": "Auto-Deal aus Lead",
                "Stage": "Qualification",
                "Amount": 0
            }
        }]
    }
    t = access_token()
    h = {"Authorization": f"Zoho-oauthtoken {t}"}
    return requests.post(url, headers=h, json=payload, timeout=30).json()
