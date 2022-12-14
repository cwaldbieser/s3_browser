import os


def create_content_security_policy():
    """
    Create site wide content security policy.
    """
    aws_region = os.environ["AWS_REGION"]
    bucket_name = os.environ["S3_BUCKET"]
    csp = {
        "default-src": [
            "'self'",
        ],
        "script-src": [
            "'self'",
            "'unsafe-eval'",
            "cdn.datatables.net",
            "cdn.jsdelivr.net",
            "cdnjs.cloudflare.com",
            "code.jquery.com",
            "maxcdn.bootstrapcdn.com",
        ],
        "style-src": [
            "'self'",
            "cdn.datatables.net",
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
        "connect-src": [
            "'self'",
            "{}.s3.{}.amazonaws.com".format(bucket_name, aws_region),
        ],
        "frame-src": [
            "'self'",
        ],
    }
    return csp
