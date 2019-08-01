import os
import boto3
from botocore.exceptions import ClientError


class FileStore:

    def __init__(self, bucket=None, connection_conf=None):
        self.s3 = boto3.resource('s3', **connection_conf)
        self.exceptions = self.s3.meta.client.exceptions
        self.bucket = self.s3.Bucket(bucket)

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

    def copy(
        self,
        key=None,
        target_bucket=None,
        target_key=None
    ):
        copy_source = dict(
            Key=key,
            Bucket=self.bucket.name
        )
        if target_bucket:
            target_bucket = self.s3.Bucket(target_bucket)
            target_bucket.Object(key=target_key).copy(copy_source)
        else:
            self.bucket.Object(key=target_key).copy(copy_source)

    def move(
        self,
        key=None,
        target_bucket=None,
        target_key=None
    ):
        self.copy(
            key=key,
            target_key=target_key,
            target_bucket=target_bucket
        )
        self.bucket.Object(key=key).delete()
