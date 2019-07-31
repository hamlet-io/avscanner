import os
import copy
import pytest
from src.task import receiver
from tests import utils


def test_valid_event_recast():
    valid_put_event = utils.get_test_data_event(
        os.path.join('put', '2019-1-1-testuser-valid.json')
    )
    recasted_event = receiver.recast_event(valid_put_event)

    valid_put_event = valid_put_event['Records'][0]
    key = valid_put_event['s3']['object']['key']
    year, month, day, user, filename = key.split('/')
    year, month, day = int(year), int(month), int(day)
    etag = valid_put_event['s3']['object']['eTag']
    size = valid_put_event['s3']['object']['size']
    bucket = valid_put_event['s3']['bucket']['name']

    assert recasted_event == {
        'user': user,
        'year': year,
        'month': month,
        'day': day,
        'file': {
            'etag': etag,
            'name': filename,
            'bucket': bucket,
            'key': key,
            'size': size,
        },
        'error': None
    }


def test_invalid_event_type_recast():
    invalid_event = utils.get_test_data_event(
        os.path.join('put', '2019-1-1-testuser-valid_invalid_event.json')
    )
    with pytest.raises(receiver.InvalidEvent):
        receiver.recast_event(invalid_event)


def test_invalid_bucket_name_recast():
    invalid_bucket_event = utils.get_test_data_event(
        os.path.join('put', '2019-1-5-testuser-invalid_bucket.json')
    )
    with pytest.raises(receiver.InvalidEvent):
        receiver.recast_event(invalid_bucket_event)


def test_event_missing_fields():
    # No 'Records'
    with pytest.raises(receiver.InvalidEvent):
        receiver.recast_event({})
    # Empty 'Records'
    with pytest.raises(receiver.InvalidEvent):
        receiver.recast_event({'Records': []})

    valid_put_event = utils.get_test_data_event(
        os.path.join('put', '2019-1-1-testuser-valid.json')
    )

    def missing_key(*path):
        event_records = copy.deepcopy(valid_put_event)
        event = event_records['Records'][0]
        for i in range(len(path) - 1):
            event = event[path[i]]
        del event[path[-1]]
        with pytest.raises(receiver.InvalidEvent):
            receiver.recast_event(event_records)

    missing_key('s3')
    missing_key('s3', 'object')
    missing_key('s3', 'object', 'eTag')
    missing_key('s3', 'object', 'key')
    missing_key('s3', 'object', 'size')
    missing_key('s3', 'bucket')
    missing_key('s3', 'bucket', 'name')


def test_key_recast():
    assert (2019, 10, 15, 'user', 'filename.json') == receiver.recast_key('2019/10/15/user/filename.json')


def test_invalid_key_recast():
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2019/10/-1/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2019/-5/15/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('-2012/10/15/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2019/13/15/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2019/13/40/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('12/14/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('a/10/4/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('a/10/4/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2015/b/4/user/filename.json')
    with pytest.raises(receiver.InvalidObjectKeyFormat):
        receiver.recast_key('2015/6/c/user/filename.json')
