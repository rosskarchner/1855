from datetime import datetime, timedelta
import json
import jwt
from urllib.parse import urlencode, parse_qs

# import requests


def auth_handler(event, context):
    """ this is the incoming request from an indieauth client. 
    Stash the incoming query parameters to S3, and redirect
    to the Cognito login UI"""
    
    incoming_params = event['queryStringParameters'].copy()
    
    if ('response_code' in incoming_params 
        and incoming_params['response_code'] == 'code'):
         if 'scope' not in incoming_params:
             incoming_params['scope'] = 'create update delete media'
            
    state_token = jwt.encode(incoming_params, 'secret', algorithm='HS256') 
    upstream_endpoint = 'https://micropub.auth.us-east-1.amazoncognito.com/oauth2/authorize'
    upstream_params = {}
    upstream_params['client_id'] = '6vpoev0qmo534hfo99snhj1nvd'
    upstream_params['response_type'] = 'code' 
    upstream_params['redirect_uri'] = 'https://ncelo6wzf5.execute-api.us-east-1.amazonaws.com/Prod/callback'
    upstream_params['state'] = state_token
    
    return {
        "statusCode": 302,
        "headers": {
                        'Location': upstream_endpoint + '?' + urlencode(upstream_params)
                    }
    }
    
    
def callback_handler(event, context):
    incoming_params = event['queryStringParameters'].copy()
    authorization_code = incoming_params['code']
    our_state = incoming_params['state']
    original_request = jwt.decode(our_state,'secret', algorithm='HS256')
    
    token_exchange_params = {}
   
    token_exchange_params['grant_type'] = 'authorization_code'
    token_exchange_params['client_id'] = '6vpoev0qmo534hfo99snhj1nvd'
    token_exchange_params['code'] = authorization_code
    
    auth_code_payload = original_request.copy()
    
    if original_request.get('response_type') == 'code':
       auth_code_payload['can_upgrade'] = True
       auth_code_payload['exp'] = datetime.utcnow() + timedelta
                      
    client_return_params = {}
    client_return_params['code'] = jwt.encode(auth_code_payload, 'secret',algorithm='HS256')
    client_return_params['state'] = original_request['state']
    
    
    return {
        "statusCode": 302,
        "headers": {
                        'Location': original_request['redirect_uri'] + '?' + urlencode(client_return_params)
                    }
    }
    
    
def auth_code_check(event,context):
    form_params = parse_qs(event['body'])
    authorization_code = form_params['code'][0]
    incoming_client_id =  form_params['client_id'][0]
    incoming_redirect_uri = form_params['redirect_uri'][0]
    
    payload = jwt.decode(authorization_code,'secret',algorithm='HS256')
    
    if (incoming_client_id == payload['client_id'] and 
        incoming_redirect_uri == payload['redirect_uri'] 
    ):
        # this is essentially broken, any user could sign in as any site
        return {'body':json.dumps({'me': payload['me']} )}