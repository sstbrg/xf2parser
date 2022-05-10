from pyedflib.highlevel import write_edf_quick
import attr

@attr.define
class EDFProcessor(object):

    file_path = attr.ib(default='')

    def dump_to_edf(self, data_in, sample_rate):
        # EDF needs [channels x samples]
        print('INFO: writing edf file %s' % self.file_path)
        write_edf_quick(edf_file=self.file_path,
                        signals=data_in,
                        sfreq=sample_rate,
                        digital=False)
        print('INFO: finished writing edf file')