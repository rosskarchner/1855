import json

import boto3
import mf2py

cloudformation = boto3.client("cloudformation")


def outputs_for_cloudformation_stack(stack_id):
    stack = cloudformation.describe_stacks(StackName=stack_id)["Stacks"][0]
    return {o["OutputKey"]: o["OutputValue"] for o in stack["Outputs"]}


def validate_site_subscriber(event):
    me_uri = event["queryStringParameters"]["me"]
    this_domain = event["requestContext"]["domainName"]
    this_path = event["requestContext"]["path"]
    expected_rel_auth = "https://%s%s" % (this_domain, this_path)
    mf2_data = mf2py.parse(url=me_uri)
    return expected_rel_auth == mf2_data["rels"]["authorization_endpoint"][0]
