import os
from urllib.parse import unquote_plus

import boto3
from logzero import logger


def resource_to_bucket_path(path, force_endslash=True):
    """
    Convert the web path to the bucket path.
    """
    bucket_root = os.environ.get("BUCKET_ROOT", "")
    if bucket_root.endswith("/"):
        bucket_root = bucket_root[:-1]
    if not path.endswith("/") and force_endslash:
        path = path + "/"
    top, subpath = path.split("/", 1)
    if top != "top":
        message = "Subpath did not start with `top`: `{}`".format(path)
        logger.warn(message)
        raise Exception(message)
    if bucket_root == "":
        bucket_path = subpath
    else:
        bucket_path = "/".join([bucket_root, subpath])
    logger.debug(
        "subpath: `{}`, bucket_root: `{}`, bucket_path: `{}`".format(
            subpath, bucket_root, bucket_path
        )
    )
    return bucket_path


def list_bucket_objects(path):
    """
    List the bucket objects at `path`.
    """
    bucket_name = os.environ.get("S3_BUCKET")
    message = "You must provide the environment variable `S3_BUCKET`."
    assert bucket_name, Exception(message)
    bucket_path = resource_to_bucket_path(path)
    files = []
    folders = []
    objects = {"files": files, "folders": folders}
    client = boto3.client("s3")
    response = client.list_objects_v2(
        Bucket=bucket_name,
        EncodingType="url",
        Prefix=bucket_path,
    )
    contents = response.get("Contents", [])
    bucket_path_len = len(bucket_path)
    for item in contents:
        key = unquote_plus(item["Key"][bucket_path_len:])
        if key == "":
            continue
        last_modified = item["LastModified"]
        size = item["Size"]
        item = {"key": key, "last_modified": last_modified.isoformat(), "size": size}
        if key.endswith("/"):
            folders.append(item)
        elif "/" in key:
            # skip files in subfolders.
            continue
        else:
            files.append(item)
    logger.info(objects)
    return objects
