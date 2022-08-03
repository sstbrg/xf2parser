from File import *
import os
import numpy as np
import fnmatch

@attr.define
class Parser(object):
    work_directory = attr.field(kw_only=True)
    data = attr.field(default={REC_TYPE_ADC: None,
                               REC_TYPE_MOTION_GYRO: None,
                               REC_TYPE_MOTION_ACCL: None})

    def _check_if_records_are_chronological(self, records):

        for type in [REC_TYPE_ADC, REC_TYPE_MOTION_GYRO, REC_TYPE_MOTION_ACCL, REC_TYPE_MOTION_GYRO_AND_ACCL]:
            prev_time = 0
            first_rec = True
            for rec in records:
                if ERROR_WRONG_EOR not in rec.errors and ERROR_HEADER_POINTS_BEYOND_EOF not in rec.errors:
                    if rec.header.Type == type:
                        if first_rec:
                            prev_time = rec.header.UnixTime + rec.header.UnixMs / 1000
                            first_rec = False
                        if prev_time > (rec.header.UnixTime + rec.header.UnixMs / 1000):
                            print('ERROR: FILE: the records are not time-aligned !!!')
                            return False

                        prev_time = rec.header.UnixTime + rec.header.UnixMs / 1000
        return True

    def findfiles(self, which, where='.'):
        # Returns list of filenames from `where` path matched by 'which'
        # shell pattern. Matching is case-insensitive.
        rule = re.compile(fnmatch.translate(which), re.IGNORECASE)
        return [os.path.join(where, name) for name in os.listdir(where) if rule.match(name)]







    def process_files(self, exclude=()):

        discontinuity_test_flag = 1
        import matplotlib.pyplot as plt
        first_timestamp_utx = 0
        prev_offset = 0
        dict_of_bad_samples = dict()
        dict_of_bad_recs = dict()
        dict_of_bad_recs_unix_time = dict()



        file_list = sorted(self.findfiles('*'+FILE_FORMAT, self.work_directory))
        # every file usually has 124560 samples of adc data and 94545 samples of gyro data
        # infer final array size, usually there are 1038 adc records of 3840 bytes per file and 369 motion records of size 510 bytes
        adc_data_shape = (int((3840/2)*2000) * NUMBER_OF_HW_ADC_CHANNELS, )
        gyro_data_shape = (int((510/2)*2000) * NUMBER_OF_HW_GYRO_CHANNELS, )
        accl_data_shape = (int((510/2)*2000) * NUMBER_OF_HW_ACCL_CHANNELS, )

        # create the arrays
        data = {REC_TYPE_ADC: np.zeros(adc_data_shape, dtype=np.uint16),
                REC_TYPE_MOTION_GYRO: np.zeros(gyro_data_shape, dtype=np.int16),
                REC_TYPE_MOTION_ACCL: np.zeros(accl_data_shape, dtype=np.int16)}

        # extract data
        offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}

        # flags that tell what type of data we detected
        flag_adc = False
        flag_gyro = False
        flag_accl = False



        for c, filepath in enumerate(file_list):

            print('INFO: FILE: collecting data from records of %s' % filepath)
            f = File(filepath=filepath)
            f.get_records()

            #if not self._check_if_records_are_chronological(f.records):
            #    print('ERROR: FILE: records are not chronological in file %s' % filepath)

            # we need to fill a matrix of [samples x channels]
            # in the worst case scenario, there will be one channel active so the data matrix will be [1 x all the samples]
            # we will later trim this

            # we extract the data per record
            num_of_records = len(f.records)
            print('INFO: FILE: there are %d records' % num_of_records)

            if c==0:
                t0 =  f.records[0].header.UnixTime + f.records[0].header.UnixMs/1000

            for c, rec in enumerate(f.records):
                if ERROR_WRONG_EOR not in rec.errors and ERROR_HEADER_POINTS_BEYOND_EOF not in rec.errors:
                    data_offset = int(rec.offset + rec.HeaderSize)
                    if rec.header.Type == REC_TYPE_ADC and REC_TYPE_ADC not in exclude:
                        flag_adc = True
                        data[REC_TYPE_ADC][offset[REC_TYPE_ADC]:offset[REC_TYPE_ADC] + int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='<u2')


                        prev_offset = offset[REC_TYPE_ADC]
                        offset[REC_TYPE_ADC] += int((rec.header.Length - 6) / 2)


                        # ---------------------------------------------------------- #

                        """
                        final data structure is :
                        
                        dict[num of bad ADC rec] = list(dict[num of ch] = idx of bad sample)
                        dict[num of bad ADC rec] = unix time of the "right" record
                        """

                        list_of_channels = rec.header.ChannelMap
                        number_of_channels = len(list_of_channels)
                        prev_unix_time = rec.header.UnixTime

                        #take care about c that not in every c there is adc data

                        data_to_test = data[REC_TYPE_ADC][prev_offset:offset[REC_TYPE_ADC]]
                        data_to_test = data_to_test - np.float_power(2,ADC_BITS - 1)  # ADC_RESOLUTION * (data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1))
                        data_to_test = data_to_test.astype(np.int16)
                        data_reshaped = np.reshape(data_to_test, (-1, number_of_channels))
                        data_reshaped = np.transpose(data_reshaped)

                        list_of_bad_samples = dict()
                        variance = 10 #uV
                        standart_diff = data_reshaped[0][1] - data_reshaped[0][0]

                        flag_loss_not_in_all_channels = 0
                        flag_loss_appear = 0

                        for idx, ch in enumerate(data_reshaped):
                            new_arr = np.abs(np.diff(ch))
                            bad_diff_idx_arr = np.where(new_arr >= 2 * standart_diff + variance)
                            if len(bad_diff_idx_arr[0]) != 0:
                                flag_loss_appear = 1
                                dict_of_bad_samples[idx] = bad_diff_idx_arr[0]

                        if len(dict_of_bad_samples) != number_of_channels and len(dict_of_bad_samples) != 0:
                            flag_loss_not_in_all_channels = 1

                        if flag_loss_appear == 1:
                            related_time = np.round(rec.header.UnixTime + rec.header.UnixMs / 1000 - t0, 2)
                            dict_of_bad_recs[c] = dict_of_bad_samples
                            dict_of_bad_recs_unix_time[c] = rec.header.UnixTime + rec.header.UnixMs / 1000

                               # ------------------------------------------------- #


                    elif rec.header.Type == REC_TYPE_MOTION_GYRO_AND_ACCL and REC_TYPE_MOTION_GYRO_AND_ACCL not in exclude:
                        if not flag_gyro or not flag_accl:
                            flag_gyro = True
                            flag_accl = True

                        data_from_record = np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                                         dtype='>i2')

                        data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO]
                                                                                +int((rec.header.Length - 6) / 4)] = \
                            np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[0::2], newshape=(1,-1))



                        data[REC_TYPE_MOTION_ACCL][offset[REC_TYPE_MOTION_ACCL]:offset[REC_TYPE_MOTION_ACCL] +
                                                                                int((rec.header.Length - 6) / 4)] = \
                            np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[1::2], newshape=(1,-1))

                        offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 4)
                        offset[REC_TYPE_MOTION_ACCL] += int((rec.header.Length - 6) / 4)

                    elif rec.header.Type == REC_TYPE_MOTION_ACCL and REC_TYPE_MOTION_ACCL not in exclude:
                        if not flag_accl:
                            flag_accl = True


                        data[REC_TYPE_MOTION_ACCL][offset[REC_TYPE_MOTION_ACCL]:offset[REC_TYPE_MOTION_ACCL] +
                                                                                int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='>i2')

                        offset[REC_TYPE_MOTION_ACCL] += int((rec.header.Length - 6) / 2)

                    elif rec.header.Type == REC_TYPE_MOTION_GYRO and REC_TYPE_MOTION_GYRO not in exclude:
                        if not flag_gyro:
                            flag_gyro = True

                        data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO] +
                        int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='>i2')

                        offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 2)


            # trim zeros from tail
            if flag_adc:
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC][:offset[REC_TYPE_ADC]]
            if flag_gyro:
                data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO][:offset[REC_TYPE_MOTION_GYRO]]
            if flag_accl:
                data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL][:offset[REC_TYPE_MOTION_ACCL]]

            # ADC: convert to signed
            if flag_adc:
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1) #ADC_RESOLUTION * (data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1))
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC].astype(np.int16)
            #if flag_gyro:
            #    data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO] - np.float_power(2, IMU_BITS - 1)
            #    data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO].astype(np.int16)
            #if flag_accl:
            #    data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL] - np.float_power(2, IMU_BITS - 1)
            #    data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL].astype(np.int16)

            # remove unrelevant data
            if not flag_adc:
                data.pop(REC_TYPE_ADC)
            if not flag_gyro:
                data.pop(REC_TYPE_MOTION_GYRO)
            if not flag_accl:
                data.pop(REC_TYPE_MOTION_ACCL)

            data_to_yield = data
            data = {REC_TYPE_ADC: np.empty(adc_data_shape),
                    REC_TYPE_MOTION_GYRO: np.empty(gyro_data_shape),
                    REC_TYPE_MOTION_ACCL: np.empty(accl_data_shape)}
            offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}

            yield (data_to_yield, filepath, f.records,
                   {REC_TYPE_ADC: flag_adc,
                    REC_TYPE_MOTION_ACCL: flag_accl,
                    REC_TYPE_MOTION_GYRO: flag_gyro})

        print('INFO: FILE: finished collecting data\n')
