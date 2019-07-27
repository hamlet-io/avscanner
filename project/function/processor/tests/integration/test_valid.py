import pytest
from src import handler


@pytest.mark.usefixtures(
    "clear_buckets",
    "fill_buckets"
)
def test(s3_events_dict):
    handler(s3_events_dict['put']['2019-1-1-testuser-valid'], {})
    handler(s3_events_dict['put']['2019-1-2-testuser-invalid'], {})
    handler(s3_events_dict['put']['2019-1-3-testuser-virus'], {})
