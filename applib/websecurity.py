def create_content_security_policy():
    """
    Create site wide content security policy.
    """
    csp = {
        "default-src": [
            "'self'",
        ],
        "script-src": [
            "'self'",
            "code.jquery.com",
            "cdnjs.cloudflare.com",
            "maxcdn.bootstrapcdn.com",
            "cdn.jsdelivr.net",
        ],
        "style-src": [
            "'self'",
            "maxcdn.bootstrapcdn.com",
            "use.fontawesome.com",
        ],
        "font-src": [
            "use.fontawesome.com",
        ],
        "img-src": [
            "data:",
            "maxcdn.bootstrapcdn.com",
        ],
    }
    return csp
