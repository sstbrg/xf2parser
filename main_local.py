import numpy as np

from XF2Parser import *
from EDFExport import *
local_work_directory = r'C:\Users\ivan\PycharmProjects\xf2parser\discontivity_tests\2ch'
#local_work_directory = r'/home/gonen/PycharmProjects/xf2parser/data'
#local_output_prefix = r'result\DAU-13-6 old-hardware-new-FW-gyro-acc-fix-20220613_sine_3hz_1v_2'

# parsing
parser = Parser(work_directory=local_work_directory)
data_gen = parser.process_files(exclude=())

# This feature run over the all XF2 files, and calculates if there are points of Discontinuity
# It outputs the num of record, its unix time , and the problematic sample

# How to - Need to create a loop on the xf2 folder, take from the iterator the timestamp of the first sample of the first record of the first file, than run over
# each 3 records with offset of 1 record, if the sample is "Bad", output the record num, its timestamp and calculate time between the first sample of the record to the bad sample

#

dict_of_bad_records_unix_times = dict()
dict_of_bad_samples = dict()
first_file_flag = 1
total_offset = 0

left_data_offset = 0
right_data_offset = 0
temp_offset = 0
active_channels = list()

def reshape_and_test_data(data,channels):

    flag_loss_not_in_all_channels =0
    flag_loss_appear =0
    num_of_channels = len(channels)
    data_reshaped = np.reshape(data, (-1, num_of_channels))
    data_reshaped = np.transpose(data_reshaped)

    list_of_bad_samples = dict()

    variance = 10 #uV
    try:
        standart_diff = data_reshaped[0][1] - data_reshaped[0][0]
    except:
        standart_diff = 0

    for idx, ch in enumerate(data_reshaped):
        new_arr = np.abs(np.diff(ch))
        bad_diff_idx_arr = np.where(new_arr >= 2*standart_diff + variance)
        if len(bad_diff_idx_arr[0]) != 0:
            flag_loss_appear = 1
            dict_of_bad_samples[idx] = bad_diff_idx_arr[0]

    if len(dict_of_bad_samples) != num_of_channels and len(dict_of_bad_samples) != 0:
        flag_loss_not_in_all_channels = 1

    return flag_loss_appear,flag_loss_not_in_all_channels,list_of_bad_samples


for  databatch, filepath, records, detected_data_types in data_gen:


    if first_file_flag:
        filename = filepath.split("\\")[-1]
        t0 = records[0].header.UnixTime + records[0].header.UnixMs/1000
        first_packet_idx = records[0].header.PacketIndex
        active_channels = records[0].header.ChannelMap
        num_of_channels = len(active_channels)
        first_file_flag = 0

    ADC_data = databatch[160]

    for idx,rec in enumerate(records):
        if rec.type == 160:
            # length = length + rec.header.Length
            if(idx == 0):
                right_data_offset = right_data_offset + rec.header.Length
                pass

            # temp_offset = right_data_offset
            # right_data_offset = right_data_offset + int((rec.header.Length - 6)/2)
            # data_to_test = ADC_data[left_data_offset:right_data_offset]
            # if right_data_offset >= len(ADC_data):
            #     print(1)
            #     continue


            flag_loss_appear,flag_loss_not_in_all_channels,list_of_bad_samples = reshape_and_test_data(ADC_data,active_channels)
            left_data_offset = temp_offset


            if flag_loss_appear == 1:
                related_time = np.round(rec.header.UnixTime + rec.header.UnixMs / 1000 - t0,2)
                # print(f" problem is file {filename} in record {idx}, relevant EDF time is {related_time} ")
                dict_of_bad_records_unix_times[idx] = related_time

    print(1)







# edf creation part
# edfer = EDFProcessor(file_path=r'result/20220728_7E88_0x41_502_sine_31_1_8ch-.~1659038988844.edf')
#
# edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=True)
