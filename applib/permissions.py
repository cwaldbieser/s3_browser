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
