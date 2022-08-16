import numpy as np
import matplotlib.pyplot as plt

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\0x55\tests\20220813_7f0d_0x55_5047_noinp_14ch'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# edf creation part

adc_timelist = list()
imu_timelist = list()
gyro_timelist = list()

adc_IDX_list = list()
imu_IDX_list = list()
gyro_IDX_list = list()

for databatch, filepath, records, detected_data_types in data_gen:

    ADC_data = databatch[160]
    name = filepath.split('\\')[-1]



    # if name == "20220813204943.xf2":
    for rec in records:
        if len(rec.errors) != 0:
            print(1)

        print(2)

        if rec.header.Type == REC_TYPE_ADC:
            adc_timelist.append(rec.header.UnixTime + rec.header.UnixMs / 1000)
            adc_IDX_list.append(rec.header.PacketIndex)

        if rec.header.Type == 3:
            imu_timelist.append(rec.header.UnixTime + rec.header.UnixMs / 1000)
            imu_IDX_list.append(rec.header.PacketIndex)

    print(1)










# savename = "result/FW13" + local_work_directory.split('\\')[-1] + '.edf'
# edfer = EDFProcessor(file_path = savename)
# edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=False)
