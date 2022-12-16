import json
import os
from functools import wraps

from flask import redirect, render_template, request, session, url_for
from logzero import logger

from applib.permissions import list_files


def authorize():
    """
    Decorator for Flask routes.
    If a user is not authenticated or not authorized deny access to the resource.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.headers.get("X-Forwarded-For") or request.remote_addr
            if client_ip == "127.0.0.1":
                dev_identity = os.environ.get("APP_DEV_IDENTITY")
                if dev_identity:
                    with open(dev_identity) as fname:
                        try:
                            session["identity"] = json.load(fname)
                        except json.JSONDecodeError:
                            message = (
                                "Could not decode `APP_DEV_IDENTITY` "
                                "environment variable."
                            )
                            logger.warn(message)
                    logger.debug(session["identity"])
            identity = session.get("identity")
            if identity is None:
                logger.debug(
                    "Client IP {} is not authenticated. Redirecting to login endpoint.".format(
                        client_ip
                    )
                )
                return redirect(url_for("login"))
            username = identity["sub"]
            permissions = identity.get("permissions")
            # Require `list_files` to use the application at all.
            has_permissions = permissions[list_files]
            if not has_permissions:
                logger.debug("App identity: {}".format(identity))
                logger.debug(
                    "User `{}`, client IP {} is not authorized for resource `{}`.".format(
                        username, client_ip, request.path
                    )
                )
                return render_template("403.jinja2"), 403
            return f(*args, **kwargs)

        return decorated_function

    return decorator
