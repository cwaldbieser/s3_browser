import os

import boto3
from flask import session
from logzero import logger

from applib.permissions import download_file, has_permission, upload_file


def get_aws_credentials():
    """
    Assume a dedicated role and return temporary credentials.
    """
    username = session["identity"]["sub"]
    role_arn = get_arn_from_env("S3_ROLE_ARN")
    policy_arns = []
    if has_permission(download_file):
        download_policy_arn = get_arn_from_env("DOWNLOAD_POLICY_ARN")
        policy_arns.append({"arn": download_policy_arn})
    if has_permission(upload_file):
        upload_policy_arn = get_arn_from_env("UPLOAD_POLICY_ARN")
        policy_arns.append({"arn": upload_policy_arn})
    logger.debug(
        "Policy ARNs for temporary credentials for `{}`: {}.".format(
            username, policy_arns
        )
    )
    if len(policy_arns) > 0:
        client = boto3.client("sts")
        response = client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=username,
            DurationSeconds=900,  # Minimum duration
            PolicyArns=policy_arns,
        )
        logger.debug(response)
        credentials = response["Credentials"]
        access_key_id = credentials["AccessKeyId"]
        secret_access_key = credentials["SecretAccessKey"]
        session_token = credentials["SessionToken"]
    else:
        access_key_id = "no permissions"
        secret_access_key = "no permissions"
        session_token = "no permissions"
    return access_key_id, secret_access_key, session_token


def get_arn_from_env(symbol):
    """
    Return an ARN from and environment variable.
    """
    arn = os.environ.get(symbol)
    message = "You must set the environment variable `{}`.".format(symbol)
    assert arn is not None, Exception(message)
    return arn
