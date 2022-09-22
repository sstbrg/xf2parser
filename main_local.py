import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\09.08.22 0x101\tests'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# edf creation part
edfer = EDFProcessor(file_path=r'result\ttt.edf')
if edfer.check_dataset_size(local_work_directory):
    edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=False,testing=1)



