import os
import posixpath
import boto3
from botocore.exceptions import ClientError
# from common import loggers
from . import utils


class FileChangedError(Exception):
    pass


def is_precondition_failed_error(e):
    code = e.response['Error']['Code']
    return code in ['PreconditionFailed', '412']


class FileStore:

    def __init__(self, bucket=None, connection_conf=None):
        self.s3 = boto3.resource('s3', **connection_conf)
        self.exceptions = self.s3.meta.client.exceptions
        self.__bucket_name = bucket

    @property
    def bucket(self):
        try:
            return self.__bucket
        except AttributeError:
            self.__bucket = self.s3.Bucket(self.__bucket_name)
            return self.__bucket

    def get(
        self,
        key=None,
        etag=None
    ):
        object = self.bucket.Object(
            key=key
        )
        get_params = utils.to_aws_params(
            IfMatch=etag
        )
        try:
            return object.get(**get_params)
        except self.exceptions.NoSuchKey:
            return None
        except ClientError as e:
            if is_precondition_failed_error(e):
                return None
            raise  # pragma: no cover

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
        recursive=False,
        etag=None
    ):
        if recursive:
            if not os.path.isdir(path):
                raise ValueError('Recursive path must be dir')
            if key and not key.endswith('/'):
                raise ValueError(f'Recursive key prefix must end with /. Key:{key}')
            objects = self.bucket.objects.filter(
                Prefix=key
            )
            downloaded = 0
            for summary in objects:
                object = summary.Object()
                filename = os.path.join(
                    path,
                    posixpath.relpath(summary.key, key)
                )
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                object.download_file(
                    Filename=filename
                )
                downloaded += 1
            return downloaded
        else:
            response = self.get(
                key=key,
                etag=etag
            )
            if response is None:
                raise FileChangedError()
            with open(path, 'wb') as f:
                f.write(response['Body'].read())
            return 1

    def copy(
        self,
        key=None,
        etag=None,
        target_bucket=None,
        target_key=None,
    ):
        params = dict(
            CopySource=dict(
                Key=key,
                Bucket=self.bucket.name
            ),
            ExtraArgs=utils.to_aws_params(
                CopySourceIfMatch=etag
            )
        )
        try:
            if target_bucket:
                target_bucket = self.s3.Bucket(target_bucket)
                target_bucket.Object(key=target_key).copy(**params)
            else:
                self.bucket.Object(key=target_key).copy(**params)
        except ClientError as e:
            if is_precondition_failed_error(e):
                raise FileChangedError() from e
            raise  # pragma: no cover

    def move(
        self,
        key=None,
        etag=None,
        target_bucket=None,
        target_key=None
    ):
        self.copy(
            key=key,
            etag=etag,
            target_key=target_key,
            target_bucket=target_bucket
        )
        self.bucket.Object(key=key).delete()

    def delete(
        self,
        key=None,
        etag=None,
        recursive=False
    ):
        if recursive:
            objects = self.bucket.objects.filter(
                Prefix=key
            )
            deleted = 0
            for summary in objects:
                summary.Object().delete()
                deleted += 1
            return deleted
        object = self.bucket.Object(key=key)
        if etag is not None and object.e_tag != etag:
            raise FileChangedError()
        object.delete()
        return 1
