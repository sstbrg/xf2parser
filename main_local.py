import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\Stas\OneDrive - xtrodes\Data\hw 1.2 fw 1.3\HW_1.2_FW_1.3\20220621_02C3_HW_1.2_FW_14.6.0.25_sine_31hz_1mv\RECORDS'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=[])

# edf creation part
edfer = EDFProcessor(file_path=r'result\20220621_02C3_HW_1.2_FW_14.6.0.25_sine_31hz_1mv.edf')

edfer.save_to_edf(data_generator=data_gen, files_metadata=parser.metadata)
