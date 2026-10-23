import datetime
import os
from functools import lru_cache

import requests
from flask import abort, redirect, request, session, url_for

from applib.permissions import get_default_permissions


def authenticate():
    """
    Authenticates a user with OIDC. On success, an ID token is stored in the
    session key `identity` with the following format:

        {
            "sub": usename of the authenticated principal.
            "family_name": family name of the principal,
            "given_name": given name of the principal,
            "permissions": {
                "list_files": boolean,
                "create_folder": boolean,
                "remove_folder": boolean,
                "download_file": boolean,
                "upload_file": boolean,
                "remove_file": boolean,
            }
        }
    """
    code = request.args.get("code", None)
    if code is None:
        get_authorization_code()
    else:
        id_token = exchange_code_for_id_token(code)
        if id_token is None:
            abort(401)
        user = id_token["preferred_username"].split("@")[0]
        identity = {
            "sub": user,
            "family_name": None,
            "given_name": None,
            "permissions": get_default_permissions(),
        }
        session["identity"] = identity
        permissions = identity["permissions"]
        new_permissions = {}
        for permission in permissions.keys():
            value = str2bool(id_token.get(permission, "0"))
            new_permissions[permission] = value
        identity["permissions"] = new_permissions


def sso_logout():
    """
    SSO logout
    """
    oidc_logout_url = os.environ.get("OIDC_LOGOUT_URL")
    if oidc_logout_url is not None:
        return redirect(oidc_logout_url)
    return redirect(url_for("index"))


def str2bool(s):
    """
    Convert various string representations to boolean values.
    """
    if s.lower().startswith("t"):
        return True
    elif s == "1":
        return True
    return False


def get_authorization_code():
    """
    Redirect user to login and get OIDC code.
    """
    oidc_metadata = get_oidc_metadata()
    authorization_endpoint = oidc_metadata["authorization_endpoint"]
    client_id = os.environ["OIDC_CLIENT_ID"]
    login_url = (
        f"{authorization_endpoint}?client_id={client_id}&"
        "response_type=code&scope=openid%20profile%20email"
    )
    return redirect(login_url)


def exchange_code_for_id_token(code):
    """
    Exchange an authorization code for an access token.
    """
    redirect_uri = os.environ["OIDC_REDIRECT_URI"]
    oidc_metadata = get_oidc_metadata()
    token_endpoint = oidc_metadata["token_endpoint"]
    client_id = os.environ["OIDC_CLIENT_ID"]
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_endpoint, headers=headers, data=data)
    result = response.json()
    id_token = result.get("id_token")
    return id_token


def get_oidc_metadata():
    """
    Retrieve OIDC metadata.
    """
    tstamp = (int(datetime.datetime.today().timestamp()) // 600) * 600
    return _get_oidc_metadata(tstamp)


@lru_cache(maxsize=10)
def _get_oidc_metadata(tstamp):
    """
    Cached implementation of fetching OIDC metadata.
    """
    metadata_url = os.environ["OIDC_METADATA_URL"]
    response = requests.get(metadata_url)
    metadata = response.json()
    return metadata
