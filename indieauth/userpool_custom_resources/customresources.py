""" based on:
https://github.com/stelligent/cloudformation-custom-resources/blob/master/lambda/python/customresource.py
"""

import json
import logging
import os
import signal
from urllib.request import HTTPHandler, Request, build_opener

import boto3

from utils import LOGGER, RequestType, custom_resource_wrapper

CLIENT_CONFIGURABLE_KEYS = [
    "UserPoolId",
    "ClientId",
    "ClientName",
    "RefreshTokenValidity",
    "ReadAttributes",
    "WriteAttributes",
    "ExplicitAuthFlows",
    "SupportedIdentityProviders",
    "CallbackURLs",
    "LogoutURLs",
    "DefaultRedirectURI",
    "AllowedOAuthFlows",
    "AllowedOAuthScopes",
    "AllowedOAuthFlowsUserPoolClient",
    "AnalyticsConfiguration",
]

USER_POOL_DOMAIN_CREATE_KEYS = ["Domain", "UserPoolId", "CustomDomainConfig"]

cognito = boto3.client("cognito-idp")


@custom_resource_wrapper
def handle_client_config(event, context, request_type):
    if request_type == RequestType.Delete:
        return

    user_pool_id = os.environ["UserPoolID"]
    client_id = os.environ["UserPoolClientID"]
    settings = cognito.describe_user_pool_client(
        UserPoolId=user_pool_id, ClientId=client_id
    )["UserPoolClient"]
    # merge the incoming ResourceProperties with the fetched settings
    settings.update(event["ResourceProperties"])
    # but only send the keys supported bu update_user_pool_client
    settings_clean = {k: settings[k] for k in CLIENT_CONFIGURABLE_KEYS if k in settings}
    # AllowedOAuthFlowsUserPoolClient must be a boolean
    if settings_clean["AllowedOAuthFlowsUserPoolClient"].lower() == "true":
        settings_clean["AllowedOAuthFlowsUserPoolClient"] = True
    else:
        settings_clean["AllowedOAuthFlowsUserPoolClient"] = False
    LOGGER.info("ATTEMPTING TO CONFIGURE USER POOL CLIENT WITH:\n %s", settings_clean)
    cognito.update_user_pool_client(**settings_clean)
    return {}


@custom_resource_wrapper
def handle_user_pool_custom_domain(event, context, request_type):
    cognito = boto3.client("cognito-idp")
    user_pool_id = os.environ["UserPoolID"]
    domain_config_cleaned = {
        k: event["ResourceProperties"][k]
        for k in USER_POOL_DOMAIN_CREATE_KEYS
        if k in event["ResourceProperties"]
    }

    if request_type == RequestType.Delete:
        safe_delete_user_pool_domain(Domain=event["ResourceProperties"]["Domain"])
    elif request_type == RequestType.Update:
        if (
            event["ResourceProperties"]["Domain"]
            == event["OldResourceProperties"]["Domain"]
        ):
            # the domain name isn't changing-- maybe a new cert?
            return cognito.update_user_pool_domain(**domain_config_cleaned)
        else:
            safe_delete_user_pool_domain(
                Domain=event["OldResourceProperties"]["Domain"]
            )
            return cognito.create_user_pool_domain(**domain_config_cleaned)

    elif request_type == RequestType.Create:
        # just in case:
        safe_delete_user_pool_domain(Domain=event["ResourceProperties"]["Domain"])

        return cognito.create_user_pool_domain(**domain_config_cleaned)


def safe_delete_user_pool_domain(Domain):
    domain_description = cognito.describe_user_pool_domain(Domain=Domain)[
        "DomainDescription"
    ]
    LOGGER.info("domain details for %s: %s" % (Domain, domain_description))
    if "UserPoolId" in domain_description:
        try:
            cognito.delete_user_pool_domain(
                Domain=Domain, UserPoolId=domain_description["UserPoolId"]
            )
        except:
            LOGGER.exception("Exception when deleting domain, maybe harmless: ")
