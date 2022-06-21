import numpy as np
import pyedflib
from XF2Types import *
from pathlib import Path

@attr.define
class EDFProcessor(object):

    file_path = attr.field()
    edfwriter = attr.field(default=None)
    _buffer = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _type_flags = attr.field(default={REC_TYPE_ADC: False, REC_TYPE_MOTION_GYRO: False, REC_TYPE_MOTION_ACCL: False})
    _left_to_read = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _number_of_samples_in_second = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _channel_maps = attr.field(default={REC_TYPE_ADC: [], REC_TYPE_MOTION_GYRO: [], REC_TYPE_MOTION_ACCL: []})
    _read_offset = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _types = attr.field(default=[])
    
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
                    dimensions[i] = 'dps'
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

    def _init_buffer(self, metadata, type):
        self._buffer[type] = np.zeros(shape=(200000000,), dtype=np.int16)
        self._type_flags[type] = True
        self._channel_maps[type] = metadata['ChannelMap']
        self._number_of_samples_in_second[type] = metadata['SamplingRate'] * len(metadata['ChannelMap'])

    def _write_buffer(self, databatch):
        for type in self._types:
            #print('INFO: writing to buffers:')
            #print('Type %s' % type)
            #print('Data size to fill %d' % databatch[type].shape[0])
            #print('Offset %d' % self._read_offset[type])
            #print('Total buffer size %d' % self._buffer[type].shape[0])
            #print('Bytes left to read %d' % self._left_to_read[type])
            self._buffer[type][self._left_to_read[type]:self._left_to_read[type] + databatch[type].shape[0]] = \
                databatch[type]
            self._left_to_read[type] += databatch[type].shape[0]
            #print('INFO: done writing to buffer')

    def save_to_edf(self, data_generator, files_metadata):
        flag_first_batch = True
        onset_in_seconds = 0
        for databatch, filepath in data_generator:
            if flag_first_batch:
                # prep signal headers and edf writer
                signal_headers = self.create_signal_headers_from_metadata(files_metadata)
                self.edfwriter = pyedflib.EdfWriter(file_name=self.file_path, n_channels=len(signal_headers))
                self.edfwriter.setSignalHeaders(signal_headers)
                
                # prepare buffer
                for x in files_metadata:
                    self._init_buffer(x, x['Type'])
                    self._types.append(x['Type'])
                flag_first_batch = False

            # write file created annotation
            self.edfwriter.writeAnnotation(onset_in_seconds=onset_in_seconds, duration_in_seconds=1, description='file created %s' % Path(filepath).name)

            # populate buffers with data from databatch
            self._write_buffer(databatch)

            # write to EDF from buffers until the smallest amount of samples are written
            # most likely gyro and accl samples will be written first
            data_to_write = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}
            #min_type = min(self._number_of_samples_in_second, key=self._number_of_samples_in_second.get)
            while any([self._left_to_read[type] >= self._number_of_samples_in_second[type] for type in self._types]):
                #self._write_to_edf_from_buffer_multimodal(databatch)
                for type in self._types:
                    data_to_write[type] = self._buffer[type][self._read_offset[type]:self._read_offset[type]+self._number_of_samples_in_second[type]]
                    data_to_write[type] = np.reshape(np.transpose(np.reshape(data_to_write[type],
                                                                             newshape=(
                                                                             -1, len(self._channel_maps[type])),
                                                                             order='C')),
                                                     newshape=(self._number_of_samples_in_second[type],), order='C')
                    self._left_to_read[type] -= self._number_of_samples_in_second[type]
                    self._read_offset[type] += self._number_of_samples_in_second[type]
                    #print('writing %d samples of type %d to edf' % (data_to_write[type].shape[0], type))
                self.edfwriter.blockWriteDigitalShortSamples(np.concatenate([data_to_write[type] for type in self._types]))

            # now there's at least one data type which has less samples in buffer to read from
            # than 1s worth of data...
            # in this case we need to populate the buffer further

            #if all([self._left_to_read[type] >= self._number_of_samples_in_second[type] for type in self._types]):
                # if any([self._left_to_read[type] < self._number_of_samples_in_second[type] for type in self._types]):
                #     for type in self._types:
                #         # relocate leftover data to start of buffer
                #         self._buffer[type][:self._left_to_read[type]] = self._buffer[type][self._read_offset[type]:
                #                                                                            self._read_offset[type] +
                #                                                                            self._left_to_read[type]]
                #         # pad with zeros anything above leftovers
                #         self._buffer[type][self._left_to_read[type]:] = 0
                #
                #         # reset pointer for data read
                #         self._read_offset[type] = 0

            # left_to_read points to the head
            # and read_offset points to the tail
            # we write to the head
            # and read from the tail towards the head

            for rec in files_metadata:
                if rec['Type'] == REC_TYPE_ADC:
                    onset_in_seconds += databatch[REC_TYPE_ADC].shape[0]/rec['SamplingRate']/len(rec['ChannelMap'])

            # relocate the tail to 0, keep leftovers and pad
            # anything over the head with 0's

            #if any([(self._buffer[type].shape[0] - self._left_to_read[type]) < self._number_of_samples_in_second[type] for type in self._types]):
            for type in self._types:
                # if left_to_read is negative (we wrote 0 to edf) then reset the counter
                if self._left_to_read[type] < 0:
                    self._left_to_read[type] = 0

                # relocate leftover data to start of buffer
                self._buffer[type][:self._left_to_read[type]] = self._buffer[type][self._read_offset[type]:
                                                                                            self._read_offset[type] +
                                                                                            self._left_to_read[type]]
                # pad with zeros anything above leftovers
                self._buffer[type][self._left_to_read[type]:] = 0

                # reset pointer for data read
                self._read_offset[type] = 0



        self.edfwriter.close()
        print('INFO: finished writing EDF file %s' % self.file_path)
