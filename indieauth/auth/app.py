import json
import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlencode, urljoin

import requests

import jwt
from tokens import authorization_state_token
from utils import outputs_for_cloudformation_stack, validate_site_subscriber

COGNITO_BASE_URL = os.environ["UserPoolURL"]

STACK_OUTPUTS = outputs_for_cloudformation_stack(os.environ["StackID"])


def cognito_url(path):
    return urljoin(COGNITO_BASE_URL, path)


def auth_handler(event, context):
    """ this is the incoming request from an indieauth client. 
    Stash the incoming query parameters into a JWT, and redirect
    to the Cognito login UI using that JWT as the "state" paramteter
    """

    if validate_site_subscriber(event):

        state_token = authorization_state_token(event["queryStringParameters"])
        print(event)
        print(context)
        upstream_endpoint = cognito_url("/oauth2/authorize")
        upstream_params = {}
        upstream_params["client_id"] = os.environ["UserPoolClientID"]
        upstream_params["response_type"] = "code"
        upstream_params["redirect_uri"] = STACK_OUTPUTS["CallbackEndpoint"]
        upstream_params["state"] = state_token
        return {
            "statusCode": 302,
            "headers": {
                "Location": upstream_endpoint + "?" + urlencode(upstream_params)
            },
        }
    else:

        return {
            "statusCode": 400,
            "body": "This site doesn't seem to belong to this subscriber",
        }


def auth_code_check(event, context):
    form_params = parse_qs(event["body"])
    authorization_code = form_params["code"][0]
    incoming_client_id = form_params["client_id"][0]
    incoming_redirect_uri = form_params["redirect_uri"][0]

    payload = jwt.decode(authorization_code, "secret", algorithm="HS256")

    if (
        incoming_client_id == payload["client_id"]
        and incoming_redirect_uri == payload["redirect_uri"]
    ):
        return {"body": json.dumps({"me": payload["me"]})}


def token():
    #    form_params = parse_qs(app.current_request.raw_body.decode())
    #    authorization_code = form_params['code'][0]
    #    original_request = json.loads(S3.get_object(Bucket=AUTHORIZATION_BUCKET, Key=authorization_code)['Body'].read())
    #    client_id = form_params['client_id']
    #    redirect_uri = form_params['redirect_uri']
    #    me = form_params['me']
    #
    #    assert(form_params['grant_type'] == 'authorization_code')
    #    assert(original_request['me'] == me)
    #    assert(original_request['client_id'] == client_id)
    #    assert(original_request['redirect_uri'] == redirect_uri)
    return {"hello": "world"}
