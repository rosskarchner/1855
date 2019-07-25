import os
import json

import boto3
from cfn_custom_resource import lambda_handler, create, update, delete

s3 = boto3.resource("s3")


def create_or_update(event):
    blog_config = event["ResourceProperties"].copy()
    bucket_name = blog_config.pop("S3Bucket")

    if "ServiceToken" in blog_config:
        del blog_config["ServiceToken"]

    if "FunctionVersion" in blog_config:
        del blog_config["FunctionVersion"]

    bucket = s3.Bucket(bucket_name)
    config_key = "_config/blog.json"
    resource_id = "s3://%s/%s" % (bucket_name, config_key)

    bucket.put_object(Key=config_key, Body=json.dumps(blog_config))

    return resource_id, blog_config


@create()
def create(event, context):
    return create_or_update(event)


@update()
def update(event, context):
    return create_or_update(event)


@delete()
def delete(event, context):
    return
