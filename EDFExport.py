import numpy as np
import pyedflib
from XF2Types import *
from pathlib import Path
import math

@attr.define
class EDFProcessor(object):

    file_path = attr.field()
    edfwriter = attr.field(default=None)
    _buffer = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _type_flags = attr.field(default={REC_TYPE_ADC: False, REC_TYPE_MOTION_GYRO: False, REC_TYPE_MOTION_ACCL: False})
    _left_to_read = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _number_of_samples_in_second = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _number_of_channels = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    #_channel_maps = attr.field(default={REC_TYPE_ADC: [], REC_TYPE_MOTION_GYRO: [], REC_TYPE_MOTION_ACCL: []})
    _read_offset = attr.field(default={REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0})
    _types = attr.field(default=[])
    
    def create_signal_headers_from_metadata(self, records, detected_signal_types):
        channel_map = np.zeros(
            shape=(NUMBER_OF_HW_ADC_CHANNELS + NUMBER_OF_HW_GYRO_CHANNELS + NUMBER_OF_HW_ACCL_CHANNELS,))
        channel_map[:] = np.nan
        sampling_rates = channel_map.copy()
        label_prefixes = channel_map.copy().astype(object)
        physical_maxs = channel_map.copy()
        physical_mins = channel_map.copy()
        digital_maxs = channel_map.copy()
        digital_mins = channel_map.copy()
        dimensions = channel_map.copy().astype(object)

        (flag_adc, flag_gyro, flag_accl) = (detected_signal_types[REC_TYPE_ADC],
                                            detected_signal_types[REC_TYPE_MOTION_GYRO],
                                            detected_signal_types[REC_TYPE_MOTION_ACCL])

        for rec in records:
            if flag_adc and rec.header.Type == REC_TYPE_ADC:
                #self._channel_maps[REC_TYPE_ADC] = rec.header.ChannelMap
                channel_map[rec.header.ChannelMap] = rec.header.ChannelMap
                sampling_rates[rec.header.ChannelMap] = rec.header.SampleRate
                label_prefixes[rec.header.ChannelMap] = 'ADC-'
                dimensions[rec.header.ChannelMap] = 'uV'
                physical_maxs[rec.header.ChannelMap] = EL_PHYS_MAX
                physical_mins[rec.header.ChannelMap] = EL_PHYS_MIN
                digital_maxs[rec.header.ChannelMap] = EL_DIG_MAX
                digital_mins[rec.header.ChannelMap] = EL_DIG_MIN
                flag_adc = False

            if flag_accl and rec.header.Type == REC_TYPE_MOTION_ACCL:
                #self._channel_maps[REC_TYPE_MOTION_ACCL] = rec.header.ChannelMap
                channel_map[rec.header.ChannelMap] = rec.header.ChannelMap
                sampling_rates[rec.header.ChannelMap] = rec.header.SampleRate
                label_prefixes[rec.header.ChannelMap] = 'ACCL-'
                dimensions[rec.header.ChannelMap] = 'g'
                physical_maxs[rec.header.ChannelMap] = ACCL_PHYS_MAX
                physical_mins[rec.header.ChannelMap] = ACCL_PHYS_MIN
                digital_maxs[rec.header.ChannelMap] = ACCL_DIG_MAX
                digital_mins[rec.header.ChannelMap] = ACCL_DIG_MIN
                flag_accl = False

            if flag_gyro and rec.header.Type == REC_TYPE_MOTION_GYRO:
                #self._channel_maps[REC_TYPE_MOTION_GYRO] = rec.header.ChannelMap
                channel_map[rec.header.ChannelMap] = rec.header.ChannelMap
                sampling_rates[rec.header.ChannelMap] = rec.header.SampleRate
                label_prefixes[rec.header.ChannelMap] = 'GYRO-'
                dimensions[rec.header.ChannelMap] = 'dps'
                physical_maxs[rec.header.ChannelMap] = GYRO_PHYS_MAX
                physical_mins[rec.header.ChannelMap] = GYRO_PHYS_MIN
                digital_maxs[rec.header.ChannelMap] = GYRO_DIG_MAX
                digital_mins[rec.header.ChannelMap] = GYRO_DIG_MIN
                flag_gyro = False

            if flag_gyro and flag_accl and rec.header.Type == REC_TYPE_MOTION_GYRO_AND_ACCL:
                #self._channel_maps[REC_TYPE_MOTION_GYRO_AND_ACCL] = rec.header.ChannelMap
                channel_map[rec.header.ChannelMap] = rec.header.ChannelMap
                sampling_rates[rec.header.ChannelMap] = rec.header.SampleRate
                label_prefixes[rec.header.ChannelMap[:3]] = 'GYRO-'
                label_prefixes[rec.header.ChannelMap[3:]] = 'ACCL-'
                dimensions[rec.header.ChannelMap[:3]] = 'dps'
                dimensions[rec.header.ChannelMap[3:]] = 'g'
                physical_maxs[rec.header.ChannelMap[:3]] = GYRO_PHYS_MAX
                physical_mins[rec.header.ChannelMap[:3]] = GYRO_PHYS_MIN
                digital_maxs[rec.header.ChannelMap[:3]] = GYRO_DIG_MAX
                digital_mins[rec.header.ChannelMap[:3]] = GYRO_DIG_MIN
                physical_maxs[rec.header.ChannelMap[3:]] = ACCL_PHYS_MAX
                physical_mins[rec.header.ChannelMap[3:]] = ACCL_PHYS_MIN
                digital_maxs[rec.header.ChannelMap[3:]] = ACCL_DIG_MAX
                digital_mins[rec.header.ChannelMap[3:]] = ACCL_DIG_MIN
                flag_gyro = False
                flag_accl = False

            if not (flag_adc or flag_gyro or flag_accl):
                break



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
                           'digital_min': digital_mins[cc]} for cc, ii in enumerate(channel_map) if not math.isnan(ii)]
        return signal_headers

    #def _init_buffer(self, metadata, type):


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

    def save_to_edf(self, data_generator, write_record_created_annotations):
        flag_first_batch = True
        #onset_in_seconds = 0
        for databatch, filepath, records, detected_data_types in data_generator:
            if flag_first_batch:
                # prep signal headers and edf writer
                signal_headers = self.create_signal_headers_from_metadata(records, detected_data_types)
                self.edfwriter = pyedflib.EdfWriter(file_name=self.file_path, n_channels=len(signal_headers))
                self.edfwriter.setSignalHeaders(signal_headers)
                
                # prepare buffer
                for x in detected_data_types.keys():
                    self._buffer[x] = np.zeros(shape=(200000000,), dtype=np.int16)

                # set active types
                for x in detected_data_types.keys():
                    self._type_flags[x] = True
                    self._types.append(x)

                # calculate the number of samples per second for all channels and the number of channels per signal type
                for x in detected_data_types.keys():
                    if x == REC_TYPE_ADC:
                        idxs = [index for (index, d) in enumerate(signal_headers) if 'ADC' in d['label']]
                    elif x == REC_TYPE_MOTION_GYRO:
                        idxs = [index for (index, d) in enumerate(signal_headers) if 'GYRO' in d['label']]
                    elif x == REC_TYPE_MOTION_ACCL:
                        idxs = [index for (index, d) in enumerate(signal_headers) if 'ACCL' in d['label']]
                    self._number_of_channels[x] = len(idxs)
                    self._number_of_samples_in_second[x] = int(signal_headers[idxs[0]]['sample_frequency'] * len(idxs))

                ## first record appears at the following time (in seconds)
                t0 = records[0].header.UnixTime + records[0].header.UnixMs/1000

                flag_first_batch = False

            # write record annotation
            if write_record_created_annotations:
                print('INFO: EDF: writing record creation annotations...')
                for rec in records:
                    onset_in_seconds = rec.header.UnixTime + rec.header.UnixMs/1000 - t0
                    self.edfwriter.writeAnnotation(onset_in_seconds=onset_in_seconds, duration_in_seconds=0.001, description='T %d Idx %d file %s' % (rec.header.Type, rec.header.PacketIndex, Path(filepath).name))

            # populate buffers with data from databatch
            self._write_buffer(databatch)

            # write to EDF from buffers until the smallest amount of samples are written
            # most likely gyro and accl samples will be written first
            data_to_write = {REC_TYPE_ADC: 0, REC_TYPE_MOTION_GYRO: 0, REC_TYPE_MOTION_ACCL: 0}
            #min_type = min(self._number_of_samples_in_second, key=self._number_of_samples_in_second.get)
            print('INFO: EDF: writing buffer contents to EDF until all the buffers do not have enough samples to fill one second')
            while all([self._left_to_read[type] >= self._number_of_samples_in_second[type] for type in self._types]):
                #self._write_to_edf_from_buffer_multimodal(databatch)
                for type in self._types:
                    data_to_write[type] = self._buffer[type][self._read_offset[type]:self._read_offset[type]+self._number_of_samples_in_second[type]]
                    data_to_write[type] = np.reshape(np.transpose(np.reshape(data_to_write[type],
                                                                             newshape=(
                                                                             -1, self._number_of_channels[type]),
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

            #for rec in files_metadata:
             #   if rec['Type'] == REC_TYPE_ADC:
             #       onset_in_seconds += databatch[REC_TYPE_ADC].shape[0]/rec['SamplingRate']/len(rec['ChannelMap'])

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
                self._buffer[type][self._left_to_read[type]:] = 10000

                # reset pointer for data read
                self._read_offset[type] = 0



        self.edfwriter.close()
        print('INFO: EDF: finished writing EDF file %s' % self.file_path)
