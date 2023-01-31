
S3 Browser
==========

A simple application for browsing and performing basic file operations on
objects in an S3 bucket.  Operations supported are:

* list files
* create folder
* remove folder
* download file
* upload file
* remove file

These permissions can be configured on a per-user basis.

Deployment
----------

- Create a secret in the target account for the application secret.
- Deploy auxilliary templates.
- Update zappa_settings.json.
- Deploy zappa app.
- Update zappa app.
- update auxilliary templates.

Create Application Secret
"""""""""""""""""""""""""

A long string of high entropy characters.
An easy way to generate it:

.. code::python

   > import secrets
   > secrets.token_hex()

Deploy Auxilliary Templates
"""""""""""""""""""""""""""

$CONFIG_FILE is the name of your config file in TOML format.

- Change folders into the `cfn` folder.
- Edit the `cfn/$CONFIG_FILE`.
- Edit `application` -> `project` and `application` -> `stack description`.
- Edit the `secrets.app_secret` ARN with the ARN of the secret from the
  previous section.
- Edit the `s3.bucket_arn` setting with the ARN of the target S3 bucket.
- Edit any logging settings as appropriate.  The log group won't exist before you deploy with Zappa.
- Update the `alarm_description`.

Run the `make_template.py` script to generate the CloudFormation template.

.. code::sh

   $ ./make_template.py --bootstrap configs/$CONFIG_FILE | tee /tmp/template.yml

The resulting template can be used to deploy a stack in CloudFormation.

Update zappa_settings.json
""""""""""""""""""""""""""

- alter stage name (e.g. "dev" -> "stage").
- edit APP_SECRET with secret name (not full ARN).
- edit the CAS_LOGIN_URL, CAS_LOGOUT_URL, and CAS_SERVICE_VALIDATE_URL.
- edit the S3BROWSER_ENTITLEMENT_PREFIX.
- edit S3_BUCKET with bucket name (not full ARN).
- `s3_bucket` setting must be the name of a code deploy bucket.
- edit other settings as appropriate.
- set CAS_SERVICE_URL to "https://www.example.net/login", this will need to be
  updated after initial deployment.
- update the `project_name`.
- optionally set environment variable `FRIENDLY_BUCKET` to a friendly bucket
  name.
- edit role and policy ARNs with resources created in previous section.
    - S3_ROLE_ARN - use the S3AssumedRole
    - DOWNLOAD_POLICY_ARN - use the S3DownloadPolicy
    - UPLOAD_POLICY_ARN - use the S3UploadPolicy
    - role_arn - Use the LambdaExecRole

Deploy Zappa App
""""""""""""""""

.. code::sh

   $ zappa deploy $STAGE

Update Zappa App
""""""""""""""""

Using the URL produced during the previous step, update the "CAS_SERVICE_URL"
to be the base URL plus the "login" resource.  E.g.
"https://$SOME_RANDOM_CHARS.execute-api.$REGION_CODE.amazonaws.com/$STAGE/login"

Then:

.. code::sh

   $ zappa update $STAGE

This sets the correct callback URL for CAS authentication.

Update Auxilliary Templates
"""""""""""""""""""""""""""

Run the `make_template.py` script to generate the CloudFormation template.

.. code::sh

   $ ./make_template.py configs/$CONFIG_FILE | tee /tmp/template.yml

The resulting template can be used to replace the current template in the
auxilliary stack.  It will add alarms and notifications.

Target S3 Bucket CORS
=====================

CORS must be configured on the target bucket:

.. code::json

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
