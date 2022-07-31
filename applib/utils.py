import logging
import os

from flask_talisman import Talisman
from logzero import logger

from applib.websecurity import create_content_security_policy


def is_dev_env():
    """
    Return True if this instance is running in developer mode.
    """
    flask_env = os.environ.get("FLASK_ENV")
    logger.debug("FLASK_ENV={}".format(flask_env))
    return flask_env == "development"


def init_flask_app(app):
    """
    Initialize the Flask app.
    """
    # Configure logging.
    logging.basicConfig(
        level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper())
    )
    # Enable web security headers when not in development mode.
    if not is_dev_env():
        Talisman(app, content_security_policy=create_content_security_policy())
    # Set the secret key to some random bytes. Keep this really secret!
    app.secret_key = get_app_secret()


def get_app_secret():
    """
    TODO: Dynamically fetch secret.
    """
    return "c592c74bbb09cd44ce5f3ca0e3e594fa97235e9304d6a357bed4f52e8ad4a742".encode(
        "utf-8"
    )


def make_path_components(subpath):
    """
    Return ...
    """
    path_components = []
    parts = subpath.split("/")
    for n in range(len(parts)):
        component = parts[n]
        full_path = "/".join(parts[:n+1])
        path_components.append((component, full_path))
    return path_components
