import numpy as np
import h5py
import json

# Load original .hdf5 file and collect positions of glomeruli
f_pos = h5py.File('scaffold_full_200.0x200.0_v3.hdf5', 'r')
positions = np.array(f_pos['positions'])

# First column: gids
# second column: cell type id
# from third to fifth: x,y,z coordinates
gloms_pos = positions[positions[:,1]==2,:]



## Set input params; duration is taken from the simulation_config.json
with open('../simulation_config.json', 'r') as config:
    sim_data = json.load(config)

duration = sim_data['run']['tstop'] # tot sim duration in msecs
stim_start = 200. # set stimulus start
stim_end = 250. # set stim end
stim_freq = 300. # frequency (burst)

# Buil input burst
spike_nums = np.int(np.round((stim_freq * (stim_end - stim_start)) / 1000.))
stim_array = np.round(np.linspace(stim_start, stim_end, spike_nums))

# Create a 'mock spike'
mockSpike = duration - 5.

# Define a 'sphere' of glomeruli to be stimulated, (origin at the center
# of granular layer). Change size of the sphere with the 'radius' variable.
# All the glomeruli falling into the sphere will be stimulated with the 'stim_array'.
# Other will receive the mockSpike
radius = 70. 

origin = np.array([100. ,100., 75.]) # for a 200 x 200 um network!
x_c, y_c, z_c = np.median(gloms_pos[:,2]), np.median(gloms_pos[:,3]), np.median(gloms_pos[:,4])

target_gloms_idx = np.sum((gloms_pos[:,2::] - np.array([x_c, y_c, z_c]))**2,axis=1).__lt__(radius**2)

stim_gloms = gloms_pos[target_gloms_idx,0].astype(int)

# Define gids and spike-times (timestamps) and update the 'external_spike_trains.h5' file (i.e., input
# file for simulation)
timestamps = []
gids = []
for glom in gloms_pos[:,0]:
    if glom in stim_gloms:
        gids.extend(np.ones(stim_array.shape[0])*glom)
        timestamps.extend(stim_array)
    else:
        gids.append(glom)
        timestamps.append(mockSpike)

gids = np.array(gids, dtype='uint32')
timestamps = np.array(timestamps)



# Build spike trains
input_file = h5py.File('external_spike_trains.h5', 'r+')
del input_file['spikes/gids']
del input_file['spikes/timestamps']

input_file['spikes'].create_dataset('gids', data=gids)
input_file['spikes'].create_dataset('timestamps', data=timestamps)


f_pos.close()
input_file.close()
