#! /usr/bin/env python

import argparse
import sys

import toml
from awacs.aws import Action, Allow, PolicyDocument, Principal, Statement
from troposphere import GetAtt, Ref, Template
from troposphere import cloudwatch as cw
from troposphere import logs as cwlogs
from troposphere import sns
from troposphere.iam import ManagedPolicy, Role


def main(args):
    """
    Create a CloudFormation template.
    """
    config = load_config(args.config_file)
    t = Template()
    t.set_description(config["application"]["stack_description"])
    params = create_parameters(t)
    resources = create_resources(t, config, params, bootstrap=args.bootstrap)
    create_outputs(t, resources)
    if args.json:
        print(t.to_json(), file=args.outfile)
    else:
        print(t.to_yaml(), file=args.outfile)


def snake2camel(identifier):
    """
    Convert snake_case to camel case.
    """
    parts = identifier.split("_")
    new_parts = [p.title() for p in parts]
    return "".join(new_parts)


def config2bool(s):
    """
    Convert user input to a boolean value.
    True, true, t, y, 1 => True
    False, false, f, n, 0 => True
    """
    s = s.strip().lower()
    if s.startswith("t"):
        return True
    elif s.startswith("y"):
        return True
    elif s == "1":
        return True
    elif s.startswith("f"):
        return False
    elif s.startswith("n"):
        return False
    elif s == "0":
        return False
    else:
        raise Exception("Ambiguous True/False value, {}".format(s))


def load_config(config_path):
    """
    Load the configuration.
    """
    with open(config_path, "r") as f:
        config = toml.load(f)
    return config


def make_s3_assumed_role(t, lambda_exec_role):
    """
    Create role that will be assumed by JS SDK to access S3.
    """
    role = Role(
        "S3AssumedRole",
        AssumeRolePolicyDocument=PolicyDocument(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[Action("sts", "AssumeRole")],
                    Principal=Principal(
                        "AWS",
                        [
                            GetAtt(lambda_exec_role, "Arn"),
                        ],
                    ),
                )
            ]
        ),
    )
    t.add_resource(role)
    return role


def get_bucket_policy_resource(config):
    """
    Compute bucket resource for use in IAM policies.
    """
    bucket_arn = config["s3"]["bucket_arn"]
    bucket_prefix = config["s3"].get("bucket_prefix", "")
    if bucket_prefix == "":
        bucket_resource = "{}/*".format(bucket_arn)
    else:
        bucket_resource = "{}/{}/*".format(bucket_arn, bucket_prefix)
    return bucket_resource


def make_s3_upload_policy(t, config, role):
    """
    Create policy that will be used to grant upload permissions.
    """
    bucket_resource = get_bucket_policy_resource(config)
    policy = ManagedPolicy(
        "S3UploadPolicy",
        PolicyDocument=PolicyDocument(
            Version="2012-10-17",
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("s3", "PutObject"),
                    ],
                    Resource=[bucket_resource],
                ),
            ],
        ),
        Roles=[Ref(role)],
    )
    t.add_resource(policy)
    return policy


def make_s3_download_policy(t, config, role):
    """
    Create policy that will be used to grant download permissions.
    """
    bucket_resource = get_bucket_policy_resource(config)
    policy = ManagedPolicy(
        "S3DownloadPolicy",
        PolicyDocument=PolicyDocument(
            Version="2012-10-17",
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("s3", "GetObject"),
                    ],
                    Resource=[bucket_resource],
                ),
            ],
        ),
        Roles=[Ref(role)],
    )
    t.add_resource(policy)
    return policy


def make_lambda_exec_role(t):
    role = Role(
        "LambdaExecRole",
        AssumeRolePolicyDocument=PolicyDocument(
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[Action("sts", "AssumeRole")],
                    Principal=Principal(
                        "Service",
                        [
                            "apigateway.amazonaws.com",
                            "events.amazonaws.com",
                            "lambda.amazonaws.com",
                        ],
                    ),
                )
            ]
        ),
    )
    t.add_resource(role)
    return role


