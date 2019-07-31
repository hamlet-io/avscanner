from botocore.exceptions import ClientError


def has_file(client, bucket, key):
    try:
        client.get_object(
            Bucket=bucket,
            Key=key
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return False
        raise


def get_bucket_file_text(client, bucket, key):
    try:
        response = client.get_object(
            Bucket=bucket,
            Key=key
        )
        return response['Body'].read().decode('utf8')
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None
        raise
