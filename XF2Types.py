import attr
from construct import *
START_OF_SAMPLING_RECORD = b'\x0D\xA0'
START_OF_MOTION_RECORD = b'\x0D\xA1'
REC_TYPE_ADC = 160
REC_TYPE_MOTION = 161
START_OF_FILE = b'\x0D\x00'
START_OF_RECORD = 13
END_OF_RECORD = 10
ERROR_WRONG_SOR_IN_HEADER = 'ERROR: Wrong SOR in header'
ERROR_WRONG_EOR = 'ERROR: Wrong EOR based on record structure'
ERROR_WRONG_CRC = 'ERROR: Calculated CEC does not match recorded CRC'

CRC_POLYNOMIAL = 0xAF01 #int.from_bytes(b'\xAF\x01', byteorder='little')
CRC_STARTING_VALUE = 0x0000
CRC_BIT_REVERSAL = True
CRC_XOR_OUT = 0x0000

# RECORDS_TABLE_COLUMNS = {'UnixTime':0, 'PacketIndex':1, 'Type':2, 'DataOffset':3, 'Length':4, 'NumOfActiveChannels':5,
#                          'IMUType':6}

NUMBER_OF_HW_ADC_CHANNELS = 16
NUMBER_OF_HW_MOTION_CHANNELS = 3

ADC_RESOLUTION = 768e-9
ADC_BITS = 15

EL_PHYS_MAX = 12582.912  # to make it uV
EL_PHYS_MIN = -12582.912  # to make it uV
EL_DIG_MAX = 2 ** 14 - 1
EL_DIG_MIN = -2 ** 14
ACC_PHYS_MAX = +19.6 / 9.80665
ACC_PHYS_MIN = -19.6 / 9.80665
ACC_DIG_MAX = 2 ** 15 - 1
ACC_DIG_MIN = -2 ** 15

FILE_FORMAT = '.XF2'

@attr.define
class RecordStruct(Struct):
    Header = attr.ib(default=Struct(
            'Sor' / Int8ul,
            'Type' / Int8ul,
            'UnixTime' / Int32ul,
            'Length' / Int16ul,
            'PacketIndex' / Int16ul,
            'ChannelMap' / Int16ul,
            'SampleRate' / Int16ul))
    #Data = Struct('Data' / Array(header['Length'], Int8ul))
    EOR = attr.ib(default=Struct(
            'CRC' / Int16ul,
            'Eor' / Int8ul
        ))

