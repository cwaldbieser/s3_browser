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
        "connect-src": [
            "{}.s3.{}.amazonaws.com".format(bucket_name, aws_region),
        ],
        "frame-src": [
            "jimmywarting.github.io",
        ],
    }
    return csp
