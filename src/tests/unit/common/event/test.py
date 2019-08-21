import json
import copy
from unittest import mock
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
        "s3": ""
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


@mock.patch("processor.common.event.UNPROCESSED_BUCKET", UNPROCESSED_BUCKET_NAME)
def test_loads_s3_unprocessed_bucket_object_created_event():
    e = {
        "eventName": "ObjectCreated:",
        "s3": {
            "bucket": {
                "name": UNPROCESSED_BUCKET_NAME
            },
            "object": {
                "key": "private/user/submissionInbox/00001.json"
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


def test_validate_unprocessed_file_key():
    with pytest.raises(event.InvalidEventError):
        event.validate_unprocessed_file_key('bad key')
    with pytest.raises(event.InvalidEventError):
        event.validate_unprocessed_file_key('/user/00012.json')
    with pytest.raises(event.InvalidEventError):
        event.validate_unprocessed_file_key('/private/user/test/submissionInbox/00012.json')
    event.validate_unprocessed_file_key('private/user/submissionInbox/00000.json')
