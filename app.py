#! /usr/bin/env python


from flask import Flask, Response, redirect, render_template, session, url_for
from flask_wtf.csrf import CSRFProtect
from logzero import logger

# Enforces permissions at each route.
from applib.authorization import authorize
# Performs authentication; maps attributes to normalized ID token.
from applib.cas import authenticate, sso_logout
from applib.utils import init_flask_app

app = Flask(__name__)


init_flask_app(app)
csrf = CSRFProtect(app)


@app.route("/")
def index():
    logger.debug("Redirecting to `/browse` ...")
    return redirect(url_for("browse"))


@app.route("/css/app.css")
@authorize()
def stylesheet():
    resp = Response(render_template("stylesheet.css"), mimetype="text/css")
    return resp


@app.route("/browse")
@authorize()
def browse():
    return render_template("browse.jinja2")


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


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.jinja2"), 404
