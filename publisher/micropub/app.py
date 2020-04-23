import json
import os
import random
import xml.etree.ElementTree
from datetime import datetime
from enum import Enum
from urllib.parse import parse_qsl, urljoin

import boto3
import dateutil.parser
import pytz
import requests
from boto3.dynamodb.conditions import Key

import multidict
import sansio_multipart
import slugify
from auth import TokenUser
from normalize import normalize_micropub_post


class MicropubOperationType(Enum):
    CREATE = 1
    UPDATE = 2
    DELETE = 3
    UNDELETE = 4
    MEDIA = 5


dynamodb = boto3.resource("dynamodb")
EntriesTable = dynamodb.Table(os.environ["TABLE"])


def remove_tags(text):
    return "".join(xml.etree.ElementTree.fromstring(text).itertext())


def micropub_get(event, context):
    print(json.dumps(event))
    return {
        "statusCode": 202,
        "body": "This site doesn't seem to belong to this subscriber",
        "headers": {"Location": "https://ross.karchner.com/fake"},
    }


def create_document(operation, document):
    timezone = pytz.timezone(os.environ["TIMEZONE"])
    now_local = timezone.fromutc(datetime.utcnow())
    now_iso = now_local.isoformat()

    # TODO: Create a persistent ID
    # TODO: sortdate should be based on UTC
    # noise gets appended to sortdate just to avoid conflicts
    # (DynamoDB sort keys must be unqiue)
    # We'll also use it as a slug if there is no name
    noise = str(random.randint(1, 1000))

    # don't mess with publication date if it's already set
    if (
        "published" not in document["properties"]
        and "dt-published" not in document["properties"]
    ):
        document["properties"]["dt-published"] = [now_iso]
        pubdate = now_local

    else:
        pubdate_iso_list = document["properties"].get("dt-published") or document[
            "properties"
        ].get("published")

        pubdate_iso = pubdate_iso_list[0]
        pubdate = dateutil.parser.parse(pubdate_iso)

    # DO set the updated date
    if "updated" in document["properties"]:
        del document["properties"]["updated"]

    document["properties"]["dt-updated"] = [now_iso]

    # figure out the URL
    slug_material_list = (
        document["properties"].get("mp-slug")
        or document["properties"].get("name")
        or [noise]
    )

    slug = slugify.slugify(slug_material_list)

    url = None

    while url == None:
        extra_slug = random.randint(1, 1000)
        speculative_url = "/%s/%s/%s-%s.html" % (
            pubdate.year,
            pubdate.month,
            extra_slug,
            slug,
        )
        existing_item = EntriesTable.get_item(Key={"url": speculative_url}).get("Item")
        if not existing_item:
            url = speculative_url

    year_month = "%s%s" % (pubdate.year, str(pubdate.month).zfill(2))
    sortdate = now_iso + "&&" + noise

    dynamo_item = {"sortdate": sortdate, "url": url, "mf2_json": document}

    EntriesTable.put_item(Item=dynamo_item)

    return url


def scope_required_for_document(document):
    if "action" in document and document["action"] in ["update", "delete", "undelete"]:
        operation = getattr(MicropubOperationType, document["action"].uppercase())
    elif "type" in document and "properties" and document["properties"]:
        operation = MicropubOperationType.CREATE


def micropub_post(event, context):
    print(json.dumps(event))
    document, access_token, files = normalize_micropub_post(event)
    users = TokenUser(access_token)

    required_scope = ScopeForOperation[operation]

    if required_scope in users_scopes:
        url_path = create_document(operation, document)
        url = urljoin(os.environ["MeURL"], url_path)
        print(url)

        return {"statusCode": 202, "headers": {"Location": url}}
