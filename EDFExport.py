import numpy as np
import pyedflib
from XF2Types import *

@attr.define
class EDFProcessor(object):

    file_path = attr.field()
    edfwriter = attr.field(default=None)
    _buffer = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _type_flags = attr.field(default={REC_TYPE_ADC: False, REC_TYPE_MOTION_GYRO: False, REC_TYPE_MOTION_ACCL: False})
    _left_to_read = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _number_of_samples_in_second = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _channel_maps = attr.field(default={REC_TYPE_ADC: [], REC_TYPE_MOTION_GYRO: [], REC_TYPE_MOTION_ACCL: []})
    _offsets = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    def create_signal_headers_from_metadata(self, files_metadata):
        channel_map = np.zeros(
            shape=(NUMBER_OF_HW_ADC_CHANNELS + NUMBER_OF_HW_GYRO_CHANNELS + NUMBER_OF_HW_ACCL_CHANNELS,))
        channel_map[:] = np.nan
        sampling_rates = list(channel_map)
        label_prefixes = list(channel_map)
        physical_maxs = list(channel_map)
        physical_mins = list(channel_map)
        digital_maxs = list(channel_map)
        digital_mins = list(channel_map)
        dimensions = list(channel_map)
        for metadata in files_metadata:
            channel_map[metadata['ChannelMap']] = metadata['ChannelMap']
            if metadata['Type'] == REC_TYPE_ADC:
                for i in metadata['ChannelMap']:
                    sampling_rates[i] = metadata['SamplingRate']
                    label_prefixes[i] = 'ADC-'
                    dimensions[i] = 'uV'
                    physical_maxs[i] = EL_PHYS_MAX
                    physical_mins[i] = EL_PHYS_MIN
                    digital_maxs[i] = EL_DIG_MAX
                    digital_mins[i] = EL_DIG_MIN
            elif metadata['Type'] == REC_TYPE_MOTION_ACCL:
                for i in metadata['ChannelMap']:
                    sampling_rates[i] = metadata['SamplingRate']
                    label_prefixes[i] = 'ACCL-'
                    dimensions[i] = 'g'
                    physical_maxs[i] = ACCL_PHYS_MAX
                    physical_mins[i] = ACCL_PHYS_MIN
                    digital_maxs[i] = ACCL_DIG_MAX
                    digital_mins[i] = ACCL_DIG_MIN
            elif metadata['Type'] == REC_TYPE_MOTION_GYRO:
                for i in metadata['ChannelMap']:
                    sampling_rates[i] = metadata['SamplingRate']
                    label_prefixes[i] = 'GYRO-'
                    dimensions[i] = 'deg/s'
                    physical_maxs[i] = GYRO_PHYS_MAX
                    physical_mins[i] = GYRO_PHYS_MIN
                    digital_maxs[i] = GYRO_DIG_MAX
                    digital_mins[i] = GYRO_DIG_MIN
        return self.create_signal_headers(channel_map=channel_map,
                                                         label_prefixes=label_prefixes,
                                                         dimensions=dimensions,
                                                         sample_freqs=sampling_rates,
                                                         physical_maxs=physical_maxs,
                                                         physical_mins=physical_mins,
                                                         diginal_maxs=digital_maxs,
                                                         digital_mins=digital_mins)

    def create_signal_headers(self, channel_map, label_prefixes, dimensions, sample_freqs, physical_maxs, physical_mins,
                              diginal_maxs, digital_mins):
        # every parameter is a list that maps values to channel_map. For example, if
        # channel_map = [5, 6, 7, 8] and
        # dimensions = ['uV', 'uV', 'mV', 'mV']
        # in case we have 4 active channels. Here channel 5-6 are in uV, and channels 7-8 are in mV
        # label_format is a list that defines the string format for each channel:
        # e.g. label_format = ['EEG Ch-', 'EEG Ch-', 'EMG Ch-', 'EMG Ch-']
        # in our example it will create labels as follows: EEG Ch-5, EEG Ch-6, EMG Ch-7, EMG Ch-8

        # check for adc, accl and gyro presence

        signal_headers = [{'label': label_prefixes[cc] + str(int(ii)),
                           'dimension': dimensions[cc],
                           'sample_frequency': sample_freqs[cc],
                           'physical_max': physical_maxs[cc],
                           'physical_min': physical_mins[cc],
                           'digital_max': diginal_maxs[cc],
                           'digital_min': digital_mins[cc]} for cc, ii in enumerate(channel_map) if ii>=0]
        return signal_headers

    def _init_buffer(self, metadata, type, databatch):
        self._buffer[type] = np.zeros(shape=(int(2 * databatch[type].shape[0]),), dtype=np.int16)
        self._type_flags[type] = True
        self._channel_maps[type] = metadata['ChannelMap']
        self._number_of_samples_in_second[type] = metadata['SamplingRate'] * len(metadata['ChannelMap'])

    def _write_buffer(self, databatch):
        for type in databatch.keys():
            self._buffer[type][self._left_to_read[type]:self._left_to_read[type] + databatch[type].shape[0]] = \
                databatch[type]
            self._left_to_read[type] += databatch[type].shape[0]

    def _write_to_edf_from_buffer_one_type(self, type):
        while self._left_to_read[type] >= self._number_of_samples_in_second[type]:
            data_to_write = self._buffer[type][self._offsets[type]:
                                                       self._offsets[type] +
                                                       self._number_of_samples_in_second[type]]

            # reshape data for edf format
            data_to_write = np.reshape(np.transpose(np.reshape(data_to_write,
                                                               newshape=(-1, len(self._channel_maps[type])),
                                                               order='C')),
                                       newshape=(self._number_of_samples_in_second[type],), order='C')

            self._left_to_read[type] -= self._number_of_samples_in_second[type]
            self._offsets[type] += self._number_of_samples_in_second[type]

            print('Left to read: %d' % self._left_to_read[type])
            print('Offset: %d' % self._offsets[type])
            self.edf_writer.blockWriteDigitalShortSamples(data_to_write)
            print('INFO: finished writing batch to EDF')

        # relocate leftover data to start of buffer
        self._buffer[type][:self._left_to_read[type]] = self._buffer[type][self._offsets[type]:
                                                                           self._offset[type]+self._left_to_read[type]]
        # reset pointer
        self._offset[type] = 0

    def _write_to_edf_from_buffer_multimodal(self, databatch):
        main_type = max(self._number_of_samples_in_second, key=self._number_of_samples_in_second.get)

        while self._left_to_read[main_type] >= self._number_of_samples_in_second[main_type]:
            data_to_write = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}
            for type in databatch.keys():
                data_to_write[type] = self._buffer[type][self._offsets[type]:self._offsets[type] +
                                                                             self._number_of_samples_in_second[type]]

            # reshape data for edf format
                data_to_write[type] = np.reshape(np.transpose(np.reshape(data_to_write[type],
                                                                   newshape=(-1,len(self._channel_maps[type])),
                                                                   order='C')),
                                           newshape=(self._number_of_samples_in_second[type],), order='C')

            data_to_write = np.concatenate([data_to_write[type] for type in databatch.keys()])
            self.edfwriter.blockWriteDigitalShortSamples(data_to_write)
            print('INFO: finished writing batch to EDF')
            for type in databatch.keys():
                self._left_to_read[type] -= self._number_of_samples_in_second[type]
                self._offsets[type] += self._number_of_samples_in_second[type]
                print('Type: %s - Left to read: %d' % (type, self._left_to_read[type]))
                print('Type: %s - Offset: %d' % (type, self._offsets[type]))


        for type in databatch.keys():
            # relocate leftover data to start of buffer
            self._buffer[type][:self._left_to_read[type]] = self._buffer[type][self._offsets[type]:
                                                                               self._offsets[type]+self._left_to_read[type]]
            # reset pointer
            self._offsets[type] = 0


    def save_to_edf(self, data_generator, files_metadata):
        flag_first_batch = True
        for databatch in data_generator:
            if flag_first_batch:
                # prep signal headers and edf writer
                signal_headers = self.create_signal_headers_from_metadata(files_metadata)
                self.edfwriter = pyedflib.EdfWriter(file_name=self.file_path, n_channels=len(signal_headers))
                self.edfwriter.setSignalHeaders(signal_headers)

                # prepare buffer
                for x in files_metadata:
                    self._init_buffer(x, x['Type'], databatch)

                flag_first_batch = False

            # populate buffers
            self._write_buffer(databatch)

            # write to EDF from buffers
            self._write_to_edf_from_buffer_multimodal(databatch)


        # pad leftovers
        for type in databatch.keys():
            self._buffer[type][self._left_to_read[type]:] = 0
        data_to_write = np.concatenate([self._buffer[type][:self._number_of_samples_in_second[type]] for type in databatch.keys()])
        # write last samples
        self.edfwriter.blockWriteDigitalShortSamples(data_to_write)
        self.edfwriter.close()
        print('INFO: finished writing EDF file %s' % self.file_path)
