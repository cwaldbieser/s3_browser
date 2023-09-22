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


def list_all_bucket_objects(bucket_name, prefix):
    """
    Generate a sequence of bucket info objects.
    """
    truncated = True
    kwargs = {}
    client = boto3.client("s3")
    while truncated:
        response = client.list_objects_v2(
            Bucket=bucket_name, EncodingType="url", Prefix=prefix, **kwargs
        )
        key_count = response["KeyCount"]
        logger.debug(f"Keys returned in this page: {key_count}")
        contents = response.get("Contents", [])
        for item in contents:
            yield item
        truncated = response["IsTruncated"]
        if truncated:
            kwargs["ContinuationToken"] = response["NextContinuationToken"]


def list_bucket_objects(path):
    """
    List the bucket objects at `path`.
    """
    bucket_name = os.environ.get("S3_BUCKET")
    message = "You must provide the environment variable `S3_BUCKET`."
    assert bucket_name, Exception(message)
    bucket_path = resource_to_bucket_path(path)
    files = []
    folders = set([])
    objects = {"files": files, "folders": folders}
    bucket_path_len = len(bucket_path)
    logger.debug(f"bucket_path: `{bucket_path}`")
    for item in list_all_bucket_objects(bucket_name, bucket_path):
        key = unquote_plus(item["Key"][bucket_path_len:])
        logger.debug(f"Found key `{key}`.")
        if key == "":
            continue
        last_modified = item["LastModified"]
        size = item["Size"]
        item = {"key": key, "last_modified": last_modified.isoformat(), "size": size}
        if key.endswith("/"):
            if "/" in key[:-1]:
                logger.debug(f"Key `{key}` is a folder with one or more subfolders.")
            else:
                logger.debug(f"Key `{key}` is a folder.")
                folders.add(key)
        elif "/" in key:
            parts = key.split("/")
            folders.add("{}/".format(parts[0]))
            logger.debug(
                f"Key `{key}` is a file with embedded folders."
                f"  Adding folder `{parts[0]}`."
            )
            # skip files in subfolders.
            # Only include their topmost folder part.
            continue
        else:
            files.append(item)
    folders = list(folders)
    folders.sort()
    folders = [{"key": k, "last_modified": "", "size": 0} for k in folders]
    objects["folders"] = folders
    logger.info(objects)
    return objects
