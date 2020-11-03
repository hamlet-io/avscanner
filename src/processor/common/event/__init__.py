import re
import json
import urllib
import dateutil
from dao.conf import UNPROCESSED_BUCKET


class InvalidEventError(Exception):
    pass


class InvalidEventDataError(InvalidEventError):
    pass


class MissingEventFieldError(InvalidEventError):
    pass


class InvalidKeyFormat(InvalidEventError):
    pass


def loads(text):
    try:
        return json.loads(text)['Records'][0]
    except ValueError as e:
        raise InvalidEventDataError('Not a valid JSON') from e
    except KeyError as e:
        raise MissingEventFieldError(str(e)) from e
    except IndexError as e:
        raise InvalidEventDataError('Empty Records list') from e


def loads_s3_object_created_event(text):
    event = loads(text)
    try:
        if not event['eventName'].startswith('ObjectCreated:'):
            raise InvalidEventError()
        event['s3']  # checking that key exists
        obj = event['s3']['object']
        obj['key'] = urllib.parse.unquote(obj['key'])
        return event
    except KeyError as e:
        raise MissingEventFieldError(str(e))


def parse_unprocessed_file_key(key):

    key_pattern = r'^([^\/\s]+)\/(([^\/\s]+)\/)*([^\/\s]+)\.(\w+)$'
    # try to use legacy format, without upload hash
    match = re.match(key_pattern, key)
    if not match:
        raise InvalidKeyFormat('Key does not match expected format')

    submission_guid = match.group(1)
    try:
        filename = match.group(2)
    except ValueError as e:
        raise InvalidKeyFormat('Key does not match expected format') from e
    try:
        file_ext = match.group(3)
    except IndexError:
        file_ext = ''

    return submission_guid, filename, file_ext


def loads_s3_unprocessed_bucket_object_created_event(text):
    event = loads_s3_object_created_event(text)
    try:

        s3 = event['s3']
        bucket = s3['bucket']['name']
        key = s3['object']['key']

        if bucket != UNPROCESSED_BUCKET:
            raise InvalidEventError(
                'Invalid bucket. Expected:{}. Got:{}.'.format(
                    UNPROCESSED_BUCKET,
                    bucket
                )
            )
        parse_unprocessed_file_key(key)
        return event
    except KeyError as e:
        raise MissingEventFieldError(str(e)) from e


def create_minimal_valid_file_put_event(
    key=None,
    etag=None,
    size=None,
    bucket=None,
    event_time=None,
):
    event_json = {
      "Records": [
        {
          "eventTime": event_time.isoformat(),
          "eventName": "ObjectCreated:Put",
          "s3": {
            "bucket": {
              "name": bucket
            },
            "object": {
              "key": key,
              "size": size,
              "eTag": etag,
            }
          }
        }
      ]
    }
    return json.dumps(event_json)
