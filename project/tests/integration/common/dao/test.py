import os
import pytest
from common.dao.filestore import FileStore
from tests.integration.conftest import ARCHIVE_BUCKET


BUCKET = ARCHIVE_BUCKET
FILES = {
    'valid/one.txt': 'one content'.encode(),
    'valid/two.txt': 'two content'.encode()
}

CONNECTION_CONF = dict(
    aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
    endpoint_url=os.environ['AWS_S3_ENDPOINT_URL']
)

DOWNLOAD_PATH = '/tmp/test'
RECURSIVE_DOWNLOAD_PATH = '/tmp'


@pytest.mark.usefixtures(
    'clear_buckets'
)
def test_filestore():
    filestore = FileStore(
        bucket=BUCKET,
        connection_conf=CONNECTION_CONF
    )

    for key, body in FILES.items():
        assert filestore.get(key=key) is None
        filestore.post(key=key, body=body)
        fileobj = filestore.get(key=key)
        assert fileobj is not None
        try:
            os.remove(DOWNLOAD_PATH)
        except FileNotFoundError:
            pass
        filestore.download(
            path=DOWNLOAD_PATH,
            key=key
        )
        assert os.path.exists(DOWNLOAD_PATH)
        with open(DOWNLOAD_PATH, 'rb') as f:
            assert f.read() == fileobj['Body'].read()
        os.remove(DOWNLOAD_PATH)

    filestore.download(
        path=RECURSIVE_DOWNLOAD_PATH,
        key='valid/',
        recursive=True
    )

    files = os.listdir(RECURSIVE_DOWNLOAD_PATH)
    assert len(files) == 2
    for file in files:
        filename = os.path.join(RECURSIVE_DOWNLOAD_PATH, file)
        with open(filename, 'rb') as f:
            assert f.read() == filestore.get(key=f'valid/{file}')['Body'].read()
        os.remove(filename)
