

"""

Example of a code for iterating over XF2 files for QA data integrity tests

"""
from XF2Parser import *
from EDFExport import *
import pyedflib
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import welch
import pickle
import os
import csv
import collections


pass_to_folder = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\0x101\sanity'

def corr_test(dataschunk_onset):
    pass
def dummy_test():
    pass

def iterate_over_xf2_files(pass_to_folder,corr_flag,dummy_flag):



    parser = Parser(work_directory=pass_to_folder)
    data_gen = parser.process_files(exclude=())

    files_count_corr = 0
    files_count_dummy = 0
    num_of_files_for_corr = 5
    num_of_files_for_dummy = 2

    first_file_flag = 1
    num_of_channels = 16 # updated later

    first_timestamp_in_unix_time = 0 # updated later

    data_chunk_corr = list()  # can be improved to allocated np array with len of X files * pre-calculated num of samples - zero trimming
    data_chunk_dummy = list()  # can be improved to allocated np array with len of X files * pre-calculated num of samples - zero trimming


    for databatch, filepath, records, detected_data_types in data_gen:


    # handle if the file is zero - sized
        if len(records) == 0:
            continue

    # find the first time of the whole recording stamp in unix time
        if first_file_flag:
            for rec in records:
                if rec.type == REC_TYPE_ADC:
                    first_timestamp_in_unix_time = records[0].header['UnixTime'] + records[0].header['UnixMs'] / 1000
                    first_file_flag = 0
                    break

        # find the first time of the batch of data
        for rec in records:
            if rec.type == REC_TYPE_ADC:
                active_channels = rec.header.ChannelMap
                num_of_channels = len(active_channels)
                first_ts_of_the_file_for_dummy = rec.header['UnixTime'] + rec.header['UnixMs'] / 1000
                first_ts_of_the_file_for_corr = rec.header['UnixTime'] + rec.header['UnixMs'] / 1000
                break

        #create chunks of data for corr and for dummy

        ADC_data_not_reshaped = databatch[REC_TYPE_ADC]
        data_reshaped = np.reshape(ADC_data_not_reshaped, (-1, num_of_channels))
        data_reshaped = np.transpose(data_reshaped)


        if corr_flag:
            #lets collect data, and after the chunk is full, test it
            if files_count_corr == 0:
                # initiate a matrix
                data_chunk_corr = data_reshaped
                # save a timestamp of the first sample in first file in the data chunk
                first_ts_of_datachunk_for_corr = first_ts_of_the_file_for_corr
                files_count_corr = files_count_corr +1
            elif files_count_corr < num_of_files_for_corr:
                data_chunk_corr = np.append(data_chunk_corr,data_reshaped)
                files_count_corr = files_count_corr + 1
            elif files_count_corr == num_of_files_for_corr:
                # data_chunk_dummy already have num_of_files_for_corr datasets inside
                # so we can make a correlation and handle the output data
                pass_fail_flag,timestamps = corr_test(first_ts_of_datachunk_for_corr)
                #code to append timestamps to an array or something

                #free all
                files_count_corr = 0
                data_chunk_corr = 0 #just to be sure the variable is free
                first_ts_of_datachunk_for_corr = 0
            else:
                #handle_error or smt
                print(1)


        if dummy_flag:
            if files_count_dummy == 0:
                # initiate a matrix
                data_chunk_dummy = data_reshaped
                # save a timestamp of the first sample in first file in the data chunk
                first_ts_of_datachunk_for_dummy = first_ts_of_the_file_for_dummy
                files_count_dummy = files_count_dummy + 1
            elif files_count_corr < num_of_files_for_dummy:
                data_chunk_dummy = np.append(data_chunk_dummy, data_reshaped)
                files_count_dummy = files_count_dummy + 1
            elif files_count_corr == num_of_files_for_dummy:
                # data_chunk_dummy already have num_of_files_for_corr datasets inside
                # so we can make a correlation and handle the output data
                pass_fail_flag, bad_files_names = dummy_test()
                # code to append timestamps to an array or something

                # free all
                files_count_dummy = 0
                data_chunk_dummy = 0  # just to be sure the variable is free
                first_ts_of_datachunk_for_dummy = 0
            else:
                # handle_error or smt
                print(1)






