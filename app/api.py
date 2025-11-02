import json

from flask import Blueprint
from flask import session, request, jsonify

from database import ContractData

api_bp = Blueprint('api', __name__)


@api_bp.route("/api/contracts", methods=["GET"])
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


@api_bp.route("/api/contracts", methods=["POST"])
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


@api_bp.route("/api/contracts/<int:contract_id>", methods=["PATCH"])
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


@api_bp.route("/api/contracts/<int:contract_id>", methods=["DELETE"])
def delete_contract(contract_id):
    google_id = session.get("google_id")
    contract = ContractData.get_or_none(ContractData.id == contract_id, ContractData.author_google_id == google_id)
    if not contract:
        return jsonify({"error": "Contract not found"}), 404

    contract.delete_instance()
    return jsonify({"success": True})
