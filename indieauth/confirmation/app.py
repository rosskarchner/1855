import os, base64

import boto3
import jwt

CMK_ID = os.environ["CMK"]
kms_client = boto3.client("kms")


def lambda_handler(event, context):
    incoming_params = event["queryStringParameters"].copy()
    authorization_code = incoming_params["code"]
    our_state = incoming_params["state"]
    signing_key_encrypted = jwt.get_unverified_header(our_state)["kid"]
    plaintext = kms_client.decrypt(
        CiphertextBlob=bytes(base64.b64decode(signing_key_encrypted))
    )
    print(plaintext)
    print(event)
    print(context)
    #    original_request = jwt.decode(our_state, "secret", algorithm="HS256")
    #
    #    print(authorization_code)
    #    token_exchange_params = {}
    #
    #    client_id = "6vpoev0qmo534hfo99snhj1nvd"
    #    client_secret = "13glquv41fmoi5qsoau5013oa3penbpoos28pjp4b428bir0s1vi"
    #    token_exchange_params["grant_type"] = "authorization_code"
    #    token_exchange_params["client_id"] = client_id
    #    token_exchange_params["code"] = authorization_code
    #    token_exchange_params[
    #        "redirect_uri"
    #    ] = "https://ncelo6wzf5.execute-api.us-east-1.amazonaws.com/Prod/callback"
    #    token_response = requests.post(
    #        "https://micropub.auth.us-east-1.amazoncognito.com/oauth2/token",
    #        token_exchange_params,
    #        auth=(client_id, client_secret),
    #    )
    #
    #    assert token_response.status_code == requests.codes.ok
    #    cognito_token = token_response.json()["access_token"]
    #
    #    userInfo_response = requests.get(
    #        "https://micropub.auth.us-east-1.amazoncognito.com/oauth2/userInfo",
    #        headers={"Authorization": "Bearer " + cognito_token},
    #    )
    #    assert userInfo_response.status_code == requests.codes.ok
    #    auth_code_payload = original_request.copy()
    #    user_info = userInfo_response.json()
    #    auth_code_payload["sub"] = user_info["sub"]
    #    auth_code_payload["username"] = user_info["username"]
    #
    #    if original_request.get("response_type") == "code":
    #        auth_code_payload["can_upgrade"] = True
    #
    #    auth_code_payload["exp"] = datetime.utcnow() + timedelta(seconds=15)
    #    print(auth_code_payload)
    #
    #    # try to verify the domain, if that fails replace 'me' with
    #    # username.domain.tld
    #    verify_url = urljoin(auth_code_payload["me"], "1855")
    #    verify_response = requests.get(verify_url)
    #    if not (
    #        verify_response.status_code == requests.codes.ok
    #        and verify_response.json()["sub"] == user_info["sub"]
    #    ):
    #        auth_code_payload["me"] = "https://%s.karchner.com/" % user_info["username"]
    #
    #    client_return_params = {}
    #    client_return_params["code"] = jwt.encode(
    #        auth_code_payload, "secret", algorithm="HS256"
    #    )
    #    client_return_params["state"] = original_request["state"]
    #
    return {"statusCode": 200, "body": "hi"}
