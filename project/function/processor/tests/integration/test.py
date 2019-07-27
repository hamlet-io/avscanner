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
from tests.integration import utils


@pytest.mark.usefixtures(
    "clear_buckets",
    "fill_buckets"
)
def test(s3_events_dict, s3client):
    event_name = '2019-1-1-testuser-valid.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)
    assert utils.get_test_data_file_text(event_name) == utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(VALID_DIR, bucket_filename)
    )

    event_name = '2019-1-2-testuser-invalid.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not utils.has_file(s3client, UNPROCESSED_BUCKET, bucket_filename)
    assert utils.get_test_data_file_text(event_name) == utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(INVALID_DIR, bucket_filename)
    )

    event_name = '2019-1-3-testuser-virus.json'
    bucket_filename = filename_to_bucket_key(event_name)
    handler(s3_events_dict['put'][event_name], {})
    assert not utils.has_file(s3client, UNPROCESSED_BUCKET, filename_to_bucket_key(event_name))
    assert utils.get_test_data_file_text(event_name) == utils.get_bucket_file_text(
        s3client,
        PROCESSED_BUCKET,
        os.path.join(QUARANTINE_DIR, bucket_filename)
    )
