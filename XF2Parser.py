from File import *
from glob import glob
from natsort import natsorted
import os
from tqdm import tqdm
import numpy as np
import gc

@attr.define
class Parser(object):
    work_directory = attr.field(kw_only=True)
    data = attr.field(default={REC_TYPE_ADC: None,
                               REC_TYPE_MOTION: None})

    def process_files(self, save_path=None, transpose_data=False):
        file_list = natsorted([x for x in glob(os.path.join(self.work_directory, '*'+FILE_FORMAT))])
        # every file usually has 124560 samples of adc data and 94545 samples of gyro data

        # infer final array size, usually there are 1038 adc records of 3840 bytes per file and 369 motion records of size 510 bytes

        if save_path is None:
            adc_data_shape = (int((3840/2)*2000*len(file_list)), NUMBER_OF_HW_ADC_CHANNELS) #(int(np.ceil(sum([sum([(rec.header.Length-4)/2/NUMBER_OF_HW_ADC_CHANNELS if rec.header.Type==REC_TYPE_ADC else 0 for rec in x.records]) for x in files]))), NUMBER_OF_HW_ADC_CHANNELS)
            motion_data_shape = (int((510/2)*2000*len(file_list)), NUMBER_OF_HW_MOTION_CHANNELS) #(int(np.ceil(sum([sum([(rec.header.Length-4)/2/NUMBER_OF_HW_ADC_CHANNELS if rec.header.Type==REC_TYPE_MOTION else 0 for rec in x.records]) for x in files]))), NUMBER_OF_HW_MOTION_CHANNELS)
        else:
            save_file = open(save_path, 'wb')
            adc_data_shape = (int((3840/2)*2000), NUMBER_OF_HW_ADC_CHANNELS)
            motion_data_shape = (int((3840/2)*2000), NUMBER_OF_HW_MOTION_CHANNELS)

        # create the arrays
        data = {REC_TYPE_ADC: np.empty(adc_data_shape),
                REC_TYPE_MOTION: np.empty(motion_data_shape)}

        # extract data
        offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION: 0}

        for c, filepath in tqdm(enumerate(file_list)):
            print('INFO: collecting data from records of %s' % filepath)
            f = File(filepath=filepath)
            f.get_records()
            # what is the total length of the data ?
            #data_size_in_bytes = sum([rec.header.Length-4 for rec in self.records])

            # for each record, count the number of active channels
            #num_of_samples = int(data_size_in_bytes / 2)  # each sample is a word

            # we need to fill a matrix of [samples x channels]
            # in the worst case scenario, there will be one channel active so the data matrix will be [1 x all the samples]
            # we will later trim this

            # we extract the data per record
            for rec in f.records:
                if ERROR_WRONG_EOR not in rec.errors:
                    data_offset = int(rec.offset + rec.HeaderSize)
                    if rec.header.Type == REC_TYPE_ADC:
                        num_of_active_channels = len([x if x is not None else 0 for x in rec.header.ChannelMap])
                        data[REC_TYPE_ADC][offset[REC_TYPE_ADC]:offset[REC_TYPE_ADC] + int(
                            (rec.header.Length - 4) / 2 / num_of_active_channels),
                        rec.header.ChannelMap] = np.reshape(
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 4)],
                                          dtype='<u2'),
                            newshape=(
                            int((rec.header.Length - 4) / 2 / num_of_active_channels), num_of_active_channels),
                            order='C')

                        offset[REC_TYPE_ADC] += int((rec.header.Length - 4) / 2 / num_of_active_channels)

                    if rec.header.Type == REC_TYPE_MOTION:
                        data[REC_TYPE_MOTION][offset[REC_TYPE_MOTION]:offset[REC_TYPE_MOTION] + int(
                            (rec.header.Length - 4) / 2 / NUMBER_OF_HW_MOTION_CHANNELS), :] = np.reshape(
                            np.fromstring(f.filecontents[data_offset:data_offset + (rec.header.Length - 4)],
                                          dtype='<u2'),
                            newshape=(int((rec.header.Length - 4) / 2 / NUMBER_OF_HW_MOTION_CHANNELS),
                                      NUMBER_OF_HW_MOTION_CHANNELS),
                            order='C')

                        offset[REC_TYPE_MOTION] += int((rec.header.Length - 4) / 2 / NUMBER_OF_HW_MOTION_CHANNELS)

            # trim zeros from tail
            data[REC_TYPE_ADC] = data[REC_TYPE_ADC][~np.all(data[REC_TYPE_ADC] == 0, axis=1)]
            data[REC_TYPE_MOTION] = data[REC_TYPE_MOTION][~np.all(data[REC_TYPE_MOTION] == 0, axis=1)]

            # ADC: convert to voltages
            data[REC_TYPE_ADC] = data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1) #ADC_RESOLUTION * (data[REC_TYPE_ADC] - np.float_power(2, ADC_BITS - 1))
            data[REC_TYPE_ADC] = data[REC_TYPE_ADC].astype(np.int16)

            if transpose_data:
                data[REC_TYPE_ADC] = np.transpose(data[REC_TYPE_ADC])

            if save_path is not None:
                np.save(save_file, data[REC_TYPE_ADC])
                save_file.flush()
                data = {REC_TYPE_ADC: np.empty(adc_data_shape),
                        REC_TYPE_MOTION: np.empty(motion_data_shape)}
                offset = {REC_TYPE_ADC: 0, REC_TYPE_MOTION: 0}

        if save_path is None:
            self.data = data
        else:
            save_file.close()

        print('INFO: finished collecting data')


