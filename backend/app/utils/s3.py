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
