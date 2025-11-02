import json
import os

import google.auth.transport.requests
from flask import Flask, redirect, session, request, jsonify, render_template, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from database import ContractData

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_key_only_for_local")

GOOGLE_CLIENT_ID = "727910134511-iciag20av4v4u3hdqajarn2g2s59g1ng.apps.googleusercontent.com"
client_secrets_file = "client_secret.json"

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email",
            "openid"],
    redirect_uri=os.getenv("REDIRECT_URI")
)


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/auth/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    request_session = google.auth.transport.requests.Request()
    id_info = id_token.verify_oauth2_token(
        id_token=credentials.id_token,
        request=request_session,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")

    return redirect(url_for('dashboard'))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('dashboard'))


@app.route("/dashboard")
def dashboard():
    if not session.get("google_id"):
        return redirect(url_for('login'))
    return render_template("dashboard.html")


@app.route("/api/contracts", methods=["GET"])
def get_contracts():
    google_id = session.get("google_id")
    if not google_id:
        return jsonify({"error": "Unauthorized"}), 401

    contracts = (
        ContractData
        .select()
        .where(ContractData.author_google_id == google_id)
        .order_by(ContractData.name)

    )

    result = []
    for c in contracts:
        result.append({
            "id": c.id,
            "name": c.name,
            "sfmc_subdomain": c.sfmc_subdomain,
            "client_id": c.client_id,
            "client_secret": c.client_secret,
            "de_key": c.de_key,
            "contacts_limit": c.contacts_limit,
            "contacts_amount": c.contacts_amount,
            "last_checked": c.last_checked.strftime("%d/%m/%Y %H:%M") if c.last_checked else None,
            "slack_users_ids": c.slack_users_ids,
        })

    return jsonify(result)


@app.route("/api/contracts", methods=["POST"])
def add_contract():
    google_id = session.get("google_id")
    data = request.form

    slack_ids = data.get("slack_users_ids", "")
    slack_ids_list = [u.strip() for u in slack_ids.split(",") if u.strip()]

    contract = ContractData.create(
        name=data.get("name"),
        author_google_id=google_id,
        slack_users_ids_raw=json.dumps(slack_ids_list),
        sfmc_subdomain=data.get("sfmc_subdomain"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        de_key=data.get("de_key"),
        contacts_limit=int(data.get("contacts_limit")),
        contacts_amount=0,
    )
    return jsonify({"success": True, "id": contract.id}), 201


@app.route("/api/contracts/<int:contract_id>", methods=["PATCH"])
def edit_contract(contract_id):
    google_id = session.get("google_id")
    contract = ContractData.get_or_none(
        ContractData.id == contract_id,
        ContractData.author_google_id == google_id
    )
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    for field in [
        "name", "sfmc_subdomain", "client_id", "client_secret",
        "de_key", "contacts_limit", "slack_users_ids"
    ]:
        if field in data:
            if field == "contacts_limit":
                setattr(contract, field, int(data[field]))
            elif field == "slack_users_ids":
                contract.slack_users_ids = data[field]
            else:
                setattr(contract, field, data[field])

    contract.save()
    return jsonify({"success": True})


@app.route("/api/contracts/<int:contract_id>", methods=["DELETE"])
def delete_contract(contract_id):
    google_id = session.get("google_id")
    contract = ContractData.get_or_none(ContractData.id == contract_id, ContractData.author_google_id == google_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    contract.delete_instance()
    return jsonify({"success": True})
