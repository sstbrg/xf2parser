import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\Stas\OneDrive - xtrodes\Data\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'
local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing into npy's
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files()

databatch = next(data_gen)
# edf creation part
edfer = EDFProcessor(file_path=r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2.edf')

signal_headers = edfer.create_signal_headers_from_metadata(parser)
edfer.save_to_edf(data_generator=data_gen, files_metadata=parser.metadata, signal_headers=signal_headers)
