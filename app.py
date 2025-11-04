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
