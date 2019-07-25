import os

import json

import boto3


s3 = boto3.resource("s3")
sfn = boto3.client("stepfunctions")


def lambda_handler(event, context):
    print(event)

    # we are only watching one bucket, and aren't too concerned which *which*
    # file under _config has changed. So, let's just get the last record.
    record = event["Records"][-1]
    bucket_name = record["s3"]["bucket"]["name"]
    blog_config_obj = s3.Object(bucket_name, "_config/blog.json")
    blog_config_json = blog_config_obj.get()["Body"].read().decode("utf-8")
    blog_config = json.loads(blog_config_json)
    sfn.start_execution(stateMachineArn=os.environ["STATEMACHINE_ARN"])
