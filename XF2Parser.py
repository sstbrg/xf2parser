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

    def process_files(self):
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
            #num_of_records = len(f.records)
            #print('INFO: FILE: there are %d records' % num_of_records)

            detected_record_types = [x for x in f.records.keys() if len(f.records[x])]
            for type in detected_record_types:
                for c, rec in enumerate(f.records[type]):
                    if ERROR_WRONG_EOR not in rec.errors and ERROR_HEADER_POINTS_BEYOND_EOF not in rec.errors:
                        if type == REC_TYPE_ADC:
                            #flag_adc = True
                            data_offset = int(rec.offset + rec.HeaderSize)
                            data[type][offset[type]:offset[type] + int((rec.header.Length - 6)/2)] = \
                                np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                              dtype='<u2')
                            offset[type] += int((rec.header.Length - 6) / 2)

                        # this special case is needed to split the REC_TYPE_MOTION_GYRO_AND_ACCL type into GYRO and ACCL types
                        elif type == REC_TYPE_MOTION_GYRO_AND_ACCL:
                            #if not flag_gyro or not flag_accl:
                            #    flag_gyro = True
                            #    flag_accl = True

                            data_from_record = np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                                             dtype='>i2')

                            data[REC_TYPE_MOTION_ACCL][offset[REC_TYPE_MOTION_ACCL]:offset[REC_TYPE_MOTION_ACCL]
                                                                                    +int((rec.header.Length - 6) / 4)] = \
                                np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[0::2], newshape=(1,-1))

                            data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO] +
                                                                                    int((rec.header.Length - 6) / 4)] = \
                                np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[1::2], newshape=(1,-1))

                            offset[REC_TYPE_MOTION_ACCL] += int((rec.header.Length - 6) / 4)
                            offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 4)

                        elif type == REC_TYPE_MOTION_GYRO or type == REC_TYPE_MOTION_ACCL:
                            #if type == REC_TYPE_MOTION_GYRO:
                            #    flag_gyro = True
                            #elif type == REC_TYPE_MOTION_ACCL:
                            #    flag_accl = True

                            data[type][offset[type]:offset[type] +
                                                                                    int((rec.header.Length - 6)/2)] = \
                                np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                              dtype='>i2')
                            offset[type] += int((rec.header.Length - 6) / 2)

                        # elif rec.header.Type == REC_TYPE_MOTION_GYRO and REC_TYPE_MOTION_GYRO not in exclude:
                        #     if not flag_gyro:
                        #         flag_gyro = True
                        #
                        #     data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO] +
                        #     int((rec.header.Length - 6)/2)] = \
                        #         np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                        #                       dtype='>i2')
                        #
                        #     offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 2)


            # continuing our splitting of the REC_TYPE_MOTION_GYRO_AND_ACCL type
            for type in detected_record_types:
                if type == REC_TYPE_ADC:
                    flag_adc = True
                elif type == REC_TYPE_MOTION_GYRO_AND_ACCL:
                    flag_accl = True
                    flag_gyro = True
                elif type == REC_TYPE_MOTION_GYRO:
                    flag_gyro = True
                elif type == REC_TYPE_MOTION_ACCL:
                    flag_accl = True

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
