import os
import pytest
from src import handler
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
