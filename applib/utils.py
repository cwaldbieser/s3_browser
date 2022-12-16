import logging
import os

import boto3
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
    secret_name = os.environ["APP_SECRET"]
    app.secret_key = get_secret_string(secret_name)


def get_secret_string(secret_name, region="us-east-1"):
    """
    Get secret string by name.
    """
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region,
    )
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response["SecretString"]
    return secret


def make_path_components(subpath):
    """
    Return ...
    """
    path_components = []
    parts = subpath.split("/")
    for n in range(len(parts)):
        component = parts[n]
        pos = n + 1
        full_path = "/".join(parts[:pos])
        path_components.append((component, full_path))
    return path_components
