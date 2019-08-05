import json
import datetime
from dao.conf import UNPROCESSED_BUCKET


class InvalidEventError(Exception):
    pass


class InvalidEventDataError(InvalidEventError):
    pass


class MissingEventFieldError(InvalidEventError):
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
        return event
    except KeyError as e:
        raise MissingEventFieldError(str(e))


def validate_unprocessed_file_key(key):
    try:
        year, month, day, user, filename = (part for part in key.split('/') if part)
    except ValueError as e:
        raise InvalidEventError('Key does not match expected format') from e
    try:
        year, month, day = int(year), int(month), int(day)
    except ValueError as e:
        raise InvalidEventError('<year>/<month>/<day> must be integers') from e
    try:
        datetime.datetime(year=year, month=month, day=day)
    except ValueError as e:
        raise InvalidEventError('Given date is invalid') from e


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
        validate_unprocessed_file_key(key)
        return event
    except KeyError as e:
        raise MissingEventFieldError(str(e)) from e
