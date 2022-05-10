import natsort
from xtrbtparser.XF2Parser import *
from xtrbtparser.EDFExport import *
from botocore.config import Config
import boto3
from urllib.parse import urlparse
import os

clientconfig = Config(
   retries = {
     'max_attempts': 10,
     'mode': 'standard'
    }
)
client = boto3.client('s3', config=clientconfig)

def get_matching_s3_objects(bucket, prefix=''):
    s3 = boto3.resource('s3')
    my_bucket = s3.Bucket(bucket)
    return [object_summary.key for object_summary in my_bucket.objects.filter(Prefix=prefix)]

input = urlparse(os.environ.get('INPUT',
                                 's3://xtrodes-datasets/public/cognito/xtrodesclient/us-east-1:092b1e60-489d-44d3-99ee-92546c2fb72f/20220503_sine31hz_1mv_xf2-.~1652126233/RECORDS/'))
output = urlparse(os.environ.get('OUTPUT', 's3://x-cognito/xf2parser/asaf_fw_sine_31_1'))

# # config = {'window_size_in_samples': int(os.environ.get('WINDOW_SIZE_IN_SAMPLES', "8000")),
# #           'power_threshold': float(os.environ.get('POWER_THRESHOLD', "0.000700")),
# #           'correlation_threshold': float(os.environ.get('CORRELATION_THRESHOLD', "0.75")),
# #           'low_cutoff_frequency': int(os.environ.get('LOW_CUTOFF_FREQUENCY', "1000")),
# #           'high_cutoff_frequency': int(os.environ.get('HIGH_CUTOFF_FREQUENCY', "1500")),
# #           'filter_order': int(os.environ.get('FILTER_ORDER', "16")),
# #           'stride_size_in_samples': int(os.environ.get('STRIDE_SIZE_IN_SAMPLES', "100"))
# #           }
#
#
# download data
files = natsort.natsorted(get_matching_s3_objects(bucket=input.netloc, prefix=input.path[1:]))
for f in files:
    client.download_file(input.netloc, f, local_file_path)
print('INFO: done pulling file')

# f = File(filepath=local_file_path)
parser = Parser(work_directory = r'C:\Users\Stas\Documents\xtrodes\data\20220503_sine31hz_1mv_xf2\RECORDS')
parser.process_files()
edfer = EDFProcessor(file_path=r'C:\Users\Stas\Documents\xtrodes\data\20220503_sine31hz_1mv_xf2\adc.edf')
edfer.dump_to_edf(data_in=np.transpose(parser.data[REC_TYPE_ADC]), sample_rate=4000)

# f = File(filepath='C:\\Users\\Stas\\Documents\\xtrodes\\data\\20220503_sine31hz_1mv_xf2\\RECORDS\\TEST13.XF2')
# f.get_records()
# f.read_data()
# print(1)