import os
import urllib

import requests
from flask import abort, redirect, request, session, url_for
from logzero import logger
from lxml import etree

from applib.permissions import get_default_permissions


def sso_logout():
    """
    Return the SSO logout response.
    """
    cas_logout_url = os.environ.get("CAS_LOGOUT_URL")
    if cas_logout_url is not None:
        return redirect(cas_logout_url)
    return redirect(url_for("index"))


def authenticate():
    """
    Authenticates a user with CAS SSO. On success, an ID token is stored in the
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
    ticket = request.args.get("ticket", None)
    has_service_ticket = ticket is not None
    logger.debug("Has service ticket? {}".format(has_service_ticket))
    # Redirect to get ticket if not presenting one
    if not has_service_ticket:
        cas_login_url = os.environ.get("CAS_LOGIN_URL")
        assert (
            cas_login_url is not None
        ), "You must provide environment variable `CAS_LOGIN_URL`."
        cas_service_url = make_service_url()
        qs_map = dict(service=cas_service_url)
        qs = urllib.parse.urlencode(qs_map)
        url = "{}?{}".format(cas_login_url, qs)
        logger.debug("Redirecting to CAS to get service ticket: {}".format(url))
        return redirect(url)
    # Validate ticket
    logger.debug("Validating service ticket {}...".format(ticket[:10]))
    is_valid, user, attributes = validate_service_ticket(ticket)
    if not is_valid:
        abort(401)
    # Success!  Log user in.
    logger.debug("Service ticket was valid.")
    logger.debug("User is '{}'.".format(user))
    identity = {
        "sub": user,
        "family_name": None,
        "given_name": None,
        "permissions": get_default_permissions(),
    }
    logger.debug("Attributes from CAS: {}".format(attributes))
    session["identity"] = identity
    map_permissions(attributes)
    map_attributes(attributes)
    logger.debug("CAS authentication successful for '{}'.".format(user))
    session["username"] = user
    logger.debug("Application identity: {}".format(identity))
    return redirect(url_for("browse", subpath="top"))


def make_service_url():
    """
    Make the service URL CAS will use to redirect the browser back to this service.
    """
    cas_service_url = os.environ.get("CAS_SERVICE_URL")
    assert (
        cas_service_url is not None
    ), "You must provide environment variable `CAS_SERVICE_URL`."
    return cas_service_url


def validate_service_ticket(ticket):
    """
    Validate a CAS service ticket.

    Returns (is_valid, user, attribs).
    `is_valid` - boolean
    `attribs` - set of attribute-value tuples.
    """
    cas_service_validate_url = os.environ.get("CAS_SERVICE_VALIDATE_URL")
    assert (
        cas_service_validate_url is not None
    ), "You must provide environment variable `CAS_SERVICE_VALIDATE_URL`."
    service = make_service_url()
    params = dict(service=service, ticket=ticket)
    logger.debug("Validate URL: {}".format(cas_service_validate_url))
    r = requests.get(cas_service_validate_url, params=params)
    if not r.status_code == requests.codes.ok:
        logger.debug(
            "Validation request was unsuccessful: {} - {}".format(r.status_code, r.text)
        )
        return (False, None, None)
    parser = etree.XMLParser()
    root = etree.fromstring(r.text, parser=parser)
    auth_result_elm = root[0]
    is_success = etree.QName(auth_result_elm).localname == "authenticationSuccess"
    if not is_success:
        return (False, None, None)
    user_elm = find_child_element(auth_result_elm, "user")
    user = user_elm.text.lower()
    attrib_results = set([])
    attribs = find_child_element(auth_result_elm, "attributes")
    if attribs is None:
        attribs = []
    for attrib in attribs:
        name = etree.QName(attrib).localname
        value = attrib.text
        attrib_results.add((name, value))
    return (True, user, attrib_results)


def find_child_element(elm, child_local_name):
    """
    Find an XML child element by local tag name.
    """
    for n in range(len(elm)):
        child_elm = elm[n]
        tag = etree.QName(child_elm)
        if tag.localname == child_local_name:
            return child_elm
    return None


def map_permissions(attributes):
    """
    Map entitlement attributes to permissions in the application.
    """
    default_prefix = "https://s3browser.example.net/example_bucket/permissions"
    entitlement_prefix = os.environ.get("S3BROWSER_ENTITLEMENT_PREFIX", default_prefix)
    permissions = session["identity"]["permissions"]
    for k, v in attributes:
        if k.lower() == "edupersonentitlement":
            entitlement = v.lower()
            if entitlement.startswith(entitlement_prefix):
                p = urllib.parse.urlparse(entitlement)
                qs = urllib.parse.parse_qs(p.query)
                for param, values in qs.items():
                    if param in permissions:
                        if len(values) == 1:
                            action_str = values[0]
                            action = parse_permission_action(values[0])
                            if action in (True, False):
                                permissions[param] = action
                            else:
                                message = (
                                    "Could not map permission `{}` action `{}`"
                                    " for entitlement `{}`."
                                ).format(param, action_str, entitlement)
                                logger.warning(message)


def parse_permission_action(value):
    """
    Convert permission actions in True, False, or None.
    True - allow permission
    False - deny permission
    None - invalid value.
    """
    if value == "allow":
        return True
    elif value == "deny":
        return False
    else:
        return None


def map_attributes(attributes):
    """
    Map attributes to user session.
    """
    identity = session["identity"]
    for attrib_name, attrib_value in attributes:
        if attrib_name.lower() == "givenname":
            identity["given_name"] = attrib_value
        if attrib_name.lower() in ("surname", "sn"):
            identity["family_name"] = attrib_value
