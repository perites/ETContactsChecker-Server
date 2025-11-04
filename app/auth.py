import os
import json

import google.auth.transport.requests
from flask import Blueprint
from flask import redirect, session, request, url_for
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

auth_bp = Blueprint('auth', __name__)

with open("client_secret.json") as f:
    client_data = json.load(f)
GOOGLE_CLIENT_ID = client_data["web"]["client_id"]


@auth_bp.route("/login")
def login():
    
    flow = Flow.from_client_secrets_file(
    "client_secret.json",
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri=os.getenv("REDIRECT_URI")
)
    
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@auth_bp.route("/auth/callback")
def callback():

    flow = Flow.from_client_secrets_file(
    "client_secret.json",
    scopes=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_uri=os.getenv("REDIRECT_URI")
)

    
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

    return redirect(url_for('dashboard.dashboard'))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('dashboard.dashboard'))
