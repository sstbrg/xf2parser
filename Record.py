from XF2Types import *
import binascii

# def calc_crc16(bytes_in):
#     crc16 = crcmod.mkCrcFun(CRC_POLYNOMIAL, CRC_STARTING_VALUE, CRC_BIT_REVERSAL, CRC_XOR_OUT)
#     result = crc16(bytes_in)
#     #print('INFO: CRC=%d' % result)
#     return result

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
        self.HeaderSize = sum([sub.length for sub in self._HeaderStruct.subcons])
        self.EORSize = sum([sub.length for sub in self._EORStruct.subcons])
        self.header = self._parse_header(content)
        self.eor = self._parse_eor(content)
        self.errors = self._check_record(content)

    def _parse_header(self, content):
        #print('Offset=%d' % self.offset)
        parsed = self._HeaderStruct.parse(content[self.offset:self.offset+self.HeaderSize])
        if parsed.Type == REC_TYPE_ADC:
            parsed.ChannelMap = [num if val == '1' else None for num, val in
                               enumerate(list(bin(parsed.ChannelMap).lstrip('0b')))]
        elif parsed.Type == REC_TYPE_MOTION:
            if int(bin(parsed.ChannelMap).lstrip('0b')) == 1:
                parsed.ChannelMap = 1

        #print('Length=%d, Sor=%d' % (parsed.Length, parsed.Sor))
        return parsed

    #data = attr.field()

    #@data.default
    #def _parse_data(self):
    #    # The data is variable so we have to define the struct each and every time we parse a record
    #    data = Struct('Data' / Array(self.header['Length'], Int8ul))
    #    return data.parse(self._filecontents[self.offset+self._HeaderSize:self.offset+self._HeaderSize+self.header.Length])


    def _check_record(self, content):
        errors = list()
        if self.header.Sor != START_OF_RECORD:
            errors.append(ERROR_WRONG_SOR_IN_HEADER)

        #if self._filecontents[0][self.offset + self.HeaderSize + self.header.Length + self.EORSize - 1] != END_OF_RECORD:
        if content[
            self.offset + self.HeaderSize + self.header.Length - 6 + self.EORSize - 1] != END_OF_RECORD:
            errors.append(ERROR_WRONG_EOR)

        #if self.eor.CRC != calc_crc16(content[self.offset + 1:
        #    self.offset + self.HeaderSize + 3840]):
        #    self.errors.append(ERROR_WRONG_CRC)

        return errors


    def _parse_eor(self, content):
        #eor = self._EORStruct.parse(self._filecontents[0][
        #                                 self.offset + self.HeaderSize + self.header.Length:
        #                                 self.offset + self.HeaderSize + self.header.Length + self.EORSize])

        eor = self._EORStruct.parse(content[
                                    self.offset + self.HeaderSize + self.header.Length - 6:
                                    self.offset + self.HeaderSize + self.header.Length - 6 + self.EORSize])

        if eor.CRC != calc_crc16(content[self.offset+1:
            self.offset+1+self.HeaderSize+self.header.Length-6-1]):
            self.errors.append(ERROR_WRONG_CRC)

        return eor