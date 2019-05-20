import os, secrets

import boto3
import jwt
import base64

CMK_ID = os.environ['CMK']
kms_client = boto3.client('kms')

def clean_authorization_params(request_params):
    response_type = request_params.get('response_type', 'id')
    assert response_type in ['id', 'code']
    required_params = ['me', 'client_id', 'redirect_uri', 'state'] 
    cleaned_dict = {'response_type': response_type}
    for param in required_params:
        cleaned_dict[param] = request_params[param]
    if response_type == 'code':
        cleaned_dict['scope'] = request_params.get('scope', 'create update delete media')
    return cleaned_dict 
    
def authorization_state_token(request_params):
    cleaned_params = clean_authorization_params(request_params)
    # "Otherwise, if no argument is provided, or if the argument is None,
    # the token_* functions will use a reasonable default instead"
    # https://docs.python.org/3/library/secrets.html#how-many-bytes-should-tokens-use
    # 
    # I like the sound of that.
    signing_key = secrets.token_bytes()
    encrypted_key = kms_client.encrypt(
        KeyId=CMK_ID,
        Plaintext=signing_key)['CiphertextBlob']
        
    return jwt.encode(
        cleaned_params,
        signing_key,
        algorithm='HS256',
        headers={'kid': base64.b64encode(encrypted_key).decode('utf8')})    