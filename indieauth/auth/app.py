from datetime import datetime, timedelta
import json, os, secrets
from urllib.parse import urlencode, parse_qs, urljoin

import jwt
import requests

from tokens import authorization_state_token

COGNITO_BASE_URL = os.environ['UserPoolURL']
def cognito_url(path):
    return urljoin(COGNITO_BASE_URL,path)
    
def auth_handler(event, context):
    """ this is the incoming request from an indieauth client. 
    Stash the incoming query parameters into a JWT, and redirect
    to the Cognito login UI using that JWT as the "state" paramteter
    """
    
    state_token = authorization_state_token(event['queryStringParameters'])
    
    #incoming_params = event['queryStringParameters'].copy()
    
    #if ('response_code' in incoming_params 
    #    and incoming_params['response_code'] == 'code'):
    #     if 'scope' not in incoming_params:
    #         incoming_params['scope'] = 'create update delete media'
            
    #state_token = jwt.encode(incoming_params, 'secret', algorithm='HS256') 
    #upstream_endpoint = cognito_url('/oauth2/authorize')
    #upstream_params = {}
    #upstream_params['client_id'] = '6vpoev0qmo534hfo99snhj1nvd'
    #upstream_params['response_type'] = 'code' 
    #upstream_params['redirect_uri'] = 'https://ncelo6wzf5.execute-api.us-east-1.amazonaws.com/Prod/callback'
    #upstream_params['state'] = state_token
    #print(os.environ)    
    return {
        "statusCode": 200,
        #"headers": {
        #                'Location': upstream_endpoint + '?' + urlencode(upstream_params)
        #            }
        "body": state_token.decode('utf-8')
    }
    
    
def callback_handler(event, context):
    incoming_params = event['queryStringParameters'].copy()
    authorization_code = incoming_params['code']
    our_state = incoming_params['state']
    original_request = jwt.decode(our_state,'secret', algorithm='HS256')
    
    print(authorization_code)
    token_exchange_params = {}
   
    client_id = '6vpoev0qmo534hfo99snhj1nvd'
    client_secret = '13glquv41fmoi5qsoau5013oa3penbpoos28pjp4b428bir0s1vi'
    token_exchange_params['grant_type'] = 'authorization_code'
    token_exchange_params['client_id'] = client_id
    token_exchange_params['code'] = authorization_code
    token_exchange_params['redirect_uri'] = 'https://ncelo6wzf5.execute-api.us-east-1.amazonaws.com/Prod/callback'
    token_response = requests.post('https://micropub.auth.us-east-1.amazoncognito.com/oauth2/token',
                                   token_exchange_params,
                                   auth=(client_id,client_secret))
    
    assert(token_response.status_code == requests.codes.ok)
    cognito_token = token_response.json()['access_token']
    
    userInfo_response = requests.get('https://micropub.auth.us-east-1.amazoncognito.com/oauth2/userInfo',
                                      headers={'Authorization': 'Bearer '+ cognito_token})
    assert(userInfo_response.status_code == requests.codes.ok)                                   
    auth_code_payload = original_request.copy()
    user_info = userInfo_response.json()
    auth_code_payload['sub'] = user_info['sub']
    auth_code_payload['username'] = user_info['username']
    
    if original_request.get('response_type') == 'code':
       auth_code_payload['can_upgrade'] = True
       
    auth_code_payload['exp'] = datetime.utcnow() + timedelta(seconds=15)
    print(auth_code_payload)                   
    
    # try to verify the domain, if that fails replace 'me' with
    # username.domain.tld
    verify_url = urljoin(auth_code_payload['me'], '1855')
    verify_response= requests.get(verify_url)
    if not (verify_response.status_code == requests.codes.ok and
        verify_response.json()['sub'] == user_info['sub']):
            auth_code_payload['me'] = 'https://%s.karchner.com/' % user_info['username']
            
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
        return {'body':json.dumps({'me': payload['me']} )}
        
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
    return {'hello': 'world'} 