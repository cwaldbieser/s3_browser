import datetime
import json
import os
from functools import lru_cache

import jwt
import requests
from flask import abort, redirect, request, session, url_for
from logzero import logger

from applib.permissions import get_default_permissions
from applib.utils import get_secret_string


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
        return get_authorization_code()
    else:
        id_token = exchange_code_for_id_token(code)
        if id_token is None:
            abort(401)
        logger.info(json.dumps(id_token))
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
        return redirect(url_for("browse", subpath="top"))


def sso_logout():
    """
    SSO logout
    """
    oidc_metadata = get_oidc_metadata()
    oidc_logout_url = oidc_metadata.get("end_session_endpoint")
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
    client_secret = get_client_secret()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(token_endpoint, headers=headers, data=data)
    result = response.json()
    encoded_id_token = result.get("id_token")
    header = jwt.get_unverified_header(encoded_id_token)
    kid = header.get("kid")
    jwks = get_jwks()
    signing_key = jwt.PyJWKClient.match_kid(jwks, kid)
    if not signing_key:
        logger.warning("Signing key not found.")
        return None
    issuer_url = oidc_metadata["issuer"]
    try:
        id_token = jwt.decode(
            encoded_id_token,
            key=signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer_url,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("JWT is expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warn("JWT validation failed.")
        logger.exception(e)
        return None
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


def get_client_secret():
    """
    Retrieve client secret.
    """
    tstamp = (int(datetime.datetime.today().timestamp()) // 600) * 600
    return _get_client_secret(tstamp)


@lru_cache(maxsize=10)
def _get_client_secret(tstamp):
    secret_name = os.environ["OIDC_CLIENT_SECRET_ARN"]
    secret = get_secret_string(secret_name)
    return secret


def get_jwks():
    """
    Retrieve JWKS (JSON Web Keys).
    """
    tstamp = (int(datetime.datetime.today().timestamp()) // 600) * 600
    return _get_jwks(tstamp)


@lru_cache(maxsize=10)
def _get_jwks(tstamp):
    """
    Cached implementation of fetching JWKS.
    """
    metadata = get_oidc_metadata()
    jwks_uri = metadata["jwks_uri"]
    response = requests.get(jwks_uri)
    result = response.json()
    jwks = jwt.PyJWKSet.from_dict(result)
    return jwks
