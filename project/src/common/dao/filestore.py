import os
import boto3
from botocore.exceptions import ClientError


class FileStore:

    def __init__(self, bucket=None, connection_conf=None):
        s3 = boto3.resource('s3', **connection_conf)
        self.exceptions = s3.meta.client.exceptions
        self.bucket = s3.Bucket(bucket)

    def get(
        self,
        key=None,
        etag=None
    ):
        object = self.bucket.Object(
            key=key
        )
        get_params = dict()
        if etag:
            get_params['IfMatch'] = etag
        try:
            return object.get(**get_params)
        except self.exceptions.NoSuchKey:
            return None
        except ClientError as e:
            code = e.response['Error']['Code']
            if code == 'PreconditionFailed':
                return None
            raise

    def post(self, key=None, body=None):
        object = self.bucket.Object(key=key)
        object.put(
            Body=body
        )
        return True

    def download(
        self,
        path=None,
        key=None,
        recursive=False
    ):
        if recursive:
            if not os.path.isdir(path):
                raise ValueError('Recursive path must be dir')
            if key and not key.endswith('/'):
                raise ValueError(f'Recursive key prefix must end with /. Key:{key}')
            objects = self.bucket.objects.filter(
                Prefix=key
            )
            for summary in objects:
                object = summary.Object()
                filename = os.path.join(
                    path,
                    object.key[len(key):]
                )
                object.download_file(
                    Filename=filename
                )
        else:
            object = self.bucket.Object(key)
            object.download_file(
                Filename=path
            )
