import codecs
import json
import os

import boto3

import chevron


s3 = boto3.client("s3")
template_path = os.path.join(os.path.dirname(__file__), "template.mustache")


def render_hfeed_page(event, context):
    print(event)

    bucket_name = os.environ["BUCKET_NAME"]
    blog_config_obj = s3.get_object(Bucket=bucket_name, Key="_config/blog.json")
    blog_config_json = blog_config_obj["Body"].read().decode("utf-8")
    blog_config = json.loads(blog_config_json)

    # todo: allow users to override with a template in the S3 bucket
    template = codecs.open(template_path, encoding="utf8")

    rendered = chevron.render(template, blog_config)
    s3.put_object(
        Bucket=bucket_name,
        Body=rendered,
        Key="index.html",
        ACL="public-read",
        ContentType="text/html; charset=utf-8",
    )
