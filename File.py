from Record import *
import re

@attr.define
class File(object):
    ###################################################################################################################
    # Data container object for XTR-BT 1.3 files.
    #   Author: Stas Steinberg (X-trodes LTD)
    #   Date: 10/April/2022
    ###################################################################################################################

    filepath = attr.field(kw_only=True)
    records = attr.field(default=None)
    offset = attr.field(default=int(0))
    records_table = attr.field(default=None)
    data = attr.field(default=None)

    filecontents = attr.field()
    @filecontents.default
    def _read_file_contents(self):
        with open(self.filepath, 'rb') as f:
            return f.read()

    def get_records(self):
        self.records = {REC_TYPE_ADC: list(),
                                  REC_TYPE_MOTION_ACCL: list(),
                                  REC_TYPE_MOTION_GYRO: list(),
                                  REC_TYPE_MOTION_GYRO_AND_ACCL: list()}
        sor_adc_offsets = [(m.start(), REC_TYPE_ADC) for m in re.finditer(START_OF_SAMPLING_RECORD, self.filecontents)]
        sor_motion_offsets = [(m.start(), REC_TYPE_MOTION) for m in re.finditer(START_OF_MOTION_RECORD, self.filecontents)]
        sor_offsets = sorted(sor_adc_offsets + sor_motion_offsets)


        for x in sor_offsets:
            record = Record(type=x[1], offset=x[0])
            if record.parse(self.filecontents):
                if record.header.Type == REC_TYPE_ADC:
                    self.records[REC_TYPE_ADC].append(record)
                elif record.header.Type == REC_TYPE_MOTION_ACCL:
                    self.records[REC_TYPE_MOTION_ACCL].append(record)
                elif record.header.Type == REC_TYPE_MOTION_GYRO:
                    self.records[REC_TYPE_MOTION_ACCL].append(record)
                elif record.header.Type == REC_TYPE_MOTION_GYRO_AND_ACCL:
                    self.records[REC_TYPE_MOTION_GYRO_AND_ACCL].append(record)
                else:
                    print('ERROR: RECORD: unrecognized record type!')
            else:
                continue

        # sort records
        for type in (REC_TYPE_ADC, REC_TYPE_MOTION_ACCL, REC_TYPE_MOTION_GYRO, REC_TYPE_MOTION_GYRO_AND_ACCL):
            if len(self.records[type]):
                self.records[type] = sorted(self.records[type], key=lambda x: x.header.UnixTime+x.header.UnixMs/1000, reverse=False)
