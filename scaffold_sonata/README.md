## How to run the Scaffold model of Cerebellum using Sonata format

### A 200 x 200 micrometers example model. Simulations performed with pyNEST

### Cell types
* granule cells
* golgi cells
* Purkinje cells
* basket cells
* stellate cells
* deep cerebellar nuclei
* glomeruli - as input nodes, in a seprate population

* The input is delivered over a defined set of glomeruli, which in turn provide excitatory synaptic contacts to 
granules, golgi cells and deep cerebellar nuclei (dcn). Given that glomeruli are not actual cells, here have been modeled as virtual
(i.e., spike generators). 
To modify input -- > inputs/set_stim.py
The contacted glomeruli are defined using a 'sphere' with a certain radius and with its origin at the center of granular layer (100,100,75).
All the glomeruli included within the sphere will be stimulated with the user-defined spike trains. All the remaining spikes will receive a late spike - hopefully this can be changed. 

* Run the simulation in pyNN: --> run_scaffold.py

* To show simple raster plot of output spikes: --> output/plot_spikes.py 

## Directories
### components/cell_dynamics
json files with specific cell types dynamics (e.g., spike threshold, Cm ecc) are stored into cell_dynamics. 

### inputs 
* scaffold_full_200.0x200.0_v3.hdf5 : this file stores data to reconstruct scaffold structure and connections. This file is used here only to collect 3D coordinates of target glomeruli 
* set_stim.py : this file allows to change (some) input properties.
* external_spike_trains.h5 : the output of set_stim.py; specifies input spike-times for each glomerulus. 

### networks
Main files for network architecture reconstructions in SONATA format:
* The input population (i.e., glomeruli) is defined in external_gloms_nodes.h5 and external_gloms_node_types.csv
* The actual scaffold network is defined in scaffold_nodes.h5 and scaffold_node_types.csv

