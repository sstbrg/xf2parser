import pyedflib
import numpy as np
edf_path = r'result/20220503_sine31hz_1mv_xf2-._1652126233.EDF'
npy_path = r'result/result.npy'
number_of_batches = 100
# load npy using mmap_mode
npy_data = np.load(npy_path, mmap_mode='r')
signal_headers = [{'label': 'Ch-%d' % ii,
                   'dimension':'uV',
                   'sample_frequency': 4000,
                   'physical_max': 12582.912,
                   'physical_min': -12582.912,
                   'digital_max': int(2 ** 15 - 1),
                   'digital_min': int(-2 ** 15)} for ii in range(npy_data.shape[0])]

pyedflib.highlevel.write_edf(edf_path, signals=npy_data,
                                   signal_headers=signal_headers, digital=True, block_size=-1)
print(1)