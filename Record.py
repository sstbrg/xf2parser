from XF2Types import *
import binascii

def calc_crc16(data: bytes):
    #perform CRC16-CCITT
    return binascii.crc_hqx(data, 0)

@attr.define
class Record(object):
    ###################################################################################################################
    # Data container object for XTR-BT 1.3 files.
    #   Author: Stas Steinberg (X-trodes LTD)
    #   Date: 10/April/2022
    ###################################################################################################################

    type = attr.field(kw_only=True)
    offset = attr.field(kw_only=True)
    _HeaderStruct = attr.field(default=RecordStruct().Header)
    HeaderSize = attr.field(default=0)
    _EORStruct = attr.field(default=RecordStruct().EOR)
    EORSize = attr.field(default=0)
    header = attr.field(default=None)
    errors = attr.field(default=list())
    eor = attr.field(default=None)

    def parse(self, content):
        self.errors = []
        self.HeaderSize = sum([sub.length for sub in self._HeaderStruct.subcons])
        self.EORSize = sum([sub.length for sub in self._EORStruct.subcons])
        self.header = self._parse_header(content)
        self.eor = self._parse_eor(content)
        if ERROR_WRONG_CRC in self.errors or \
            ERROR_WRONG_EOR in self.errors or \
            ERROR_HEADER_POINTS_BEYOND_EOF in self.errors or \
            ERROR_WRONG_SOR_IN_HEADER in self.errors:
                return False
        else:
            return True

    def _parse_header(self, content):

        if self.offset + self.HeaderSize > len(content):
            self.errors.append(ERROR_HEADER_POINTS_BEYOND_EOF)
            print(ERROR_HEADER_POINTS_BEYOND_EOF)
            return False

        parsed = self._HeaderStruct.parse(content[self.offset:self.offset+self.HeaderSize])

        if parsed.Sor != START_OF_RECORD:
            self.errors.append(ERROR_WRONG_SOR_IN_HEADER)
            print(ERROR_WRONG_SOR_IN_HEADER)

        if self.offset + self.HeaderSize + parsed.Length - 6 - 1 + self.EORSize >= len(content):
            self.errors.append(ERROR_HEADER_POINTS_BEYOND_EOF)
            print(ERROR_HEADER_POINTS_BEYOND_EOF)
            return False

        if content[
            self.offset + self.HeaderSize + parsed.Length - 6 - 1 + self.EORSize] != END_OF_RECORD:
            self.errors.append(ERROR_WRONG_EOR)
            print(ERROR_WRONG_EOR)

        if parsed.Type == REC_TYPE_ADC:
            parsed.ChannelMap = [num if val == '1' else None for num, val in
                               enumerate(list('{0:016b}'.format(parsed.ChannelMap)))]
            parsed.ChannelMap = [x for x in parsed.ChannelMap if x is not None]
        elif parsed.Type == REC_TYPE_MOTION:
            if parsed.ChannelMap == REC_TYPE_MOTION_GYRO:
                parsed.Type = REC_TYPE_MOTION_GYRO
                parsed.ChannelMap = REC_TYPE_MOTION_GYRO_CHANNELS
            elif parsed.ChannelMap == REC_TYPE_MOTION_ACCL:
                parsed.Type = REC_TYPE_MOTION_ACCL
                parsed.ChannelMap = REC_TYPE_MOTION_ACCL_CHANNELS
            elif parsed.ChannelMap == REC_TYPE_MOTION_GYRO_AND_ACCL:
                parsed.Type = REC_TYPE_MOTION_GYRO_AND_ACCL
                parsed.ChannelMap = REC_TYPE_MOTION_GYRO_AND_ACCL_CHANNELS
        return parsed


    def _parse_eor(self, content):
        if ERROR_HEADER_POINTS_BEYOND_EOF not in self.errors:
            eor = self._EORStruct.parse(content[
                                        self.offset + self.HeaderSize + self.header.Length - 6:
                                        self.offset + self.HeaderSize + self.header.Length - 6 + self.EORSize])

            if eor.CRC != calc_crc16(content[self.offset+1:self.offset+1+self.HeaderSize+self.header.Length-6-1]):
                self.errors.append(ERROR_WRONG_CRC)
                print(ERROR_WRONG_CRC)
            return eor
        else:
            return False
