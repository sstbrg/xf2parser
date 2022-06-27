from File import *
from glob import glob
from natsort import natsorted
import os
import numpy as np

@attr.define
class Parser(object):
    work_directory = attr.field(kw_only=True)
    data = attr.field(default={REC_TYPE_ADC: None,
                               REC_TYPE_MOTION_GYRO: None,
                               REC_TYPE_MOTION_ACCL: None})
    metadata = attr.field(default=list())

    def process_files(self, exclude=()):
        file_list = natsorted([x for x in glob(os.path.join(self.work_directory, '*'+FILE_FORMAT))])
        # every file usually has 124560 samples of adc data and 94545 samples of gyro data

        # infer final array size, usually there are 1038 adc records of 3840 bytes per file and 369 motion records of size 510 bytes

        adc_data_shape = (int((3840/2)*2000) * NUMBER_OF_HW_ADC_CHANNELS, )
        gyro_data_shape = (int((510/2)*2000) * NUMBER_OF_HW_GYRO_CHANNELS, )
        accl_data_shape = (int((510/2)*2000) * NUMBER_OF_HW_ACCL_CHANNELS, )

        # create the arrays
        data = {REC_TYPE_ADC: np.zeros(adc_data_shape, dtype=np.uint16),
                REC_TYPE_MOTION_GYRO: np.zeros(gyro_data_shape, dtype=np.uint16),
                REC_TYPE_MOTION_ACCL: np.zeros(accl_data_shape, dtype=np.uint16)}

        # extract data
        offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}

        # metadata flags
        flag_adc_metadata = False
        flag_gyro_metadata = False
        flag_accl_metadata = False

        for c, filepath in enumerate(file_list):

            print('INFO: collecting data from records of %s' % filepath)
            f = File(filepath=filepath)
            f.get_records()
            # we need to fill a matrix of [samples x channels]
            # in the worst case scenario, there will be one channel active so the data matrix will be [1 x all the samples]
            # we will later trim this

            # we extract the data per record
            num_of_records = len(f.records)
            print('INFO: there are %d records' % num_of_records)

            for c, rec in enumerate(f.records):
                # notify about errors
                if ERROR_WRONG_CRC in rec.errors:
                    print('ERROR: Skipping record data. Record %d has a wrong CRC' % c)
                if ERROR_WRONG_EOR in rec.errors:
                    print('WARNING: Skipping record data. Start of record (SOR) in record %d does not point to an actual record. ' 
                          'This is most likely becuase the SOR byte is part of the data.' % c)
                if ERROR_WRONG_SOR_IN_HEADER in rec.errors:
                    print('ERROR: Skipping record data. Wrong start of record (SOR) byte found in record header')
                if ERROR_WRONG_EOR not in rec.errors:
                    data_offset = int(rec.offset + rec.HeaderSize)
                    if rec.header.Type == REC_TYPE_ADC and REC_TYPE_ADC not in exclude:
                        # save metadata
                        if not flag_adc_metadata:
                            self.metadata.append({'Record': c, 'Type': REC_TYPE_ADC,
                                                  'ChannelMap': rec.header.ChannelMap,
                                                  'SamplingRate': rec.header.SampleRate,
                                                  'PacketIndex': rec.header.PacketIndex,
                                                  'ADCOffset': offset[REC_TYPE_ADC],
                                                  'FileContentOffset': data_offset})
                            flag_adc_metadata = True

                        data[REC_TYPE_ADC][offset[REC_TYPE_ADC]:offset[REC_TYPE_ADC] + int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='<u2')

                        offset[REC_TYPE_ADC] += int((rec.header.Length - 6) / 2)

                        #if c==1774 or c==1775:
                        #    d.append(np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                        #                  dtype='<u2'))

                        #if c==1776:
                        #    import matplotlib.pyplot as plt
                        #    plt.plot(np.reshape(np.concatenate(d), newshape=(-1, 16), order='C')[:, 0])
                        #    plt.show()

                    elif rec.header.Type == REC_TYPE_MOTION_GYRO_AND_ACCL and REC_TYPE_MOTION_GYRO_AND_ACCL not in exclude:
                        # save metadata
                        if not flag_gyro_metadata or not flag_accl_metadata:
                            self.metadata.append({'Record': c, 'Type': REC_TYPE_MOTION_GYRO,
                                                  'ChannelMap': [16, 17, 18],
                                                  'SamplingRate': rec.header.SampleRate,
                                                  'PacketIndex': rec.header.PacketIndex,
                                                  'ADCOffset': offset[REC_TYPE_ADC],
                                                  'FileContentOffset': data_offset})

                            self.metadata.append({'Record': c, 'Type': REC_TYPE_MOTION_ACCL,
                                                   'ChannelMap': [19, 20, 21],
                                                   'SamplingRate': rec.header.SampleRate,
                                                   'PacketIndex': rec.header.PacketIndex,
                                                   'ADCOffset': offset[REC_TYPE_ADC],
                                                   'FileContentOffset': data_offset})

                            flag_gyro_metadata = True
                            flag_accl_metadata = True

                        data_from_record = np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                                         dtype='>i2')

                        data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO]
                                                                                +int((rec.header.Length - 6) / 4)] = \
                            np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[1::2], newshape=(1,-1))



                        data[REC_TYPE_MOTION_ACCL][offset[REC_TYPE_MOTION_ACCL]:offset[REC_TYPE_MOTION_ACCL] +
                                                                                int((rec.header.Length - 6) / 4)] = \
                            np.reshape(np.reshape(data_from_record, newshape=(-1, 3))[0::2], newshape=(1,-1))

                        offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 4)
                        offset[REC_TYPE_MOTION_ACCL] += int((rec.header.Length - 6) / 4)

                    elif rec.header.Type == REC_TYPE_MOTION_ACCL and REC_TYPE_MOTION_ACCL not in exclude:
                        # save metadata
                        if not flag_accl_metadata:
                            self.metadata.append({'Record': c, 'Type': REC_TYPE_MOTION_ACCL,
                                                  'ChannelMap': [19, 20, 21],
                                                  'SamplingRate': rec.header.SampleRate,
                                                  'PacketIndex': rec.header.PacketIndex,
                                                  'ADCOffset': offset[REC_TYPE_ADC],
                                                  'FileContentOffset': data_offset})
                            flag_accl_metadata = True


                        data[REC_TYPE_MOTION_ACCL][offset[REC_TYPE_MOTION_ACCL]:offset[REC_TYPE_MOTION_ACCL] +
                                                                                int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='>i2')

                        offset[REC_TYPE_MOTION_ACCL] += int((rec.header.Length - 6) / 2)

                    elif rec.header.Type == REC_TYPE_MOTION_GYRO and REC_TYPE_MOTION_GYRO not in exclude:
                        # save metadata
                        if not flag_gyro_metadata:
                            self.metadata.append({'Record': c, 'Type': REC_TYPE_MOTION_GYRO,
                                                  'ChannelMap': [16, 17, 18],
                                                  'SamplingRate': rec.header.SampleRate,
                                                  'PacketIndex': rec.header.PacketIndex,
                                                  'ADCOffset': offset[REC_TYPE_ADC],
                                                  'FileContentOffset': data_offset})
                            flag_gyro_metadata = True

                        data[REC_TYPE_MOTION_GYRO][offset[REC_TYPE_MOTION_GYRO]:offset[REC_TYPE_MOTION_GYRO] +
                        int((rec.header.Length - 6)/2)] = \
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 6)],
                                          dtype='>i2')

                        offset[REC_TYPE_MOTION_GYRO] += int((rec.header.Length - 6) / 2)

            # trim zeros from tail
            if flag_adc_metadata:
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC][:offset[REC_TYPE_ADC]]
            if flag_gyro_metadata:
                data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO][:offset[REC_TYPE_MOTION_GYRO]]
            if flag_accl_metadata:
                data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL][:offset[REC_TYPE_MOTION_ACCL]]

            # ADC: convert to signed
            if flag_adc_metadata:
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1) #ADC_RESOLUTION * (data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1))
                data[REC_TYPE_ADC] = data[REC_TYPE_ADC].astype(np.int16)
            #if flag_gyro_metadata:
            #    data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO] - np.float_power(2, IMU_BITS - 1)
            #    data[REC_TYPE_MOTION_GYRO] = data[REC_TYPE_MOTION_GYRO].astype(np.int16)
            #if flag_accl_metadata:
            #    data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL] - np.float_power(2, IMU_BITS - 1)
            #    data[REC_TYPE_MOTION_ACCL] = data[REC_TYPE_MOTION_ACCL].astype(np.int16)

            # remove unrelevant data
            if not flag_adc_metadata:
                data.pop(REC_TYPE_ADC)
            if not flag_gyro_metadata:
                data.pop(REC_TYPE_MOTION_GYRO)
            if not flag_accl_metadata:
                data.pop(REC_TYPE_MOTION_ACCL)

            data_to_yield = data
            data = {REC_TYPE_ADC: np.empty(adc_data_shape),
                    REC_TYPE_MOTION_GYRO: np.empty(gyro_data_shape),
                    REC_TYPE_MOTION_ACCL: np.empty(accl_data_shape)}
            offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}

            yield (data_to_yield, filepath)

        print('INFO: finished collecting data\n')


