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


input = urlparse(os.environ.get('INPUT',
                                 's3://xtrodes-datasets/public/cognito/xtrodesclient/us-east-1:092b1e60-489d-44d3-99ee-92546c2fb72f/20220506_1005_13_NoApp_31_1/'))
output = urlparse(os.environ.get('OUTPUT', 's3://x-cognito/xf2parser/test_data/20220506_1005_13_NoApp_31_1.edf'))

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

# f = File(filepath=local_file_path)
parser = Parser(work_directory = local_work_directory)
parser.process_files()
edfer = EDFProcessor(file_path=local_output_path)
edfer.dump_to_edf(data_in=np.transpose(parser.data[REC_TYPE_ADC]), sample_rate=4000)

output_prefix = output.path[1:]
print('INFO: uploading %s' % output_prefix)
client.upload_file(local_output_path, 'x-cognito', output_prefix)
print('INFO: finished uploading')
