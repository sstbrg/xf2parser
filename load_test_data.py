import sys

import boto3
import fnmatch
from typing import Union
from urllib.parse import urlparse
import subprocess
import os


def sync_from_s3(s3_source, local_destination):
    print(s3_source)
    cmd = 'aws s3 sync ' + s3_source + ' ' + local_destination
    subprocess.call(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)


def search_folder(bucket, prefix, pattern, s3_client):
    folders = list()
    result = s3_client.list_objects(Bucket=bucket, Prefix=prefix, Delimiter='/')
    for o in result.get('CommonPrefixes'):
        prefix = o.get('Prefix')
        if pattern in prefix:
            folders.append(prefix)
    return folders


def download(s3_client, s3_path: str, local_filepath: str):
    """
    Downloads file stored in S3 URI <s3_path> to local file <local_filepath>.
    Must be connected to S3 via boto3 client <s3_client>.
    """
    url = urlparse(os.environ.get('INPUT', s3_path))
    s3_client.download_file(Bucket=url.netloc, Key=url.path[1:], Filename=local_filepath)


def get_paths(s3_client, bucket_name, prefix='/', delimiter='/', start_after='',
              pattern: Union[str, list, tuple] = '*'):
    """
    Returns generator object of all S3 URIs in "S3 folder" S3://<bucknet_name>/<prefix> that follows string format
     <pattern>.
    """
    prefix = prefix[1:] if prefix.startswith(delimiter) else prefix
    start_after = (start_after or prefix) if prefix.endswith(delimiter) else start_after
    s3_paginator = s3_client.get_paginator('list_objects_v2')
    for page in s3_paginator.paginate(Bucket=bucket_name, Prefix=prefix,
                                      StartAfter=start_after):  # Delimeter=delimeter to avoid recursing into subdirectories
        for content in page.get('Contents', ()):
            if type(pattern) is str:
                pattern = [pattern]
            if any([fnmatch.fnmatch(content.get('Key'), p) for p in pattern]):
                yield f's3://{bucket_name}/{content["Key"]}'


def get_files(bucket_name, pattern, prefix, s3_client):
    return list(get_paths(s3_client, bucket_name=bucket_name,
                          prefix=prefix,
                          pattern=pattern))


def download_tested_data(root_dir='DATA', pattern='tri'):
    s3_client = boto3.client('s3')
    bucket_name = 'xtrodes-danila'

    prefix = 'public/cognito/xtrodesclient/us-east-1:cc6a05a3-ebba-4ca3-b8c4-a0ac8e044d6a/'
    folders = search_folder(bucket_name, prefix, pattern, s3_client)
    for folder in folders:
        local_folder_name = f'{root_dir}/{folder.split("/")[-2]}'
        if not os.path.isdir(local_folder_name):
            sync_from_s3(f's3://{bucket_name}/{folder}', local_folder_name)
        else:
            print(f"{local_folder_name} is found locally")


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        root_dir = args[0]
        download_tested_data(root_dir)
    elif len(args) == 2:
        root_dir, pattern = args[0], args[1]
        download_tested_data(root_dir, pattern)
    else:
        download_tested_data()


if __name__ == '__main__':
    main()