def make_lambda_exec_policy(t, config, role):
    """
    Make policies that grant Lambda exec privs.
    """
    bucket_arn = config["s3"]["bucket_arn"]
    bucket_resource = get_bucket_policy_resource(config)
    secrets = config["secrets"]
    secret_arns = list(secrets.values())
    policy = ManagedPolicy(
        "LambdaExecPolicy",
        PolicyDocument=PolicyDocument(
            Version="2012-10-17",
            Statement=[
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("logs", "CreateLogGroup"),
                        Action("logs", "CreateLogStream"),
                        Action("logs", "PutLogEvents"),
                    ],
                    Resource=["arn:aws:logs:*:*:*"],
                ),
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("lambda", "InvokeFunction"),
                    ],
                    Resource=["*"],
                ),
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("s3", "ListBucket"),
                    ],
                    Resource=[bucket_arn],
                ),
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("s3", "PutObject"),
                        Action("s3", "DeleteObject"),
                    ],
                    Resource=[bucket_resource],
                ),
                Statement(
                    Effect=Allow,
                    Action=[
                        Action("secretsmanager", "GetSecretValue"),
                    ],
                    Resource=secret_arns,
                ),
            ],
        ),
        Roles=[Ref(role)],
    )
    t.add_resource(policy)
    return policy


def create_parameters(t):
    """
    Create the CloudFormation parameters.
    Return a mapping of params.
    """
    return dict()


def create_sns_topic(t, config, topic_id):
    """
    Create an SNS topic for workflow notifications.
    """
    topic = sns.Topic(
        "AlarmTopic",
    )
    t.add_resource(topic)
    return topic


def create_log_alarms(t, config, topic):
    """
    Create alarms on logs.
    """
    alarms_cfg = config.get("log_alarms", {})
    for alarm_name, alarm_cfg in alarms_cfg.items():
        create_log_alarm(t, config, alarm_name, alarm_cfg, topic)


def create_log_alarm(t, config, alarm_name, alarm_cfg, topic):
    """
    Create a log alarm.
    """
    logical_name = "{}LogAlarm".format(snake2camel(alarm_name))
    kwargs = {}
    for key, value in alarm_cfg.items():
        if key in {"log_group", "filter_pattern"}:
            continue
        kwargs[snake2camel(key)] = value
    metric_namespace = alarm_cfg.get("namespace")
    assert metric_namespace is not None, Exception(
        "Log alarm `{}` requires a `namespace`.".format(alarm_name)
    )
    log_group = alarm_cfg.get("log_group")
    assert log_group is not None, Exception(
        "Log alarm `{}` requires a `log_group`.".format(alarm_name)
    )
    filter_pattern = alarm_cfg.get("filter_pattern")
    assert filter_pattern is not None, Exception(
        "Log alarm `{}` requires a `filter_pattern`.".format(alarm_name)
    )
    metric_filter = create_metric_filter(
        t, config, alarm_name, log_group, filter_pattern, metric_namespace
    )
    kwargs["MetricName"] = metric_filter.MetricTransformations[0].MetricName
    alarm = cw.Alarm(logical_name, AlarmActions=[Ref(topic)], **kwargs)
    t.add_resource(alarm)
    return alarm


def create_metric_filter(
    t, config, filter_name, log_group, filter_pattern, metric_namespace
):
    """
    Create a metric filter.
    """
    logical_name = "{}MetricFilter".format(snake2camel(filter_name))
    metric_name = "{}Metric".format(snake2camel(filter_name))
    metric_filter = cwlogs.MetricFilter(
        logical_name,
        FilterPattern=filter_pattern,
        LogGroupName=log_group,
        MetricTransformations=[
            cwlogs.MetricTransformation(
                MetricValue="1",
                MetricNamespace=metric_namespace,
                MetricName=metric_name,
            )
        ],
    )
    t.add_resource(metric_filter)
    return metric_filter


def create_resources(t, config, params, bootstrap=False):
    """
    Create CloudFormation resources and return a mapping of those.  See
    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html
    """
    role = make_lambda_exec_role(t)
    assumed_role = make_s3_assumed_role(t, role)
    make_s3_upload_policy(t, config, assumed_role)
    make_s3_download_policy(t, config, assumed_role)
    make_lambda_exec_policy(t, config, role)
    if not bootstrap:
        alarm_topic = create_sns_topic(t, config, "s3browser_alarms_topic")
        create_log_alarms(t, config, alarm_topic)


def create_outputs(t, resources):
    """
    Create CloudFormation outputs.
    """
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create S3Browser aux resource stack.")
    parser.add_argument("config_file", action="store", help="Configuration file")
    parser.add_argument(
        "-j", "--json", action="store_true", help="Output JSON instead of YAML."
    )
    parser.add_argument(
        "-o",
        "--outfile",
        action="store",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="Output file.  Use `-` for STDOUT.",
    )
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Create resources needed to bootstrap the Zappa deployment.",
    )
    args = parser.parse_args()
    main(args)
