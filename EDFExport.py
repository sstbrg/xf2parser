import numpy as np
import pyedflib
from XF2Types import *

@attr.define
class EDFProcessor(object):

    file_path = attr.field()

    def create_signal_headers_from_metadata(self, parser):
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
        for metadata in parser.metadata:
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


    def _prep_data_for_edf_batch_write(self, databatch, files_metadata, data_type):
        sampling_rate = [x['SamplingRate'] for x in files_metadata if x['Type'] == data_type][0]
        channel_map = [x['ChannelMap'] for x in files_metadata if x['Type'] == data_type][0]
        split = np.split(databatch[data_type],
                              indices_or_sections=[sampling_rate * len(channel_map) * (i + 1) for i in
                                                   range(int(databatch[data_type].shape[0] /
                                                             sampling_rate /
                                                             len(channel_map)))])
        # pad last value
        if split[-1].shape[0] < sampling_rate * len(channel_map):
            split[-1] = np.pad(split[-1],
                                    pad_width=(0, sampling_rate * len(channel_map) - split[-1].shape[0]),
                                    mode='constant',
                                    constant_values=0)
        return split

    def save_to_edf(self, data_generator, files_metadata, signal_headers):
        # EDF needs [channels x samples]
        edf_writer = pyedflib.EdfWriter(file_name=self.file_path, n_channels=len(signal_headers))
        edf_writer.setSignalHeaders(signal_headers)

        for databatch in data_generator:
            split_adc = []
            split_gyro = []
            split_accl = []
            if REC_TYPE_ADC in databatch.keys():
                split_adc = self._prep_data_for_edf_batch_write(databatch, files_metadata, REC_TYPE_ADC)

            if REC_TYPE_MOTION_GYRO in databatch.keys():
                split_gyro = self._prep_data_for_edf_batch_write(databatch, files_metadata, REC_TYPE_MOTION_GYRO)

            if REC_TYPE_MOTION_ACCL in databatch.keys():
                split_accl = self._prep_data_for_edf_batch_write(databatch, files_metadata, REC_TYPE_MOTION_ACCL)

            for x in range(len(split_adc)):
                if len(split_adc) > 0 and len(split_gyro) > 0 and len(split_accl) > 0: # adc, gyro, accl
                    data_to_write = np.concatenate((split_adc[x], split_gyro[x], split_accl[x]))
                elif  len(split_adc) > 0 and len(split_gyro) > 0 and len(split_accl) == 0: # adc, gyro
                    data_to_write = np.concatenate((split_adc[x], split_gyro[x]))
                elif len(split_adc) > 0 and len(split_gyro) == 0 and len(split_accl) > 0: # adc, accl
                    data_to_write = np.concatenate((split_adc[x], split_accl[x]))
                elif len(split_adc) == 0 and len(split_gyro) > 0 and len(split_accl) > 0: # gyro, accl
                    data_to_write = np.concatenate((split_gyro[x], split_accl[x]))
                elif len(split_adc) == 0 and len(split_gyro) == 0 and len(split_accl) > 0: # accl
                    data_to_write = split_accl[x]
                elif len(split_adc) == 0 and len(split_gyro) > 0 and len(split_accl) == 0: # gyro
                    data_to_write = split_gyro[x]
                elif len(split_adc) > 0 and len(split_gyro) == 0 and len(split_accl) == 0: # adc
                    data_to_write = split_adc[x]

                edf_writer.blockWriteDigitalShortSamples(data_to_write)
            print('INFO: finished writing batch to EDF')

        edf_writer.close()
        print('INFO: finished writing EDF file %s' % self.file_path)