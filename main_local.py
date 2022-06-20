import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\Stas\OneDrive - xtrodes\Data\7f1b session 2 sine 1mv 4hz\RECORDS'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=[])

# edf creation part
edfer = EDFProcessor(file_path=r'result\7f1b session 2 sine 1mv 4hz.edf')

edfer.save_to_edf(data_generator=data_gen, files_metadata=parser.metadata)
