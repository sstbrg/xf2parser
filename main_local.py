
from XF2Parser import *
from EDFExport import *
# local_work_directory = r'C:\Users\sstbr\Documents\xtrodes'
# local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data/11-8'
local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data/14--8_small_file_issue'

#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# edf creation part
edfer = EDFProcessor(file_path=r'/home/gonen/PycharmProjects/xf2parser/data/output.edf')

edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=False)
