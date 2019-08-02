import json


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
    except KeyError as e:
        raise MissingEventFieldError(str(e))
