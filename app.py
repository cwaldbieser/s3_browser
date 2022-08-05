#! /usr/bin/env python

import os
import uuid

from flask import (Flask, Response, make_response, redirect, render_template,
                   request, session, url_for)
from flask_wtf.csrf import CSRFProtect
from logzero import logger

# Enforces permissions at each route.
from applib.authorization import authorize
from applib.aws import (create_bucket_folder, delete_file_from_bucket,
                        delete_folder_from_bucket, get_aws_credentials)
from applib.bucket import list_bucket_objects, resource_to_bucket_path
# Performs authentication; maps attributes to normalized ID token.
from applib.cas import authenticate, sso_logout
from applib.permissions import (create_folder, download_file, has_permission,
                                remove_file, remove_folder, upload_file)
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


@app.route("/browse/<path:subpath>", methods=["GET", "DELETE", "PUT"])
@authorize()
def browse(subpath):
    if request.method == "DELETE":
        resp = __browse_DELETE(subpath)
    elif request.method == "PUT":
        resp = __browse_PUT(subpath)
    else:
        resp = __browse_GET(subpath)
    return resp


def __browse_GET(subpath):
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
    allow_remove_file = has_permission(remove_file)
    allow_remove_folder = has_permission(remove_folder)
    allow_create_folder = has_permission(create_folder)
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
        allow_remove_file=allow_remove_file,
        allow_remove_folder=allow_remove_folder,
        allow_create_folder=allow_create_folder,
    )


def __browse_DELETE(subpath):
    # bucket_name = os.environ.get("S3_BUCKET")
    allow_remove_file = has_permission(remove_file)
    allow_remove_folder = has_permission(remove_folder)
    if not (allow_remove_file or allow_remove_folder):
        return "Forbidden", 403
    key = resource_to_bucket_path(subpath, force_endslash=False)
    is_folder = key.endswith("/")
    is_file = not is_folder
    if not allow_remove_folder and is_folder:
        return "Forbidden", 403
    if not allow_remove_file and is_file:
        return "Forbidden", 403
    logger.debug("bucket path: {}".format(key))
    if is_file:
        return delete_file_from_bucket(key)
    if is_folder:
        return delete_folder_from_bucket(key)
    return "Bad Request", 400


def __browse_PUT(subpath):
    key = resource_to_bucket_path(subpath)
    logger.debug("New folder: {}".format(key))
    return create_bucket_folder(key)


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
