import boto3


def on_update(zappa_cli):
    """
    When the app is updated via the Zappa CLI, call this function.
    """
    if zappa_cli.domain is None:
        return
    print(f"DOMAIN: '{zappa_cli.domain}'")
    client = boto3.client("apigateway")
    client.update_domain_name(
        domainName=zappa_cli.domain,
        patchOperations=[
            {
                "op": "replace",
                "path": "/securityPolicy",
                "value": "SecurityPolicy_TLS13_2025_EDGE",
            },
            {"op": "replace", "path": "/endpointAccessMode", "value": "STRICT"},
        ],
    )
