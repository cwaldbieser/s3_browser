import boto3


def on_update(zappa_cli):
    """
    When the app is updated via the Zappa CLI, call this function.
    """
    if zappa_cli.domain is None:
        return
    print("DOMAIN: `{}`".format(zappa_cli.domain))
    client = boto3.client("apigateway")
    client.update_domain_name(
        domainName=zappa_cli.domain,
        patchOperations=[
            {"op": "replace", "path": "/securityPolicy", "value": "TLS_1_2"},
        ],
    )
