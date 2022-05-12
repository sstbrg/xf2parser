from XF2Parser import *

local_work_directory = r'C:\Users\Stas\Documents\xtrodes\data\20220512_xf2_allnight_sine\RECORDS'
local_output_path = r'result\result.npy'

parser = Parser(work_directory = local_work_directory)
parser.process_files(save_path=local_output_path, transpose_data=True)
