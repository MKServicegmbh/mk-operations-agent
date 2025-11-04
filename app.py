import os
from flask import Flask, jsonify, abort, request
import zoho

AUTH = os.getenv("BOT_AUTH_TOKEN")  # beliebiges geheimes Token

app = Flask(__name__)

def guard():
    if AUTH and request.headers.get("X-Bot-Auth") != AUTH:
        abort(401)

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/crm/ping")
def crm_ping():
    guard()
    data = zoho.crm_whoami()
    return jsonify({"ok": True, "user": data})
@app.post("/crm/leads/list")
def api_list_leads():
    guard()
    body = request.get_json(silent=True) or {}
    limit = int(body.get("limit", 10))
    data = zoho.crm_list_leads(limit=limit)
    return jsonify({"ok": True, "count": len(data.get("data", [])), "data": data.get("data", [])})

@app.post("/crm/leads/convert")
def api_convert_lead():
    guard()
    body = request.get_json(silent=True) or {}
    lead_id = body.get("lead_id")
    if not lead_id:
        abort(400, "lead_id fehlt")
    res = zoho.crm_convert_lead(lead_id)
    return jsonify({"ok": True, "result": res})

@app.post("/crm/record/note")
def api_add_note():
    guard()
    b = request.get_json(silent=True) or {}
    module = b.get("module")
    record_id = b.get("record_id")
    title = b.get("title","Notiz")
    content = b.get("content","")
    if not (module and record_id):
        abort(400, "module und record_id sind Pflicht")
    res = zoho.crm_add_note(module, record_id, title, content)
    return jsonify({"ok": True, "result": res})

@app.post("/crm/record/task")
def api_add_task():
    guard()
    b = request.get_json(silent=True) or {}
    module = b.get("module")
    record_id = b.get("record_id")
    subject = b.get("subject","Follow-up")
    due_in_days = int(b.get("due_in_days", 3))
    if not (module and record_id):
        abort(400, "module und record_id sind Pflicht")
    res = zoho.crm_create_task(module, record_id, subject, due_in_days)
    return jsonify({"ok": True, "result": res})
# app.py (Ergänzung oben hinzufügen)
import os, re
from flask import request

CLIQ_SECRET = os.getenv("CLIQ_SECRET")  # in Render als ENV setzen

def _ok(msg, card=None):
    # einfache Antwort an Cliq
    out = {"text": msg}
    if card: out["card"] = card
    return out

@app.post("/cliq/ingest")
def cliq_ingest():
    # 1) Webhook-Authentifizierung prüfen (optional je nach Cliq-Konfiguration)
    if CLIQ_SECRET and request.headers.get("X-Cliq-Token") != CLIQ_SECRET:
        return {"text":"Unauthorized"}, 401

    payload = request.get_json(force=True, silent=True) or {}
    text = (payload.get("text") or "").strip()
    user = payload.get("user", {}).get("name", "unknown")

    # 2) Routing: Einfache Befehle -> CRM-Aktionen
    # Beispiele:
    # @mkbot notiz lead <id> <text>
    m = re.match(r".*\bnotiz\s+lead\s+(\d+)\s+(.+)$", text, re.I)
    if m:
        lead_id, note_text = m.group(1), m.group(2)
        res = zoho.crm_add_note("Leads", lead_id, "Notiz", note_text)
        return _ok(f"📝 Notiz angelegt bei Lead {lead_id}.")

    # @mkbot aufgabe lead <id> <betreff> [in <Tagen>]
    m = re.match(r".*\baufgabe\s+lead\s+(\d+)\s+(.+?)(?:\s+in\s+(\d+))?$", text, re.I)
    if m:
        lead_id, subject, days = m.group(1), m.group(2), m.group(3) or "3"
        res = zoho.crm_create_task("Leads", lead_id, subject, int(days))
        return _ok(f"✅ Aufgabe '{subject}' in {days} Tag(en) erstellt (Lead {lead_id}).")

    # @mkbot konvertiere lead <id>
    m = re.match(r".*\bkonvertiere\s+lead\s+(\d+)$", text, re.I)
    if m:
        lead_id = m.group(1)
        res = zoho.crm_convert_lead(lead_id)
        return _ok(f"🔁 Lead {lead_id} konvertiert (Account/Contact/Deal).")

    # @mkbot leads [limit]
    m = re.match(r".*\bleads(?:\s+(\d+))?$", text, re.I)
    if m:
        limit = int(m.group(1) or "3")
        data = zoho.crm_list_leads(limit=limit)
        leads = data.get("data", [])
        if not leads:
            return _ok("Keine Leads gefunden.")
        lines = [f"- {l.get('Company','')} | {l.get('Last_Name','?')} ({l.get('id')})" for l in leads]
        return _ok("📋 Leads:\n" + "\n".join(lines))

    # Fallback-Hilfe:
    help_txt = (
        "Befehle:\n"
        "• @mkbot leads [3]\n"
        "• @mkbot notiz lead <ID> <Text>\n"
        "• @mkbot aufgabe lead <ID> <Betreff> [in <Tagen>]\n"
        "• @mkbot konvertiere lead <ID>\n"
        "• Mehr Aktionen? Schreib: @mkbot hilfe"
    )
    return _ok(help_txt)
