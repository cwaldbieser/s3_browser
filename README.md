S3 Browser
==========

A simple application for browsing and performing basic file operations
on objects in an S3 bucket. Operations supported are:

-   list files
-   create folder
-   remove folder
-   download file
-   upload file
-   remove file

These permissions can be configured on a per-user basis.

Deployment
----------

-   Create a secret in the target account for the application secret.
-   Deploy auxilliary templates.
-   Update zappa\_settings.json.
-   Deploy zappa app.
-   Update zappa app.
-   update auxilliary templates.

### Create Application Secret

A long string of high entropy characters. An easy way to generate it:

``` {.python}
> import secrets
> secrets.token_hex()
```

### Deploy Auxilliary Templates

\$CONFIG\_FILE is the name of your config file in TOML format.

-   Change folders into the [cfn]{.title-ref} folder.
-   Edit the [cfn/\$CONFIG\_FILE]{.title-ref}.
-   Edit [application]{.title-ref} -\> [project]{.title-ref} and
    [application]{.title-ref} -\> [stack description]{.title-ref}.
-   Edit the [secrets.app\_secret]{.title-ref} ARN with the ARN of the
    secret from the previous section.
-   Edit the [s3.bucket\_arn]{.title-ref} setting with the ARN of the
    target S3 bucket.
-   Edit any logging settings as appropriate. The log group won\'t exist
    before you deploy with Zappa.
-   Update the [alarm\_description]{.title-ref}.

Run the [make\_template.py]{.title-ref} script to generate the
CloudFormation template.

``` {.sh}
$ ./make_template.py --bootstrap configs/$CONFIG_FILE | tee /tmp/template.yml
```

The resulting template can be used to deploy a stack in CloudFormation.

### Update zappa\_settings.json

-   alter stage name (e.g. \"dev\" -\> \"stage\").

-   edit APP\_SECRET with secret name (not full ARN).

-   edit the CAS\_LOGIN\_URL, CAS\_LOGOUT\_URL, and
    CAS\_SERVICE\_VALIDATE\_URL.

-   edit the S3BROWSER\_ENTITLEMENT\_PREFIX.

-   edit S3\_BUCKET with bucket name (not full ARN).

-   [s3\_bucket]{.title-ref} setting must be the name of a code deploy
    bucket.

-   edit other settings as appropriate.

-   set CAS\_SERVICE\_URL to \"<https://www.example.net/login>\", this
    will need to be updated after initial deployment.

-   update the [project\_name]{.title-ref}.

-   optionally set environment variable [FRIENDLY\_BUCKET]{.title-ref}
    to a friendly bucket name.

-   

    edit role and policy ARNs with resources created in previous section.

    :   -   S3\_ROLE\_ARN - use the S3AssumedRole
        -   DOWNLOAD\_POLICY\_ARN - use the S3DownloadPolicy
        -   UPLOAD\_POLICY\_ARN - use the S3UploadPolicy
        -   role\_arn - Use the LambdaExecRole

### Deploy Zappa App

``` {.sh}
$ zappa deploy $STAGE
```

### Update Zappa App

Using the URL produced during the previous step, update the
\"CAS\_SERVICE\_URL\" to be the base URL plus the \"login\" resource.
E.g.
\"<https://$SOME_RANDOM_CHARS.execute-api.$REGION_CODE.amazonaws.com/stage/login>\"

Then:

``` {.sh}
$ zappa update $STAGE
```

This sets the correct callback URL for CAS authentication.

### Update Auxilliary Templates

Run the [make\_template.py]{.title-ref} script to generate the
CloudFormation template.

``` {.sh}
$ ./make_template.py configs/$CONFIG_FILE | tee /tmp/template.yml
```

The resulting template can be used to replace the current template in
the auxilliary stack. It will add alarms and notifications.

Target S3 Bucket CORS
=====================

CORS must be configured on the target bucket:

``` {.json}
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "GET",
            "PUT"
        ],
        "AllowedOrigins": [
            "*"
        ],
        "ExposeHeaders": []
    }
]
```
