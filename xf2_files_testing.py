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

deleteme = 0

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

"######################################################################################################################"


def validate_periodic_signal_in_data_and_provide_vdif(signal, fs, freq):
    expected_freq_deviation = 1  # Hz
    standard_vdiff = 100  # uV

    f, Pxx_den = welch(signal, fs, nperseg=len(signal))
    maxfreq = f[np.argmax(Pxx_den)]

    if abs(maxfreq - freq) > expected_freq_deviation:
        return -1

    # todo: add calculation of vdiff(freq)
    vdiff = standard_vdiff  # todo: get rid of it

    return vdiff

def test_single_file(databatch, records, triangle_flag=0, test_on_one_channel=1, tested_freq=-1):


    fs = -1

    first_file_flag = 1
    first_adc_rec_flag = 1
    first_imu_rec_flag = 1

    num_of_channels = -1
    first_adc_rec_idx = -1
    first_imu_rec_idx = -1
    onset_in_samples = -1
    onset_in_time = -1

    records_spread_on_data_num_of_record = list()
    records_spread_on_data_onset_in_samples_not_reshaped = list()
    records_spread_on_data_onset_in_unix_time = list()
    records_spread_on_data_record_idx = list()
    num_of_recs_with_bad_adc_tdiff = list()
    vals_of_tdiff_of_recs_with_bad_adc_tdiff = list()
    num_of_recs_with_bad_adc_idxdiff = list()
    vals_of_idxdiff_of_recs_with_bad_adc_idxdiff = list()
    num_of_sample_with_bad_vdiff = list()
    vals_of_vdiff_of_sample_with_bad_vdiff = list()
    num_of_records_which_offset_in_samples_aligned_with_bad_sample_idx_in_reshaped_data = list()
    num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data = list()
    num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data = list()
    num_of_records_which_offset_in_samples_aligned_with_bad_sample_idx_in_reshaped_data = list()

    statistics = dict()
    problems_with_records = dict()
    problems_with_ADC_continuity = dict()

    # vars to calibration and tuning
    # ----------------
    time_diff_variance_percent = 0.3
    expected_time_diff = 0.03  # unix sec
    vdiff_variance_percent = 0.3

    # find the initials
    # ----------------
    if first_file_flag:



        #  todo : fs = records[0].header.??? not sure
        fs = 4000  # todo: get rid of it
        first_timestamp_in_file = records[0].header.UnixTime + records[0].header.UnixMs / 1000
        print(first_timestamp_in_file)
        offset = 0
        first_file_flag = 0


    for rec in records:
        if rec.type == REC_TYPE_ADC:
            active_channels = rec.header.ChannelMap
            num_of_channels = len(active_channels)
            first_adc_rec_idx = rec.header.PacketIndex
            first_adc_rec_flag = 0

        elif rec.type == REC_TYPE_MOTION:
            first_imu_rec_idx = rec.header.PacketIndex
            first_imu_rec_flag = 0

        elif first_adc_rec_flag == 0 and first_imu_rec_flag == 0:
            break
    # -------------------

    # loop over the records and extract the metadata
    # -------------------
    for idx, rec in enumerate(records):

        if rec.type == REC_TYPE_ADC:
            onset_in_samples = onset_in_samples + int((rec.header.Length - 6) / 2)
            records_spread_on_data_num_of_record.append(idx)

            if idx == 0:
                records_spread_on_data_onset_in_samples_not_reshaped.append(0)
            else:
                records_spread_on_data_onset_in_samples_not_reshaped.append(onset_in_samples)

            onset_in_time = rec.header.UnixTime + rec.header.UnixMs / 1000
            records_spread_on_data_onset_in_unix_time.append(onset_in_time)

            records_spread_on_data_record_idx.append(rec.header.PacketIndex)

    statistics['num_of_record'] = records_spread_on_data_num_of_record
    statistics[
        'onset_in_samples_not_reshaped'] = records_spread_on_data_onset_in_samples_not_reshaped
    statistics['onset_in_unix_time'] = records_spread_on_data_onset_in_unix_time
    statistics['records_idx'] = records_spread_on_data_record_idx
    # -------------------

    # look for problems in record's metadata
    # -------------------
    # expected_time_diff = np.mean(np.diff(records_spread_on_data_onset_in_unix_time[0:10])) * \
    #                      (1 + time_diff_variance_percent)

    num_of_recs_with_bad_adc_tdiff = np.where(np.diff(records_spread_on_data_onset_in_unix_time)
                                              > expected_time_diff * (1 + time_diff_variance_percent))[0].tolist()

    vals_of_tdiff_of_recs_with_bad_adc_tdiff = np.diff(records_spread_on_data_onset_in_unix_time)[
        num_of_recs_with_bad_adc_tdiff].tolist()

    num_of_recs_with_bad_adc_idxdiff = np.where(np.diff(records_spread_on_data_record_idx)
                                                != 1)[0].tolist()

    vals_of_idxdiff_of_recs_with_bad_adc_idxdiff = np.diff(records_spread_on_data_record_idx)[
        num_of_recs_with_bad_adc_idxdiff].tolist()

    problems_with_records['num_of_record_with_bad_tdiff'] = num_of_recs_with_bad_adc_tdiff
    problems_with_records[
        'vals_of_tdiff_of_recs_with_bad_tdiff'] = vals_of_tdiff_of_recs_with_bad_adc_tdiff

    problems_with_records['num_of_recs_with_bad_idxdiff'] = num_of_recs_with_bad_adc_idxdiff
    problems_with_records['vals_of_idxdiff_of_recs_with_bad_idxdiff'] = \
        vals_of_idxdiff_of_recs_with_bad_adc_idxdiff

    if len(num_of_recs_with_bad_adc_tdiff) != 0:
        problems_with_records['tdiff_problem_appear'] = 1
    if len(num_of_recs_with_bad_adc_idxdiff) != 0:
        problems_with_records['idx_problem_appear'] = 1

    # -------------------

    # if the ADC data is triangle, look for dataaloss in ADC data
    # -------------------
    if triangle_flag:

        ADC_data = databatch[REC_TYPE_ADC]
        data_reshaped = np.reshape(ADC_data, (-1, num_of_channels))
        data_reshaped = np.transpose(data_reshaped)

        if test_on_one_channel != 1:
            print("-------------------------------------------\n")
            print(" TEMP. ONLY TEST FOR ONE CHANNEL APPLICABLE\n")
            print("-------------------------------------------\n")
            # todo: to handle testing of all channels, and add relevant fields to the report, the logic is to see if the ADC dataloss is consistand in all channels or not
            data_to_test = data_reshaped[0]

        data_to_test = data_reshaped[0]
        abs_dif_data_to_test = abs(np.diff(data_to_test))
        records_spread_on_data_onset_in_samples_reshaped = np.floor_divide(np.array(
            records_spread_on_data_onset_in_samples_not_reshaped), num_of_channels)

        # todo: understani id the first sample is 0 and the last sample is n-1 or so
        # records_spread_on_data_onset_in_samples_reshaped = records_spread_on_data_onset_in_samples_reshaped -1

        if tested_freq == -1:
            print("\033[1;32;40m TESTED FREQ WAS NOT PROVIDED, ADC DATALOSS TESTING WAS NOT EXECUTED \n")
            pass

        expected_vdiff = validate_periodic_signal_in_data_and_provide_vdif(data_to_test, fs, tested_freq)

        if expected_vdiff == -1:
            print("\033[1;32;40m FILE DOES NOT CONTAIN PERIODIC DATA, ADC DATALOSS TESTING WAS NOT EXECUTED \n")
            pass

        num_of_sample_with_bad_vdiff = np.where(abs_dif_data_to_test > expected_vdiff * (1 + vdiff_variance_percent))[
            0].tolist()

        vals_of_vdiff_of_sample_with_bad_vdiff = abs_dif_data_to_test[num_of_sample_with_bad_vdiff]

        if len(num_of_sample_with_bad_vdiff) == 0:
            pass

        num_of_sample_with_bad_vdiff = np.array(num_of_sample_with_bad_vdiff)

        for sample_idx, data_idx in enumerate(num_of_sample_with_bad_vdiff):

            temp_between = np.where(records_spread_on_data_onset_in_samples_reshaped == data_idx)[0]

            if len(temp_between) == 0:
                temp_inside = np.where(records_spread_on_data_onset_in_samples_reshaped < data_idx)[0][-1]
                num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data.append(temp_inside)
            else:
                num_of_records_which_offset_in_samples_aligned_with_bad_sample_idx_in_reshaped_data.append(
                    temp_between[0])

        list(set(num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data))

        problems_with_ADC_continuity['num_of_record_with_bad_vdiff_between'] = \
            num_of_records_which_offset_in_samples_aligned_with_bad_sample_idx_in_reshaped_data
        problems_with_ADC_continuity['num_of_record_with_bad_vdiff_inside'] = \
            num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data

        if len(num_of_records_which_offset_in_samples_aligned_with_bad_sample_idx_in_reshaped_data) != 0:
            problems_with_ADC_continuity['dataloss_problem_appear_between'] = 1
        if len(num_of_records_with_bad_sample_idx_inside_a_record_in_reshaped_data) != 0:
            problems_with_ADC_continuity['dataloss_problem_appear_inside'] = 1



    # -------------------

    # Wrap up the output, and explain it
    # -------------------



    '''

    statistics:

        statistics['onset_in_samples_not_reshaped'] -> list:  sample stamp of each ADC record on ADC data vector
        statistics['onset_in_unix_time'] -> list: time stamp of start of each ADC recording
        statistics['records_idx'] -> list: from all records, XF2 indexes of all ADC recordings
        statistics['num_of_record'] -> list: from all records, internal indexes of only ADC recordings

    problems_with_records:

        problems_with_records['num_of_record_with_bad_tdiff'] ->
                              list: indexes of ADC records, that have bad diff in unix time with the next record
        problems_with_records['vals_of_tdiff_of_recs_with_bad_tdiff'] ->
                              list: values of the  bad diff (in seconds) for each record index above
        problems_with_records['num_of_recs_with_bad_idxdiff'] ->
                              list: indexes of ADC records, which follwing records have a wrong XF2 index
        problems_with_records['vals_of_idxdiff_of_recs_with_bad_idxdiff'] ->
                              list: values of diff in XF2 indexes between 2 records, for each record above
                              
        problems_with_records['tdiff_problem_appear'] : empty or 1 ->  appearance of the tdiff problem
        problems_with_records['idx_problem_appear'] : empty or 1  -> appearance of the idxdiff problem

    Pproblems_with_ADC_continuity:

        problems_with_ADC_continuity['num_of_record_with_bad_vdiff_between'] ->
                              list: indexes of a records, that have a dataloss between him and the following record
        problems_with_ADC_continuity['num_of_record_with_bad_vdiff_inside'] ->
                              list: indexes of a records, that have a dataloss inside the record.
                            
        problems_with_ADC_continuity['dataloss_problem_appear_between'] : empty or 1  -> appearance of the dataloss problem between the records                      
        problems_with_ADC_continuity['dataloss_problem_appear_inside']: empty or 1  -> appearance of the dataloss problem inside the record
    '''

    return statistics,problems_with_records,problems_with_ADC_continuity

