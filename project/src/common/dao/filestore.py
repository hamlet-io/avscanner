import boto3


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

    def post(self, key=None, data=None):
        object = self.bucket.Object(key=key)
        object.put(
            Body=data
        )
        return True
