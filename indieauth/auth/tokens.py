import base64
import os
import secrets

import boto3

import jwt

CMK_ID = os.environ["CMK"]
kms_client = boto3.client("kms")


def clean_authorization_params(request_params):
    response_type = request_params.get("response_type", "id")
    assert response_type in ["id", "code"]
    required_params = ["me", "client_id", "redirect_uri", "state"]
    cleaned_dict = {"response_type": response_type}
    for param in required_params:
        cleaned_dict[param] = request_params[param]
    if response_type == "code":
        cleaned_dict["scope"] = request_params.get(
            "scope", "create update delete media"
        )
    return cleaned_dict


def authorization_state_token(request_params):
    print(CMK_ID)
    payload = clean_authorization_params(request_params)
    payload["aud"] = "upstream_oauth_state"
    signing_key = secrets.token_bytes()
    encrypted_key = kms_client.encrypt(KeyId=CMK_ID, Plaintext=signing_key)[
        "CiphertextBlob"
    ]

    return jwt.encode(
        payload,
        signing_key,
        algorithm="HS256",
        headers={"kid": base64.b64encode(encrypted_key).decode("utf8")},
    )
