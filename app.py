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