def test_session(session_folder, triangle_flag=1, test_on_one_channel=1, tested_freq=31, gather_statistics = 1):
    '''

    Structure of session_dict:
        for each find that a problem was found
        session_dict[filename] = single_file_dict

    Structure of single_file_dict:
       statistics:

           statistics['onset_in_samples_not_reshaped'] -> list:  sample stamp of each ADC record on ADC data vector
           statistics['onset_in_unix_time'] -> list: time stamp of start of each ADC recording
           statistics['records_idx'] -> list: from all records, XF2 indexes of all ADC recordings
           statistics['num_of_record'] -> list: from all records, internal indexes of only ADC recordings

       problems_with_records:

           problems_with_records['num_of_record_with_bad_tdiff'] ->
                                 list: indexes of ADC records, that have bad diff in unix time with the next record
           problems_with_records['vals_of_tdiff_of_recs_with_bad_tdiff'] ->
                                 list: values of the  bad diff (in seconds) for each record index above
           problems_with_records['num_of_recs_with_bad_idxdiff'] ->
                                 list: indexes of ADC records, which follwing records have a wrong XF2 index
           problems_with_records['vals_of_idxdiff_of_recs_with_bad_idxdiff'] ->
                                 list: values of diff in XF2 indexes between 2 records, for each record above

           problems_with_records['tdiff_problem_appear'] : empty or 1 ->  appearance of the tdiff problem
           problems_with_records['idx_problem_appear'] : empty or 1  -> appearance of the idxdiff problem

       Pproblems_with_ADC_continuity:

           problems_with_ADC_continuity['num_of_record_with_bad_vdiff_between'] ->
                                 list: indexes of a records, that have a dataloss between him and the following record
           problems_with_ADC_continuity['num_of_record_with_bad_vdiff_inside'] ->
                                 list: indexes of a records, that have a dataloss inside the record.

           problems_with_ADC_continuity['dataloss_problem_appear_between'] : empty or 1  -> appearance of the dataloss problem between the records
           problems_with_ADC_continuity['dataloss_problem_appear_inside']: empty or 1  -> appearance of the dataloss problem inside the record
       '''


    gather_bad_statistic = 0

    add_file_flag = 0
    session_dict = dict()
    single_file_dict = dict()
    single_file_dict['problems'] = [None] * 4

    statistics = dict()
    problems_with_records = dict()
    problems_with_ADC_continuity = dict()


    parser = Parser(work_directory=session_folder)
    data_gen = parser.process_files(exclude=())

    count = 0

    for databatch, filepath, records, detected_data_types in data_gen:

        # todo add full recording time, file size, stats for bad files
        #todo add description about : file size
        # todo add last adc timestamp for each dataset ( last adc rec time + samples/fs )
        # todo add tests between files


        count = count +1

        single_file_dict = dict()
        statistics = dict()
        problems_with_records = dict()
        problems_with_ADC_continuity = dict()
        single_file_dict['problems'] = [None] * 4


        statistics,problems_with_records,problems_with_ADC_continuity = \
            test_single_file(databatch, records, triangle_flag, test_on_one_channel, tested_freq)

        single_file_dict['num_of_file'] = count



        if ([a for a in problems_with_records.values() if a != []]):
            single_file_dict['problems_with_records'] = problems_with_records
            if 'tdiff_problem_appear' in problems_with_records.keys():
                single_file_dict['problems'][0] = 'tdiff_problem'
            if 'idx_problem_appear' in problems_with_records.keys():
                single_file_dict['problems'][1] = 'idxdiff_problem'

            gather_bad_statistic = 1
            add_file_flag = 1

        if triangle_flag:
            if  problems_with_ADC_continuity:
                single_file_dict['problems_with_ADC_continuity'] = problems_with_ADC_continuity
                if 'dataloss_problem_appear_between' in problems_with_ADC_continuity.keys():
                    single_file_dict['problems'][2] = 'dataloss_between_recs'
                if 'dataloss_problem_appear_inside' in problems_with_ADC_continuity.keys():
                    single_file_dict['problems'][3] = 'dataloss_inside_rec'
                gather_bad_statistic = 1
                add_file_flag = 1

        if gather_bad_statistic:
            single_file_dict['statistics'] = statistics

            size_in_kb = np.round((os.path.getsize(filepath) / 1024),2)
            single_file_dict['statistics']['filesize'] = size_in_kb
            gather_bad_statistic = 0

        if gather_statistics:
            single_file_dict['statistics'] = statistics
            add_file_flag = 1


        if add_file_flag == 1:
            session_dict[filepath.split('\\')[-1]] = single_file_dict
            add_file_flag = 0
            print(1)



    # session_folder
    # savename = r'result\\FW13' + session_folder.split('\\')[-1] + '.edf'
    # edfer = EDFProcessor(file_path=savename)
    # if edfer.check_dataset_size(session_folder):
    #     edfer.save_to_edf(data_generator=data_gen, write_record_created_annotations=False)

    dict_name = session_folder.split('\\')[-1]
    with open(f'{dict_name}_results_dict.pkl', 'wb') as f:
        pickle.dump(session_dict, f)


    print(dict_name)



    return dict_name,session_dict



