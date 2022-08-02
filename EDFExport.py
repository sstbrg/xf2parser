import datetime
import json
import logging

import numpy as np
import pyedflib
import pytz as pytz
import math
from .XF2Types import *
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
    session_details = attr.field(default=None)
    user_events = attr.field(default=None)
    seconds_processed = attr.field(default=0)
    end_of_recording_to_edf = attr.field(default=None)
    session_details_fields = (
        'Study_name',
        'Dateset_name',
        'site',
        'operator',
        'remarks',
        'Patient_id',
        'Age',
        'Gender',
        'App_version',
        'DAU_serial_number',
        'DAU_fw_number',
        'Session_date_time',
        "SKU")

    def parse_date(self, date, timezone):
        timestamp = None
        if not timezone:
            timezone = pytz.timezone("UTC")
        else:
            timezone = pytz.timezone(timezone)
        if not date: return None
        try:
            timestamp = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f%z').astimezone(timezone).replace(
                tzinfo=None)
        except ValueError:
            timestamp = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S%z').astimezone(timezone).replace(
                tzinfo=None)
        return timestamp

    def set_session_details(self, edf_writer, details):
        try:
            edf_writer.setTechnician(details["operator"])
            edf_writer.setEquipment(details["Session_sensor"])
            edf_writer.setPatientCode(details["Patient_id"])
            patient_additional = []
            record_additional = []
            patient_additional.append(f"Study:{details['Study_name']}")
            patient_additional.append(f"Session:{details['Dateset_name']}")
            record_additional.append(f"App ver.:{details['Session_gateway']}")
            record_additional.append(f"Site:{details['site']}")
            edf_writer.setPatientAdditional(';'.join(patient_additional))
            edf_writer.setRecordingAdditional(';'.join(record_additional))
            return edf_writer
        except:
            self.handle_exception()

    def truncate(self, f, n):
        return math.floor(f * 10 ** n) / 10 ** n

    def write_annotation_with_truncated_offset(self, edf_writer, onset, duration, name):
        onset = self.truncate(onset, 3)
        edf_writer.writeAnnotation(onset, duration, name)

    def write_annotations(self):
        if self.session_details:
            details = {d: self.session_details[d] for d in self.session_details_fields}
            details["Patient ID"] = details.pop("Patient_id", "err")
            details["App version"] = details.pop("App_version", "err")
            details["DAU serial number"] = details.pop("DAU_serial_number", "err")
            details["DAU fw number"] = details.pop("DAU_fw_number", "err")
            details["Date and Time"] = details.pop("Session_date_time", "err")
            details["Site"] = details.pop("site", "err")
            details["Operator"] = details.pop("operator", "err")
            details["Remarks"] = details.pop("remarks", "err")
            details['Session_name'] = details.pop('Dateset_name').split('-.~')[0]
            details['Montage'] = ', '.join(details.pop('SKU'))
            self.end_of_recording_to_edf = self.parse_date(self.session_details['Session_date_time'],
                                                           self.session_details['timezone']) + datetime.timedelta(
                seconds=self.seconds_processed)
            try:
                details["Date and Time"] = self.parse_date(details["Date and Time"], self.session_details['timezone'])
            except:
                pass
            for k, v in details.items():
                self.write_annotation_with_truncated_offset(self.edfwriter,
                                                            0, 0.1,
                                                            f"{k.replace('_', ' ')}: {v}")
            rec_start = self.parse_date(self.session_details['Session_date_time'],
                                        self.session_details['timezone'])

            for num, ch in enumerate(self.session_details['modalities']):
                self.edfwriter.writeAnnotation(0, 0.1,
                                               f'CH-{num + 1} {ch}')
            for event in self.user_events:
                # t_stamp = datetime.datetime.strptime(event['Timestamp'], "%d-%m-%Y %H:%M:%S:%f").timestamp()
                event_date_time = self.parse_date(event['Timestamp'], self.session_details['timezone'])
                duration = event.get('Duration', 0.1)
                if event['EventName'] == 'Recording Stopped':
                    event['EventName'] = "App End Recording"
                    if event_date_time > self.end_of_recording_to_edf:
                        tmp = {}
                        tmp['EventName'] = 'End of Data'
                        self.edfwriter.writeAnnotation(self.end_of_recording_to_edf, duration, tmp['EventName'])
                        event['EventName'] = "App End Recording"
                        self.edfwriter.writeAnnotation(event_date_time, duration, event['EventName'])

                self.edfwriter.writeAnnotation((event_date_time - rec_start).total_seconds(), duration,
                                               event['EventName'])

    def handle_exception(self, ):
        exception_type, exception_value, exception_traceback = sys.exc_info()
        traceback_string = traceback.format_exception(exception_type, exception_value, exception_traceback)
        err_msg = json.dumps({
            "errorType": exception_type.__name__,
            "errorMessage": str(exception_value),
            "stackTrace": traceback_string
        })
        self.logger.error(err_msg)
        pass


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
                if self.session_details:
                    self.edfwriter.setStartdatetime(self.parse_date(self.session_details['Session_date_time'],
                                                                    self.session_details['timezone']))
                    self.edfwriter = self.set_session_details(self.edfwriter, self.session_details)

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
        self.write_annotations()
        self.edfwriter.close()
        print('INFO: EDF: finished writing EDF file %s' % self.file_path)
