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
(i.e., spike generators). To modify input -- > inputs/set_stim.py
The contacted glomeruli are defined using a 'sphere' with a certain radius and with its origin at the center of granular layer (100,100,75).
All the glomeruli included within the sphere will be stimulated the user-defined spike trains. All the remaining spikes will receive a 
late spike. 

* Run the simulation in pyNN: --> run_scaffold.py

* To show simple raster plot of output spikes: --> output/plot_spikes.py 
