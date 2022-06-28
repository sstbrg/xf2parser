import attr
from construct import *
START_OF_SAMPLING_RECORD = b'\x0D\xA0'
START_OF_MOTION_RECORD = b'\x0D\xA1'
REC_TYPE_ADC = 160
REC_TYPE_MOTION = 161
REC_TYPE_MOTION_GYRO = 1
REC_TYPE_MOTION_ACCL = 2
REC_TYPE_MOTION_GYRO_AND_ACCL = 3

START_OF_FILE = b'\x0D\x00'
START_OF_RECORD = 13
END_OF_RECORD = 10
ERROR_WRONG_SOR_IN_HEADER = 'ERROR: Wrong SOR in header'
ERROR_WRONG_EOR = 'ERROR: Wrong EOR based on record structure'
ERROR_WRONG_CRC = 'ERROR: Calculated CEC does not match recorded CRC'
ERROR_CHANNEL_MAP_CHANGED = 'ERROR: Channel map has changed within the file'

CRC_POLYNOMIAL = 0xAF01 #int.from_bytes(b'\xAF\x01', byteorder='little')
CRC_STARTING_VALUE = 0x0000
CRC_BIT_REVERSAL = True
CRC_XOR_OUT = 0x0000

# RECORDS_TABLE_COLUMNS = {'UnixTime':0, 'PacketIndex':1, 'Type':2, 'DataOffset':3, 'Length':4, 'NumOfActiveChannels':5,
#                          'IMUType':6}

NUMBER_OF_HW_ADC_CHANNELS = 16
NUMBER_OF_HW_GYRO_CHANNELS = 3
NUMBER_OF_HW_ACCL_CHANNELS = 3

ADC_RESOLUTION = 768e-9
ADC_BITS = 15

IMU_BITS = 16

EL_PHYS_MAX = 12582.912  #uV
EL_PHYS_MIN = -12582.912  #uV
EL_DIG_MAX = 2 ** 14 - 1
EL_DIG_MIN = -2 ** 14
ACCL_PHYS_MAX = 16 #g #+19.6 / 9.80665
ACCL_PHYS_MIN = -16 #g #-19.6 / 9.80665
ACCL_DIG_MAX = 2 ** 15 - 1
ACCL_DIG_MIN = -2 ** 15
GYRO_PHYS_MAX = 2000 #dps
GYRO_PHYS_MIN = -2000 #dps
GYRO_DIG_MAX = 2 ** 15 - 1
GYRO_DIG_MIN = -2 ** 15
FILE_FORMAT = '.XF2'

@attr.define
class RecordStruct(Struct):
    Header = attr.ib(default=Struct(
            'Sor' / Int8ul,
            'Type' / Int8ul,
            'UnixTime' / Int32ul,
            'UnixMs' / Int16ul,
            'Length' / Int16ul,
            'PacketIndex' / Int16ul,
            'ChannelMap' / Int16ul,
            'SampleRate' / Int16ul,
            'DownSamplingFactor' / Int8ul))
    #Data = Struct('Data' / Array(header['Length'], Int8ul))
    EOR = attr.ib(default=Struct(
            'CRC' / Int16ul,
            'Eor' / Int8ul
        ))

