import natsort
from XF2Parser import *
from EDFExport import *
from botocore.config import Config
import boto3
from urllib.parse import urlparse
from pathlib import Path
import os





def get_matching_s3_objects(bucket, prefix=''):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket)
    return [object_summary.key for object_summary in my_bucket.objects.filter(Prefix=prefix)]


clientconfig = Config(
   retries = {
     'max_attempts': 10,
     'mode': 'standard'
    }
)
client = boto3.client('s3', config=clientconfig)

# pull environmental variables
input = urlparse(os.environ.get('INPUT',
                                 's3://xtrodes-danila/public/cognito/xtrodesclient/us-east-1:cc6a05a3-ebba-4ca3-b8c4-a0ac8e044d6a/imu_gyro_testing_2-.~1659265183533/'))
output = urlparse(os.environ.get('OUTPUT', 's3://x-cognito/data for 1.3 HW and FW testing/HW_1.2_FW_1.3/imu_gyro_testing_2.edf'))

local_work_directory = 'data'
if not os.path.isdir(local_work_directory):
    os.mkdir(local_work_directory)
if not os.path.isdir('result'):
    os.mkdir('result')
local_output_path = os.path.join('result', 'result.edf')

# download data
files = natsort.natsorted(get_matching_s3_objects(bucket=input.netloc, prefix=input.path[1:]))

for f in files:
    if 'xf2' in Path(f).name.lower():
        local_file_path = os.path.join(local_work_directory, Path(f).name)
        if not os.path.isfile(local_file_path):
            print('INFO: downloading %s' % f)
            client.download_file(input.netloc, f, local_file_path)
print('INFO: done pulling files')

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=[])

# edf creation part

edfer = EDFProcessor(file_path=local_output_path)
if edfer.check_dataset_size(local_work_directory):
    edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=False)

output_prefix = output.path[1:]
print('INFO: uploading %s' % output_prefix)
client.upload_file(local_output_path, 'x-cognito', output_prefix)
print('INFO: finished uploading')
