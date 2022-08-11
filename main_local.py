import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\night test 08.08.2022\7e7f'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

k=1

timelist = list()
offlist = list()
import matplotlib.pyplot as plt
for databatch, filepath, records, detected_data_types in data_gen:
    ADC_data = databatch[160]
    data_reshaped = np.reshape(ADC_data, (-1, 16))
    data_reshaped = np.transpose(data_reshaped)

    for idx,rec in enumerate(records):
        if rec.type == 160:
            print(f" rec num {idx}, ADC rec num num {k} ")
            k = k + 1
            timelist.append(rec.header.UnixTime + rec.header.UnixMs/1000)
            offlist.append(rec.offset)


    plt.figure()
    plt.plot(timelist)
    plt.figure()
    plt.stem(np.diff(timelist))
    print(1)



    # problem in rec 37
    # for rec in records:
    #     if rec.header.UnixTime > 1660006181:
    #         print(1)


    # if k == 814:




# edf creation part
file_path = r'result/FW13/' + local_work_directory.split('\\')[-1] +'.edf'
edfer = EDFProcessor(file_path=file_path)

edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=True)
