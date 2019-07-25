import numpy as np
import json
import numpy as np
import h5py
import matplotlib.pyplot as plt
plt.interactive(True)
from scaffold_params import cell_type_ID

# Load scaffold for mapping of gids to cell-types
gids_file = h5py.File('../inputs/scaffold_full_200.0x200.0_v3.hdf5', 'r')
gids_ctypes = np.array(gids_file['positions'][:,[0,1]])

# Load name of spikes file from simualtion_config.json
with open('../simulation_config.json', 'r') as config:
	spikes_file = json.load(config)['output']['spikes_file']
	
f = h5py.File(spikes_file, 'r')

spikes = np.column_stack([np.array(f['spikes/gids']), np.array(f['spikes/timestamps'])])

gids_file.close()
f.close()

def mapGID_cellType(ctype):
	cnum = cell_type_ID[ctype]
	gids = gids_ctypes[gids_ctypes[:,1]==cnum,0]
	indicies = np.isin(spikes[:,0], gids)
	return spikes[indicies]

# Divide spikes for each cell type 
goc_spikes = mapGID_cellType('golgi') # golgi
grc_spikes = mapGID_cellType('granule') # granule 
pc_spikes = mapGID_cellType('purkinje') # purkinje
sc_spikes = mapGID_cellType('stellate') # stellate
bc_spikes = mapGID_cellType('basket') # basket
dcn_spikes = mapGID_cellType('dcn') # deep cerebellar nuclei

# Example: raster plots of golgi, granule and purkinje cells
plt.figure()
plt.subplot(311)
plt.plot(goc_spikes[:,1], goc_spikes[:,0], 'b.')
plt.xlim([0,495]) # time limits
plt.subplot(312)
plt.plot(grc_spikes[:,1], grc_spikes[:,0], 'r.')
plt.xlim([0,495]) # time limits
plt.subplot(313)
plt.plot(pc_spikes[:,1], pc_spikes[:,0], 'g.')
plt.xlim([0,495]) # time limits
