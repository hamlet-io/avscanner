import os
from common.dao.filestore import FileStore


def test_filestore():
    connection_conf = dict(
        aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        endpoint_url=os.environ['AWS_S3_ENDPOINT_URL']
    )
    filestore = FileStore(
        bucket='processed',
        connection_conf=connection_conf
    )
    filestore.post(
        key='hello-world.txt',
        data='Hello world!'.encode()
    )
    fileobj = filestore.get(
        key='hello-world.txt',
        etag='HeyHey'
    )
    assert fileobj is None
