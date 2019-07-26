import datetime
from zappa.asynchronous import task
from loggers import logging
from task import scanner
from s3client import UNPROCESSED_BUCKET


logger = logging.getLogger(__name__)


class InvalidObjectKeyFormat(Exception):
    pass


class InvalidEvent(Exception):
    pass


VALID_S3_EVENT_NAME = 'ObjectCreated:Put'


def recast_event(event):
    try:
        event = event['Records'][0]
        s3 = event['s3']
        key = s3['object']['key']
        bucket = s3['bucket']['name']
        size = s3['object']['size']
        etag = s3['object']['eTag']
        eventName = event['eventName']
        if eventName != VALID_S3_EVENT_NAME:
            raise InvalidEvent(f'Invalid event name:{eventName}')
        if bucket != UNPROCESSED_BUCKET:
            raise InvalidEvent(f'Invalid bucket name:{bucket}')
    except KeyError as e:
        raise InvalidEvent(f'Event missing:{e}') from e
    except IndexError as e:
        raise InvalidEvent('No event in Records') from e
    try:
        year, month, day, user, filename = key.split('/')
    except ValueError as e:
        raise InvalidObjectKeyFormat("Invalid key format") from e
    try:
        year, month, day = int(year), int(month), int(day)
    except ValueError as e:
        raise InvalidObjectKeyFormat('Invalid date component format, must be integer') from e
    try:
        datetime.datetime(year, month, day).date()
    except ValueError as e:
        raise InvalidObjectKeyFormat(f"Invalid date:{e}") from e
    return dict(
        user=user,
        file=dict(
            name=filename,
            size=size,
            hash=etag,
            bucket=bucket,
            key=key
        ),
        year=year,
        month=month,
        day=day
    )


@task
def handler(event, context):
    try:
        event = recast_event(event)
    except InvalidObjectKeyFormat:
        # do nothing for now but in future we may move file to another "dir"
        return True
    except InvalidEvent:
        # do nothing because can't handle this event
        return True

    logger.info(event)
    scanner.handler(event, context)
    return True
