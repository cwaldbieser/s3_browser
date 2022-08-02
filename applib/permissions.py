from flask import session
from logzero import logger

# Permissions enumerated.
list_files = "list_files"
create_folder = "create_folder"
remove_folder = "remove_folder"
download_file = "download_file"
upload_file = "upload_file"
remove_file = "remove_file"
permission_set = set(
    [list_files, create_folder, remove_folder, download_file, upload_file, remove_file]
)


def get_default_permissions():
    """
    Return default permissions.
    """
    permissions = {
        "list_files": False,
        "create_folder": False,
        "remove_folder": False,
        "download_file": False,
        "upload_file": False,
        "remove_file": False,
    }
    return permissions


def has_permission(perm):
    """
    Does the current session have the permission?
    """
    if perm not in permission_set:
        logger.warn("Check for invalid permission `{}`.".format(perm))
        return False
    identity = session.get("identity")
    if identity is None:
        return False
    permissions = identity.get("permissions")
    if permissions is None:
        logger.warn("Session has identity by no permissions structure.")
        return False
    return bool(permissions.get(perm))
