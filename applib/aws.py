import boto3
from logzero import logger


def get_aws_credentials():
    """
    Assume a dedicated role and return temporary credentials.
    """
    client = boto3.client("sts")
    response = client.assume_role(
        RoleArn="arn:aws:iam::758816453596:role/S3BrowserDownloadRole",
        RoleSessionName="downloader",
        DurationSeconds=900,  # Minimum duration
    )
    logger.debug(response)
    credentials = response["Credentials"]
    access_key_id = credentials["AccessKeyId"]
    secret_access_key = credentials["SecretAccessKey"]
    session_token = credentials["SessionToken"]
    return access_key_id, secret_access_key, session_token
