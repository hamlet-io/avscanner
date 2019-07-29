import os
import io
import json
import pytest
from src import handler, s3client as lambda_s3client
from src.task import receiver
from tests.integration.conftest import (
    PROCESSED_BUCKET,
    UNPROCESSED_BUCKET,
    QUARANTINE_DIR,
    INVALID_DIR,
    VALID_DIR,
    filename_to_bucket_key
)
from tests.integration import utils as integration_test_utils
from tests import utils as test_utils


@pytest.mark.usefixtures(
    "clear_buckets",
    "fill_buckets"
)
def test(s3_events_dict, s3client):
    event_name = 'invalid-key-format.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert integration_test_utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)

    event_name = '2019-1-1-testuser-valid_invalid_event.json'
    bucket_filename = filename_to_bucket_key('2019-1-1-testuser-valid.json')
    handler(s3_events_dict['put'][event_name], {})
    assert integration_test_utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)

    event_name = '2019-1-1-testuser-valid.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not integration_test_utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)
    assert test_utils.get_test_data_file_text(event_name) == integration_test_utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(VALID_DIR, bucket_filename)
    )

    event_name = '2019-1-2-testuser-invalid.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not integration_test_utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)
    assert test_utils.get_test_data_file_text(event_name) == integration_test_utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(INVALID_DIR, bucket_filename)
    )

    event_name = '2019-1-3-testuser-virus.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not integration_test_utils.has_file(s3client, UNPROCESSED_BUCKET, filename_to_bucket_key(event_name))
    assert test_utils.get_test_data_file_text(event_name) == integration_test_utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(QUARANTINE_DIR, bucket_filename)
    )


@pytest.mark.usefixtures(
    "clear_buckets",
    "fill_buckets"
)
def test_get_unprocessed_file_object_modified_error(s3client, s3_events_dict):
    # must raise file changed error if file removed or modified
    event_name = '2019-1-1-testuser-valid.json'
    event = receiver.recast_event(s3_events_dict['put'][event_name])
    # first time must be succesfull because file unchanged
    body = json.loads(lambda_s3client.get_unprocessed_file_object(event)['Body'].read())
    s3client.put_object(
        Bucket=event['file']['bucket'],
        Key=event['file']['key'],
        Body=io.BytesIO(json.dumps(body).encode('utf8'))
    )
    # second time should fail with original event because file modified
    with pytest.raises(lambda_s3client.FileChangedError):
        lambda_s3client.get_unprocessed_file_object(event)
    response = s3client.get_object(
        Bucket=event['file']['bucket'],
        Key=event['file']['key']
    )
    # Updating etag to make event point to current file verison
    event['file']['etag'] = response['ETag']
    lambda_s3client.get_unprocessed_file_object(event)

    # Deleting object
    s3client.delete_object(
        Bucket=event['file']['bucket'],
        Key=event['file']['key']
    )
    # Deleted = modified
    with pytest.raises(lambda_s3client.FileChangedError):
        lambda_s3client.get_unprocessed_file_object(event)
