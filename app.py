#! /usr/bin/env python

import os
import uuid

from flask import (Flask, Response, make_response, redirect, render_template,
                   session, url_for)
from flask_wtf.csrf import CSRFProtect
from logzero import logger

# Enforces permissions at each route.
from applib.authorization import authorize
from applib.aws import get_aws_credentials
from applib.bucket import list_bucket_objects, resource_to_bucket_path
# Performs authentication; maps attributes to normalized ID token.
from applib.cas import authenticate, sso_logout
from applib.permissions import download_file, has_permission, upload_file
from applib.utils import init_flask_app, make_path_components

app = Flask(__name__)


init_flask_app(app)
csrf = CSRFProtect(app)


@app.route("/")
def index():
    logger.debug("Redirecting to `/browse` ...")
    return redirect(url_for("browse", subpath="top"))


@app.route("/css/app.css")
@authorize()
def stylesheet():
    resp = Response(render_template("stylesheet.css"), mimetype="text/css")
    resp.headers["Content-Type"] = "text/css; charset=utf-8"
    return resp


@app.route("/browse/<path:subpath>")
@authorize()
def browse(subpath):
    # Remove trailing slash from subpath.
    if subpath.endswith("/"):
        subpath = subpath[:-1]
    bucket_name = os.environ.get("S3_BUCKET")
    logger.info("subpath: {}".format(subpath))
    objects = list_bucket_objects(subpath)
    path_components = make_path_components(subpath)
    bucket_path = resource_to_bucket_path(subpath)
    if bucket_path.endswith("/"):
        bucket_path = bucket_path[:-1]
    allow_download_file = has_permission(download_file)
    allow_upload_file = has_permission(upload_file)
    appconfig_version = str(uuid.uuid4())
    return render_template(
        "browse.jinja2",
        appconfig_version=appconfig_version,
        bucket_name=bucket_name,
        bucket_objects=objects,
        path_components=path_components,
        subpath=subpath,
        bucket_path=bucket_path,
        allow_download_file=allow_download_file,
        allow_upload_file=allow_upload_file,
    )


@app.route("/js/<uuid:version>.js")
@authorize()
def appconfig_js(version):
    access_key_id, secret_access_key, session_token = get_aws_credentials()
    resp = make_response(
        render_template(
            "appconfig.jinja2",
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            session_token=session_token,
        ),
        200,
    )
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return resp


@app.route("/login")
def login():
    return authenticate()


@app.route("/logout")
def logout():
    """
    Logout resource.
    """
    # remove the username from the session if it's there
    username = session["identity"]["sub"]
    logger.info("User `{}` was logged out.".format(username))
    session.clear()
    return sso_logout()


# Not found handler.
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.jinja2"), 404
