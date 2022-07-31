def create_content_security_policy():
    """
    Create site wide content security policy.
    """
    csp = {
        "default-src": [
            "'self'",
        ],
    }
    return csp
