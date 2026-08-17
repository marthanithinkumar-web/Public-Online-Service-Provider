import os

# Placeholder S3 helper. Requires boto3 and AWS credentials in environment to work.
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None


def upload_file_to_s3(local_path: str, bucket: str, key: str) -> bool:
    if boto3 is None:
        raise RuntimeError('boto3 not installed')
    s3 = boto3.client('s3')
    try:
        s3.upload_file(local_path, bucket, key)
        return True
    except (BotoCoreError, ClientError) as e:
        print('S3 upload failed', e)
        return False
