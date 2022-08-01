
import os

import boto3
from logzero import logger


def get_aws_credentials():
    """
    Assume a dedicated role and return temporary credentials.
    """
    role_arn = os.environ.get("S3_DOWNLOAD_ROLE_ARN")
    message = "You must set the environment variable `S3_DOWNLOAD_ROLE_ARN`."
    assert role_arn is not None, Exception(message)
    client = boto3.client("sts")
    response = client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="downloader",
        DurationSeconds=900,  # Minimum duration
    )
    logger.debug(response)
    credentials = response["Credentials"]
    access_key_id = credentials["AccessKeyId"]
    secret_access_key = credentials["SecretAccessKey"]
    session_token = credentials["SessionToken"]
    return access_key_id, secret_access_key, session_token
