from Record import *
import fnmatch
import os
import re

@attr.define
class File(object):
    ###################################################################################################################
    # Data container object for XTR-BT 1.3 files.
    #   Author: Stas Steinberg (X-trodes LTD)
    #   Date: 10/April/2022
    ###################################################################################################################

    filepath = attr.field(kw_only=True)
    records = attr.field(default=list())
    offset = attr.field(default=int(0))
    records_table = attr.field(default=None)
    data = attr.field(default=None)

    filecontents = attr.field()
    @filecontents.default
    def _read_file_contents(self):
        with open(self.filepath, 'rb') as f:
            return f.read()



    def get_records(self):
        #filecontentsstr = self.filecontents.hex()
        self.records = list()
        sor_adc_offsets = [(m.start(), REC_TYPE_ADC) for m in re.finditer(START_OF_SAMPLING_RECORD, self.filecontents)]
        sor_motion_offsets = [(m.start(), REC_TYPE_MOTION) for m in re.finditer(START_OF_MOTION_RECORD, self.filecontents)]
        sor_offsets = sorted(sor_adc_offsets + sor_motion_offsets)

        for x in sor_offsets:
            record = Record(type=x[1], offset=x[0])
            if record.parse(self.filecontents):
                self.records.append(record)
            else:
                continue

        self.records = sorted(self.records, key=lambda x: x.header.PacketIndex, reverse=False)




        # rearrange the records into a table and sort according to PacketIndex
        # RECORDS_TABLE_COLUMNS=[Time PacketIndex Type Offset Length] (see in XF2Types.py)
        # self.records_table = 0*np.empty(shape=(len(self.records), len(RECORDS_TABLE_COLUMNS))).astype(np.int)
        #
        # for c, rec in enumerate(self.records):
        #     if ERROR_WRONG_EOR not in rec.errors:
        #         if rec.header.Type == REC_TYPE_ADC:
        #             self.records_table[c, :] = [rec.header.UnixTime, rec.header.PacketIndex, rec.header.Type,
        #                                         rec.offset+rec.HeaderSize, rec.header.Length-4,
        #                                         len([x if x is not None else 0 for x in rec.header.ChannelMap]), 0]
        #         if rec.header.Type == REC_TYPE_MOTION:
        #             self.records_table[c, :] = [rec.header.UnixTime, rec.header.PacketIndex, rec.header.Type,
        #                                         rec.offset + rec.HeaderSize, rec.header.Length - 4,
        #                                         0, rec.header.ChannelMap]
        #
        # # sort by PacketIndex
        # self.records_table = self.records_table[self.records_table[:, 1].argsort()]
       #delattr(self, 'records')
