from unittest import mock
from processor.dao import filestore
from processor.dao import conf


def test():
    filestore.Quarantine(conf.get_s3_env_conf())
    filestore.Unprocessed(conf.get_s3_env_conf())
    filestore.Archive(conf.get_s3_env_conf())


@mock.patch('processor.dao.filestore.UNPROCESSED_BUCKET', None)
@mock.patch('processor.dao.filestore.ARCHIVE_BUCKET', None)
@mock.patch('processor.dao.filestore.QUARANTINE_BUCKET', None)
def test_no_name_initialization():
    assert filestore.ARCHIVE_BUCKET is None
    assert filestore.QUARANTINE_BUCKET is None
    assert filestore.UNPROCESSED_BUCKET is None
    filestore.Quarantine(conf.get_s3_env_conf())
    filestore.Unprocessed(conf.get_s3_env_conf())
    filestore.Archive(conf.get_s3_env_conf())
