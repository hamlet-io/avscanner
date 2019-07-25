import pytest
from src import handler


@pytest.mark.usefixtures(
    "clear_buckets",
    "fill_buckets"
)
def test(s3_events_dict):
    handler(s3_events_dict['put-valid'], {})
