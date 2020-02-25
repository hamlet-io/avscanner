import json
import copy
import datetime
from unittest import mock
import dateutil
import pytest
from processor.common import event

UNPROCESSED_BUCKET_NAME = "test"


def test_loads():
    # Not a json str
    with pytest.raises(event.InvalidEventDataError):
        event.loads("not a JSON")
    # No Records field
    with pytest.raises(event.MissingEventFieldError):
        event.loads(json.dumps({}))
    # Empty Records list
    with pytest.raises(event.InvalidEventDataError):
        event.loads(json.dumps({
            "Records": []
        }))
    assert event.loads(json.dumps({
        "Records": ["Hello"]
    })) == "Hello"


def test_loads_object_created():
    e = {
        "eventName": "ObjectCreated:",
        "s3": {
            "object": {
                "key": "key"
            }
        }
    }
    data = {
        "Records": [e]
    }
    event.loads_s3_object_created_event(json.dumps(data))

    invalid_data = copy.deepcopy(data)
    del invalid_data['Records'][0]['eventName']
    with pytest.raises(event.MissingEventFieldError):
        event.loads_s3_object_created_event(json.dumps(invalid_data))

    invalid_data = copy.deepcopy(data)
    del invalid_data['Records'][0]['s3']
    with pytest.raises(event.MissingEventFieldError):
        event.loads_s3_object_created_event(json.dumps(invalid_data))

    invalid_data = copy.deepcopy(data)
    invalid_data['Records'][0]['eventName'] = "ObjectDeleted:"
    with pytest.raises(event.InvalidEventError):
        event.loads_s3_object_created_event(json.dumps(invalid_data))

    # testing key url decode
    url_encoded_key_data = copy.deepcopy(data)
    url_encoded_key_data['Records'][0]['s3']['object']['key'] = \
        'private%2Fuser%3Afname%3Alname%2FsubmissionInbox%2F100-100-10.json'
    parsed = event.loads_s3_object_created_event(json.dumps(url_encoded_key_data))
    assert parsed['s3']['object']['key'] == 'private/user:fname:lname/submissionInbox/100-100-10.json'


@mock.patch("processor.common.event.UNPROCESSED_BUCKET", UNPROCESSED_BUCKET_NAME)
def test_loads_s3_unprocessed_bucket_object_created_event():
    e = {
        "eventName": "ObjectCreated:",
        "s3": {
            "bucket": {
                "name": UNPROCESSED_BUCKET_NAME
            },
            "object": {
                "key": "private/user/submissionInbox/2019-11-18T14:11:50+08:00-xxxxxxx.json"
            }
        }
    }
    data = {
        "Records": [e]
    }

    event.loads_s3_unprocessed_bucket_object_created_event(json.dumps(data))

    # invalid bucket
    invalid_data = copy.deepcopy(data)
    invalid_data['Records'][0]['s3']['bucket']['name'] = 'invalid'
    with pytest.raises(event.InvalidEventError):
        event.loads_s3_unprocessed_bucket_object_created_event(json.dumps(invalid_data))

    required_keys = [
        ["s3"],
        ["s3", "bucket"],
        ["s3", "bucket", "name"],
        ["s3", "object"],
        ["s3", "object", "key"]
    ]
    for required in required_keys:
        invalid_data = copy.deepcopy(data)
        obj = invalid_data['Records'][0]
        for key in required[:-1]:
            obj = obj[key]
        del obj[required[-1]]
        with pytest.raises(event.MissingEventFieldError) as exc_info:
            event.loads_s3_unprocessed_bucket_object_created_event(json.dumps(invalid_data))
        assert exc_info.value.args[0] == "'{}'".format(required[-1])


def test_parse_unprocessed_file_key():
    with pytest.raises(event.InvalidEventError):
        event.parse_unprocessed_file_key('bad key')
    with pytest.raises(event.InvalidEventError):
        event.parse_unprocessed_file_key('/user/2019-11-18T14:11:50+08:00-xxxxxxx.json')
    with pytest.raises(event.InvalidEventError):
        event.parse_unprocessed_file_key('/private/user/submissionInbox/2019-11-18T14:11:50+08:00.json')
    with pytest.raises(event.InvalidEventError):
        event.parse_unprocessed_file_key('private/user/submissionInbox/2K18K-11-18T14:11:50+08:00-xxxxxxx.json')
    event.parse_unprocessed_file_key('private/user/submissionInbox/2019-11-18T14:11:50+08:00-xxxxxxx.json')


def test_create_minimal_valid_file_put_event():
    key = 'private/user-id/submissionInbox/2019-11-18T14:11:50+08:00.json'
    event_time = datetime.datetime(2019, 11, 18, 14, 11, 50)
    size = 10
    bucket = event.UNPROCESSED_BUCKET
    etag = 'etag'
    event_body = event.create_minimal_valid_file_put_event(
        key=key,
        event_time=event_time,
        size=size,
        bucket=bucket,
        etag=etag
    )
    event.loads_s3_unprocessed_bucket_object_created_event(event_body)
