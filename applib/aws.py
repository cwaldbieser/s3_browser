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


def delete_file_from_bucket(key):
    """
    Delete a file from the S3 bucket.
    """
    logger.debug("Entered delete_file_from_bucket().")
    if key.endswith("/"):
        return "Bad Request", 400
    bucket_name = os.environ.get("S3_BUCKET")
    bucket_root = os.environ.get("BUCKET_ROOT", "")
    if not key.startswith(bucket_root):
        return "Forbidden", 403
    logger.debug("Deleting bucket: {}, key: {} ...".format(bucket_name, key))
    client = boto3.client("s3")
    resp = client.delete_object(Bucket=bucket_name, Key=key)
    logger.debug("Response from deleting file: {}".format(resp))
    meta = resp["ResponseMetadata"]
    http_status = meta["HTTPStatusCode"]
    return "Response Status", http_status


def files_in_folder(folder):
    """
    Test if files exist in the folder.
    """
    bucket_name = os.environ.get("S3_BUCKET")
    client = boto3.client("s3")
    resp = client.list_objects_v2(
        Bucket=bucket_name,
        Delimiter='/',
        MaxKeys=2,
        Prefix=folder,
    )
    contents = resp.get("Contents", [])
    return len(contents) > 1


def delete_folder_from_bucket(key):
    """
    Delete a folder from the S3 bucket.
    """
    logger.debug("Entered delete_folder_from_bucket().")
    if not key.endswith("/"):
        return "Bad Request", 400
    bucket_name = os.environ.get("S3_BUCKET")
    bucket_root = os.environ.get("BUCKET_ROOT", "")
    if not key.startswith(bucket_root):
        return "Forbidden", 403
    if key == bucket_root:
        return "Forbidden", 403
    if files_in_folder(key):
        return "Cannot delete folder containing files.", 403
    logger.debug("Deleting bucket: {}, key: {} ...".format(bucket_name, key))
    client = boto3.client("s3")
    resp = client.delete_object(Bucket=bucket_name, Key=key)
    logger.debug("Response from deleting file: {}".format(resp))
    meta = resp["ResponseMetadata"]
    http_status = meta["HTTPStatusCode"]
    return "Response Status", http_status


def create_bucket_folder(key):
    """
    Create a bucket folder.
    """
    if not key.endswith("/"):
        return "Bad Request", 400
    bucket_name = os.environ.get("S3_BUCKET")
    bucket_root = os.environ.get("BUCKET_ROOT", "")
    if not key.startswith(bucket_root):
        return "Forbidden", 403
    if key == bucket_root:
        return "Forbidden", 403
    client = boto3.client("s3")
    resp = client.put_object(Bucket=bucket_name, Key=key)
    logger.debug("Response from creating folder: {}".format(resp))
    meta = resp["ResponseMetadata"]
    http_status = meta["HTTPStatusCode"]
    return "Response Status", http_status
