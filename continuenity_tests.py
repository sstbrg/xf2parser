from XF2Parser import *
from EDFExport import *


import pyedflib
import matplotlib.pyplot as plt
import numpy as np

# local_work_directory = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\night test 08.08.2022\7e88'
#
# parser = Parser(work_directory=local_work_directory)
# data_gen = parser.process_files(exclude=())

import os

import csv

"###################################S3 Convenience functions and results storing (misha) ###########################################"


def save_dict_as_csv(dict, fname):
    w = csv.writer(open(fname, "w"))
    for key, val in dict.items():
        w.writerow([key, val])


"######################################################################################################################"


def test_single_file(databatch, records):
    ADC_data_code = 160
    first_file_flag = 1
    loss_flag = 0
    not_between_recs_flag = 0
    next_PacketIndex = 0

    variance = 0  # uV
    offset = 0
    num_of_rec = 1
    num_of_channels = 0

    records_idxs_list = list()
    bad_sample_list = list()
    bad_diff_val_list = list()
    bad_rec_num_list = list()
    bad_rec_num_inside_rec_list = list()
    timelist = list()
    offlist = list()
    packedIdx_list = list()
    bad_file_dict = dict()

    if first_file_flag:
        t0 = records[0].header.UnixTime + records[0].header.UnixMs / 1000
        first_packet_idx = records[0].header.PacketIndex
        first_file_flag = 0
        offset = 0

    for rec in records:
        if rec.type == ADC_data_code:
            active_channels = rec.header.ChannelMap
            num_of_channels = len(active_channels)
            break

    for idx, rec in enumerate(records):
        if rec.type == ADC_data_code:
            offset = offset + int((rec.header.Length - 6) / 2)
            records_idxs_list.append(offset)
            timelist.append(rec.header.UnixTime + rec.header.UnixMs / 1000)
            packedIdx_list.append(rec.header.PacketIndex)
            offlist.append(rec.offset)

    # finding problem with continuous of timestamps and recording indexes
    good_timediff = np.diff(timelist)[0]
    bad_tdif_idxs = np.where(np.diff(timelist) > 1.5 * good_timediff)[0]
    bad_tdif_vals = np.diff(timelist)[bad_tdif_idxs]
    bad_tdif = (bad_tdif_idxs, bad_tdif_vals)

    bad_packIdx_idxs = np.where(np.diff(packedIdx_list) != 1)[0]
    bad_packIdx_vals = np.diff(packedIdx_list)[bad_packIdx_idxs]
    bad_packIdx = (bad_packIdx_idxs, bad_packIdx_vals)

    bad_file_dict[
        "recs_with_bad_tdiff"] = bad_tdif  # tuple of 2 lists : num of left record with bad time diff and the value of bad time diff
    bad_file_dict[
        "recs_with_bad_PacketIndex_diff"] = bad_packIdx  # tuple of 2 lists : num of the rec, before the rec with wrong packetID and the "wrong jump" in index

    # create a data matrix and records on samples
    ADC_data = databatch[ADC_data_code]

    data_reshaped = np.reshape(ADC_data, (-1, num_of_channels))
    data_reshaped = np.transpose(data_reshaped)
    data_to_test = data_reshaped[0]
    abs_dif_data_to_test = abs(np.diff(data_to_test))

    records_idxs_list_reshaped = np.floor_divide(np.array(records_idxs_list), num_of_channels)
    records_idxs_list_reshaped = records_idxs_list_reshaped - 1

    standart_diff = 100

    for data_sample_num, data_diff_val in enumerate(abs_dif_data_to_test):
        if data_diff_val > standart_diff + variance:
            loss_flag = 1
            bad_sample_list.append(data_sample_num)
            bad_diff_val_list.append(data_diff_val)

    if (loss_flag):
        loss_flag = 0
        bad_sample_list = np.array(bad_sample_list)
        for sample_idx, sample_val in enumerate(bad_sample_list):
            temp = np.where(records_idxs_list_reshaped == sample_val)

            if len(temp[0]) == 0:
                if (sample_idx == 0):
                    rec_num = 0
                else:
                    temp = np.where(bad_sample_list < sample_idx)
                    rec_num = temp[0][-1]
                bad_rec_num_inside_rec_list.append([rec_num])
            else:
                rec_num = temp[0][0]
                bad_rec_num_list.append([rec_num])

            bad_file_dict["recs_with_dataloss_after"] = bad_rec_num_list
            bad_file_dict["recs_with_dataloss_inside"] = bad_rec_num_inside_rec_list

    if (len(bad_rec_num_list) == len(bad_rec_num_inside_rec_list) == len(bad_packIdx[0]) == len(bad_tdif[0]) == 0):

        bad_file_dict["isempty"] = 1
    else:
        bad_file_dict["isempty"] = 0

    # free all vers for the next file
    records_idxs_list = list()
    bad_sample_list = list()
    bad_diff_val_list = list()
    bad_rec_num_list = list()
    timelist = list()
    offlist = list()

    return bad_file_dict


def continuenity_test(data_gen):
    session_dict = dict()
    i = 0
    for databatch, filepath, records, detected_data_types in data_gen:
        single_file_dict = test_single_file(databatch, records)
        if single_file_dict['isempty'] != 1:
            i += 1
            if i > 10:
                session_dict[filepath.split('\\')[-1]] = single_file_dict
    return session_dict


def main():
    rootdir = 'DATA'
    results_subdir = 'continuity_results'
    for file in os.listdir(rootdir):
        d = os.path.join(rootdir, file)
        if os.path.isdir(d):
            local_work_directory = d
            parser = Parser(work_directory=local_work_directory)
            data_gen = parser.process_files(exclude=())
            try:
                session_dict = continuenity_test(data_gen)
            except Exception as e:
                print(f'Error in {local_work_directory} dataset : {str(e)}')
                continue
            print(session_dict)
            if len(list(session_dict.keys())) != 0:
                save_dict_as_csv(session_dict, f'{d}_continuity_stats.csv')
            else:
                print(f'Empty output in {d}')


if __name__ == '__main__':
    main()
