import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'/home/stas/xtrodes/20220725v7e88v0x29v501vsine31v1'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# edf creation part
edfer = EDFProcessor(file_path=r'result/20220725v7e88v0x29v501vsine31v1.edf')

edfer.save_to_edf(data_generator=data_gen, files_metadata=parser.metadata)
