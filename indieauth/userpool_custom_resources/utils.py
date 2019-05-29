import json
import logging
import os
import signal
from enum import Enum
from urllib.request import HTTPHandler, Request, build_opener

import boto3

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


class RequestType(Enum):
    Create = 1
    Update = 2
    Delete = 3


def custom_resource_wrapper(inner_func):
    """Handle Lambda event from AWS"""
    # largely based on https://github.com/stelligent/cloudformation-custom-resources/blob/master/lambda/python/customresource.py

    def wrapped(event, context):
        # Setup alarm for remaining runtime minus a second
        signal.alarm(int((context.get_remaining_time_in_millis() / 1000)) - 1)
        try:
            LOGGER.info("REQUEST RECEIVED:\n %s", event)
            LOGGER.info("REQUEST RECEIVED:\n %s", context)
            request_type = getattr(RequestType, event["RequestType"])
            if request_type == RequestType.Create:
                LOGGER.info("CREATE!")
                attributes = inner_func(event, context, request_type)
                send_response(
                    event,
                    context,
                    "SUCCESS",
                    {"Message": "Resource creation successful!"},
                    attributes=attributes,
                )
            elif request_type == RequestType.Update:
                LOGGER.info("UPDATE!")
                attributes = inner_func(event, context, request_type)
                send_response(
                    event,
                    context,
                    "SUCCESS",
                    {"Message": "Resource update successful!"},
                    attributes=attributes,
                )
            elif request_type == RequestType.Delete:
                LOGGER.info("DELETE!")
                attributes = inner_func(event, context, request_type)
                send_response(
                    event,
                    context,
                    "SUCCESS",
                    {"Message": "Resource deletion successful!"},
                    attributes=attributes,
                )
            else:
                LOGGER.info("FAILED!")
                send_response(
                    event,
                    context,
                    "FAILED",
                    {"Message": "Unexpected event received from CloudFormation"},
                )
        except Exception as e:  # pylint: disable=W0702
            LOGGER.exception("Exception occured")
            LOGGER.info("FAILED!")
            send_response(
                event, context, "FAILED", {"Message": "Exception during processing"}
            )

    return wrapped


def send_response(event, context, response_status, response_data, attributes=None):
    """Send a resource manipulation status response to CloudFormation"""

    if attributes:
        response_data.update(attributes)

    response_body = json.dumps(
        {
            "Status": response_status,
            "Reason": "See the details in CloudWatch Log Stream: "
            + context.log_stream_name,
            "PhysicalResourceId": context.log_stream_name,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "Data": response_data,
        }
    ).encode("utf-8")

    LOGGER.info("ResponseURL: %s", event["ResponseURL"])
    LOGGER.info("ResponseBody: %s", response_body)

    opener = build_opener(HTTPHandler)
    request = Request(event["ResponseURL"], data=response_body)
    request.add_header("Content-Type", "")
    request.add_header("Content-Length", len(response_body))
    request.get_method = lambda: "PUT"
    response = opener.open(request)
    LOGGER.info("Status code: %s", response.getcode())
    LOGGER.info("Status message: %s", response.msg)


def timeout_handler(_signal, _frame):
    """Handle SIGALRM"""
    raise Exception("Time exceeded")


signal.signal(signal.SIGALRM, timeout_handler)
