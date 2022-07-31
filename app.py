#! /usr/bin/env python


from flask import Flask, Response, redirect, render_template, session, url_for
from flask_wtf.csrf import CSRFProtect
from logzero import logger

# Enforces permissions at each route.
from applib.authorization import authorize
from applib.bucket import list_bucket_objects
# Performs authentication; maps attributes to normalized ID token.
from applib.cas import authenticate, sso_logout
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
    return resp


@app.route("/browse/<path:subpath>")
@authorize()
def browse(subpath):
    # Remove trailing slash from subpath.
    if subpath.endswith("/"):
        subpath = subpath[:-1]
    logger.info("subpath: {}".format(subpath))
    objects = list_bucket_objects(subpath)
    path_components = make_path_components(subpath)
    return render_template(
        "browse.jinja2",
        bucket_objects=objects,
        path_components=path_components,
        subpath=subpath,
    )


@app.route("/login")
def login():
    return authenticate()


@app.route("/logout")
def logout():
    """
    Logout resource.
    """
    # remove the username from the session if it's there
    logger.log("Logged out.")
    session.clear()
    return sso_logout()


# Not found handler.
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.jinja2"), 404
