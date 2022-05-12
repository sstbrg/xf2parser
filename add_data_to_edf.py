import pyedflib
import numpy as np
edf_path = r'result/20220503_sine31hz_1mv_xf2-._1652126233.EDF'
npy_path = r'result/result.npy'
number_of_batches = 100
samples_per_batch = 4000 #should represet one second!
# load npy using mmap_mode
npy_data = np.load(npy_path, mmap_mode='r')
split_npy_data = np.split(npy_data, indices_or_sections=[samples_per_batch*(i+1) for i in range(int(npy_data.shape[1]/samples_per_batch))], axis=1)

signal_headers = [{'label': 'Ch-%d' % ii,
                   'dimension':'uV',
                   'sample_frequency': 4000,
                   'physical_max': 12582.912,
                   'physical_min': -12582.912,
                   'digital_max': int(2 ** 15 - 1),
                   'digital_min': int(-2 ** 15)} for ii in range(npy_data.shape[0])]

edf_writer = pyedflib.EdfWriter(file_name=edf_path, n_channels=npy_data.shape[0])
edf_writer.setSignalHeaders(signal_headers)

for databatch in split_npy_data:
    if databatch.shape[1] < samples_per_batch:
        databatch = np.pad(databatch, pad_width=samples_per_batch-databatch.shape[1], mode='constant', constant_values=0)
    databatch = np.reshape(databatch, newshape=(databatch.shape[0]*databatch.shape[1],), order='C')
    edf_writer.blockWriteDigitalShortSamples(databatch)

edf_writer.close()

print(1)