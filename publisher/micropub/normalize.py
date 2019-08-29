import json
import os
from urllib.parse import parse_qsl, urljoin

import multidict
import sansio_multipart


def kvpairs_to_mfjson(kvpairs):
    types = set(["h-entry"])
    action = None
    url = None
    properties = {}
    access_token = None
    files = {}

    for key, value in kvpairs:
        if key == "h":
            types.add("h-" + value)

        elif key == "url":
            url = value

        elif key == "action":
            action = value

        elif key == "access_token":
            access_token = value

        elif key.endswith("[]"):
            key_no_brackets = key[:-2]
            if key_no_brackets in properties:
                properties[key_no_brackets].append(value)
        else:
            properties[key] = [value]

    if action and url:
        assert action in ["delete", "undelete"]
        document = {"action": action, "url": url}

    else:
        document = {"type": list(types), "properties": properties}

    return document, access_token


def normalize_micropub_post(event):
    # accepts an API Gateway event, that should represent a micropub request in
    # either json, x-www-form-urlencoded, or multipart/form-data. Returns a tuple of
    # access token, the type of operation (see MicroPubOperationType) and the json-formatted
    # Create, updated, or delete document per https://www.w3.org/TR/micropub/#syntax

    headers = multidict.CIMultiDict(event["headers"])

    header_access_token = None
    body_access_token = None
    files = {}

    if "Authorization" in headers:
        header_access_token = headers["Authorization"][7:]

    if headers["content-type"] == "application/json":
        json_document = json.loads(event["body"])

    elif headers["content-type"] == "application/x-www-form-urlencoded":
        json_document, body_access_token = kvpairs_to_mfjson(parse_qsl(event["body"]))

    elif headers["content-type"].startswith("multipart/form-data"):
        ct_fields_unparsed = headers["content-type"].split(";")[1:]
        ct_fields = {}
        for field in ct_fields_unparsed:
            key, value = field.split("=")
            ct_fields[key.strip()] = value

        multipart_parser = sansio_multipart.MultipartParser(ct_fields["boundary"])

        # todo: is utf8 a dangerous assumption?
        chunks = multipart_parser.parse(event["body"].encode("utf-8"))

        # we need to "inflate" each Part by feeding them the PartData
        parts = []
        for chunk in chunks[:-1]:
            if isinstance(chunk, sansio_multipart.parser.Part):
                parts.append(chunk)
            elif isinstance(chunk, sansio_multipart.parser.PartData):
                parts[-1].buffer(chunk)

        kvpairs = []
        me_url = os.environ["MeURL"]
        request_id = event["requestContext"]["requestId"]
        for part in parts:
            if part.filename:
                key = "media/" + "-".join([request_id, part.filename])
                url = urljoin(me_url, key)
                files[key] = part
                kvpairs.append((part.name, url))
            # I don't know if this is reasonable, discard anything without
            # a filename but with a content-type
            elif not part.content_type:
                kvpairs.append((part.name, part.value))

        json_document, body_access_token = kvpairs_to_mfjson(kvpairs)

    return json_document, header_access_token or body_access_token, files
