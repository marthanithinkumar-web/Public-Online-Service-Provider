import os

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None


def s3_client():
    if boto3 is None:
        raise RuntimeError('boto3 not installed')
    options = {}
    if os.getenv('S3_ENDPOINT_URL'):
        options['endpoint_url'] = os.environ['S3_ENDPOINT_URL']
    if os.getenv('AWS_REGION'):
        options['region_name'] = os.environ['AWS_REGION']
    return boto3.client('s3', **options)


def upload_file_to_s3(local_path: str, bucket: str, key: str) -> bool:
    try:
        s3_client().upload_file(local_path, bucket, key)
        return True
    except (BotoCoreError, ClientError) as e:
        print('S3 upload failed', e)
        return False


def presigned_download(bucket: str, key: str, expires: int = 300) -> str:
    return s3_client().generate_presigned_url(
        'get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=expires
    )


def delete_stored_file(stored_path: str) -> None:
    """Delete an attachment from S3-compatible storage or the local fallback.

    S3 DeleteObject is idempotent, so retrying cleanup is safe when an earlier
    request removed the object but did not finish its database transaction.
    """
    value = str(stored_path or '')
    if value.startswith('s3://'):
        bucket_and_key = value.removeprefix('s3://').split('/', 1)
        if len(bucket_and_key) != 2 or not all(bucket_and_key):
            raise ValueError('Invalid S3 attachment path')
        bucket, key = bucket_and_key
        client = s3_client()
        versions = client.list_object_versions(Bucket=bucket, Prefix=key)
        stored_versions = [
            item for group in ('Versions', 'DeleteMarkers')
            for item in versions.get(group, [])
            if item.get('Key') == key and item.get('VersionId')
        ]
        if stored_versions:
            for item in stored_versions:
                client.delete_object(Bucket=bucket, Key=key, VersionId=item['VersionId'])
        else:
            client.delete_object(Bucket=bucket, Key=key)
        return
    if value and os.path.exists(value):
        os.remove(value)
