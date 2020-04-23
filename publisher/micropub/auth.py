import os
from urllib.parse import parse_qsl

import requests

import multidict


class TokenUser(object, context=None):
    def __init__(self, token):
        endpoint = os.environ["TokenEndpointURL"]
        me = os.environ["MeURL"]

        headers = {"Authorization": "Bearer " + token}

        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:  # todo: respond to failures
            if response.headers["Content-type"] == "application/x-www-form-urlencoded":
                token_data = multidict.MultiDict(parse_qsl(response.text))

            else:
                token_data = response.json()

            if token_data["me"] == me:
                self.scopes = token_data.get("scope").split()
        else:
            self.scopes = []
