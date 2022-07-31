import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'/home/stas/xtrodes/20220728_7E88_0x41_502_sine_31_1_8ch-.~1659038988844'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# edf creation part
edfer = EDFProcessor(file_path=r'result/20220728_7E88_0x41_502_sine_31_1_8ch-.~1659038988844.edf')

edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=True)