def save_to_excel(dict_name,session_dict):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active

    #todo add headers : A - filename
    # B - bad tdiff idx
    # C - bad tdif vals
    # D - bad idx idx
    # E - bad idx val
    # F - bad data idx (between)
    # G - bad data val (between)
    # F - bad data idx (inside)
    # G - bad data val (inside)


    Acount = 1
    Aplace = 'A' + str(Acount)
    Bcount = 2
    Bplace = 'B' + str(Bcount)

    places = ['A','B','C','D','E','F','G']

    for item in session_dict.items():

        Aplace = 'A' + str(Acount)
        wb[places[0]] = item[0] # file name to A row
        wb[places[1] + str(1)] = 'idx_of_record_with_bad_tdiff'
        wb[places[2] + str(1)] = 'vals_of_tdiff_of_recs_with_bad_tdiff'
        wb[places[3] + str(1)] = 'num_of_recs_with_bad_idxdiff'
        wb[places[4] + str(1)] = 'vals_of_idxdiff_of_recs_with_bad_idxdiff'
        Acount = Acount + 1


        file_dict = item[1]
        rec_problems = file_dict['problems_with_records']
        list_num_of_record_with_bad_tdiff = rec_problems['num_of_record_with_bad_tdiff']
        list_vals_of_tdiff_of_recs_with_bad_tdiff = rec_problems['vals_of_tdiff_of_recs_with_bad_tdiff']
        list_num_of_recs_with_bad_idxdiff = rec_problems['num_of_recs_with_bad_idxdiff']
        list_vals_of_idxdiff_of_recs_with_bad_idxdiff = rec_problems['vals_of_idxdiff_of_recs_with_bad_idxdiff']


        for item in list_num_of_record_with_bad_tdiff:
            wb





    wb['A1'] = dict_name
    # wb['B2'] = session_dict[]
    wb.save("sample.xlsx")
    wb.close()
    pass



def test_chunk_of_sesions_and_create_statistics():
    pass


local_work_directory = r'C:\Users\ivan\OneDrive - xtrodes\Desktop\DATA\SD test\30VSD -7e7f test2'

# dict_name, _ = test_session(local_work_directory, triangle_flag=0, test_on_one_channel=0, tested_freq=0,gather_statistics=0)


dd = local_work_directory.split('\\')[-1] + '_results_dict.pkl'
# dict_name ='30VSD -7e7f test2_results_dict.pkl'
dict_name =dd
with open(f'{dict_name}', 'rb') as f:
    loaded_dict = pickle.load(f)
    print("done")


    # import csv
    #
    # new_path = open("mytest.csv", "w")
    # z = csv.writer(new_path)
    #
    #
    # # for new_k, new_v in loaded_dict.items():
    # #     z.writerow([new_k, new_v])
    #
    #
    # for filename,filedict in loaded_dict.items() :
    #     z.writerow([filename])
    #     for key,val in filedict.items():
    #         z.writecol([key])
    #
    #
    #     a = [1,2,3]
    #     b = [1,2]
    #
    #
    # new_path.close()
    # print("done")
