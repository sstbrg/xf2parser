import aux_functions
from parser_for_QA_test import iterate_over_xf2_files
from itertools import tee
from XF2Parser import *
from EDFExport import *
import traceback
import os.path
from cmd import Cmd

import warnings

warnings.filterwarnings("ignore")


class Xshell(Cmd):

    def do_test(self, args):
        """test <path_to_folder_with_xf2_files>
"""
        try:
            local_work_directory = args
            dataset_name = os.path.basename(local_work_directory)

            parser = Parser(work_directory=local_work_directory)
            data_gen = parser.process_files(exclude=())

            corr_gen, edf_gen = tee(data_gen)
            num_of_files_for_corr = len(os.listdir(local_work_directory)) - 1
            timestamps, t0 = iterate_over_xf2_files(corr_gen, num_of_files_for_corr, corr_flag=True, dummy_flag=False)

            timstapmps_df = aux_functions.write_corr_res(timestamps, t0)
            timstapmps_df.to_csv(f"{dataset_name}_corr_ts.csv")
            if len(timestamps) <= 1:
                print(f"{local_work_directory} passed the test")
            else:
                print(f"{local_work_directory} failed the test")

            print(f'Generating annotated EDF {dataset_name}:')

            edfer = EDFProcessor(file_path=f'{dataset_name}_tested.edf')

            if edfer.check_dataset_size(local_work_directory):
                edfer.save_to_edf(data_generator=edf_gen, write_record_created_annotations=False, testing=1,
                                  anotations=timestamps)
        except Exception as e:
            print(f'ERROR')
            print(str(e))
            traceback.print_exc()
            return False


def main():
    prompt = Xshell()

    prompt.prompt = '> '
    prompt.cmdloop('XF2 data integrity tool.\n')


if __name__ == '__main__':
    main()
