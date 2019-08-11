from unittest import mock
from processor.dao import conf


@mock.patch('processor.dao.conf.os.environ', {})
def test_configs_not_set():
    assert len(conf.get_sqs_env_conf()) == 0
    assert len(conf.get_s3_env_conf()) == 0


@mock.patch('processor.dao.conf.os.environ', {
    "AWS_S3_ACCESS_KEY_ID": "s3_access",
    "AWS_S3_SECRET_ACCESS_KEY": "s3_secret",
    "AWS_S3_ENDPOINT_URL": "s3_endpoint",
    "AWS_S3_REGION": "s3_region"
})
def test_s3_env_conf():
    assert conf.get_s3_env_conf() == {
        "aws_access_key_id": "s3_access",
        "aws_secret_access_key": "s3_secret",
        "endpoint_url": "s3_endpoint",
        "region_name": "s3_region"
    }


@mock.patch('processor.dao.conf.os.environ', {
    "AWS_SQS_ACCESS_KEY_ID": "sqs_access",
    "AWS_SQS_SECRET_ACCESS_KEY": "sqs_secret",
    "AWS_SQS_ENDPOINT_URL": "sqs_endpoint",
    "AWS_SQS_REGION": "sqs_region"
})
def test_sqs_env_conf():
    assert conf.get_sqs_env_conf() == {
        "aws_access_key_id": "sqs_access",
        "aws_secret_access_key": "sqs_secret",
        "endpoint_url": "sqs_endpoint",
        "region_name": "sqs_region"
    }
