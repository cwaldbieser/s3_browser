---
title: S3 Browser
---

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
==========

-   Create a secret in the target account for the application secret.
-   Deploy auxilliary templates.
-   Update zappa\_settings.json.
-   Deploy zappa app.
-   Update zappa app.
-   update auxilliary templates.

Create Application Secret
-------------------------

A long string of high entropy characters. An easy way to generate it:

``` {.sourceCode .python}
> import secrets
> secrets.token_hex()
```

Deploy Auxilliary Templates
---------------------------

\$CONFIG\_FILE is the name of your config file in TOML format.

-   Change folders into the cfn folder.
-   Edit the cfn/\$CONFIG\_FILE.
-   Edit the secrets.app\_secret ARN with the ARN of the secret from the
    previous section.
-   Edit the s3.bucket\_arn setting with the ARN of the target S3
    bucket.
-   Edit any logging settings as appropriate.

Run the make\_template.py script to generate the CloudFormation
template.

``` {.sourceCode .sh}
$ ./make_template.py --bootstrap cfn/$CONFIG_FILE | tee /tmp/template.yml
```

The resulting template can be used to deploy a stack in CloudFormation.

Update zappa\_settings.json
---------------------------

-   alter stage name (e.g. "dev" -&gt; "stage").
-   edit APP\_SECRET with secret name (not full ARN).
-   edit S3\_BUCKET with bucket name (not full ARN).
-   s3\_bucket setting must be the name of a code deploy bucket.
-   edit other settings as appropriate.
-   set CAS\_SERVICE\_URL to "<https://www.example.net/login>", this
    will need to be updated after initial deployment.
-   

    edit role and policy ARNs with resources created in previous section.

    :   -   S3\_ROLE\_ARN - use the S3AssumedRole
        -   DOWNLOAD\_POLICY\_ARN - use the S3DownloadPolicy
        -   UPLOAD\_POLICY\_ARN - use the S3UploadPolicy
        -   role\_arn - Use the LambdaExecRole

Deploy Zappa App
----------------

``` {.sourceCode .sh}
$ zappa deploy stage
```

Update Zappa App
----------------

Using the URL produced during the previous step, update the
"CAS\_SERVICE\_URL" to be the base URL plus the "login" resource. E.g.
"<https://$SOME_RANDOM_CHARS.execute-api.$REGION_CODE.amazonaws.com/stage/login>"

Then:

``` {.sourceCode .sh}
$ zappa update stage
```

This sets the correct callback URL for CAS authentication.

Update Auxilliary Templates
---------------------------

Run the make\_template.py script to generate the CloudFormation
template.

``` {.sourceCode .sh}
$ ./make_template.py cfn/$CONFIG_FILE | tee /tmp/template.yml
```

The resulting template can be used to replace the current template in
the auxilliary stack. It will add alarms and notifications.
