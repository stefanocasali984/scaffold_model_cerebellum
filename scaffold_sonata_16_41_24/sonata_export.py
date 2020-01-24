#nest:parrot_neuron
import os
import pyNN.nest as sim
import numpy as np
import h5py
import json
import pandas as pd

from pyNN.nest import native_cell_type
from pyNN.network import Network
from pyNN.serialization import export_to_sonata

from datetime import datetime

h5ScaffoldFile = 'scaffold_network_2020_01_20-154436.hdf5'

# Load scaffold hdf5 file
f = h5py.File(h5ScaffoldFile, 'r')

# Load configuration data as a dictionary  - exploit json to convert the string
config = f.attrs['configuration_string']
configParams = json.loads(config)

cell_gids = np.array(f['cells/positions'])[:,0]
connections_link = f['cells/connections']

# This will store in a dictionary the ID-mapping for each cell type; only mossy fibers
# should be empty and we have to add them from a different source
cellsMaps = {cellName.split('_map')[0].split('_cell')[0]: cell_gids[np.array(cellIDS)]
                for cellName, cellIDS in f['cells/type_maps'].items()
                if 'glomerulus' not in cellName}

cellsMaps['mossy'] = np.array(f['entities/mossy_fibers'])


# Convert mossy_to_glomerulus connectivity matrix into a dictionary
# here we map glomerulus (key) to its mossy fibers (value)
mossy_to_glom = {var[1]:var[0] for var in np.array(connections_link['mossy_to_glomerulus'])}
# Target glomerular connections: granule cells and golgi cells
glom_grc = np.array(connections_link['glomerulus_to_granule'])
glom_goc = np.array(connections_link['glomerulus_to_golgi'])
# Create matrices that will contain mossy to granule and mossy to golgi connections
mossy_to_grc = np.copy(glom_grc)
mossy_to_goc = np.copy(glom_goc)
# Replace glomeruli IDs with mossy fibers IDs
for idx, glom in enumerate(glom_grc[:,0]):
    mossy_to_grc[idx,0] = mossy_to_glom[glom]
for idx, glom in enumerate(glom_goc[:,0]):
    mossy_to_goc[idx,0] = mossy_to_glom[glom]


def mergeDict(d1, d2):
    ''' A small function to merge two dictionaries '''
    return (d2.update(d1))

# Mapping pyNEST parameter names to pyNN
paramKeyMap = {'C_m':'cm',
                'E_L':'v_rest',
                'I_e':'i_offset',
                'V_reset':'v_reset',
                'V_th':'v_thresh',
                't_ref':'tau_refrac',
                'tau_syn_ex':'tau_syn_E',
                'tau_syn_in':'tau_syn_I'}

# An extra parameter, so far not included in pyNN
extraParam = 'g_L'

# Load config data for cell dynamics
cellModelsDict = dict()
cellModels = configParams['simulations']['FCN_2019']['cell_models']
for cellType, params in cellModels.iteritems():
    if cellType != 'glomerulus': # Skip glomeruli: no dynamics for them!
        # BY default, assume that we're using LIF models and not EGLIF - TO BE CHANGED!
        # Parameters for cell model (LIF or EGLIF) and general parameters are stored
        # in two different dictionaries; we merge them in a single one
        cellType = cellType.split('_cell')[0]
        iaf_cond_alpha = params['iaf_cond_alpha']
        parameters = params['parameters']
        cellParams = parameters.copy()
        mergeDict(iaf_cond_alpha, cellParams)
        # Update parameter names
        for paramName in paramKeyMap.iterkeys():
            cellParams[paramKeyMap[paramName]] = cellParams[paramName]
            cellParams.pop(paramName, None)
        cellParams.pop(extraParam, None)
        # Populate dictionary with Population models for each cell type
        popSize = len(cellsMaps[cellType])
        cellModelsDict[cellType] = sim.Population(popSize, sim.IF_cond_alpha(**cellParams), label=cellType)

# Manually add the mossy fibers: these are parrot neurons -- native cell type from nest
mossy_cells = native_cell_type('parrot_neuron')
mfSize = len(cellsMaps['mossy'])
cellModelsDict['mossy'] = sim.Population(mfSize, mossy_cells(), label='mossy')

# IDs remapping procedure: pyNN assigns IDs to cells; remap scaffold IDs to pyNN IDs;
IDsMap = dict()
for cellT in cellModelsDict.iterkeys():
    cMap = cellsMaps[cellT]
    pynnMap = cellModelsDict[cellT].all_cells
    IDsMap[cellT.split('_cell')[0]] = {key1:key2 for key1, key2 in zip(cMap, pynnMap)}

# Next steps:
# 1 - Connections dataset contains a couple of connection including glomeruli :
#     these should be removed
connectionsData = {key: np.array(value) for key, value in connections_link.iteritems() if 'glomerulus' not in key}
# 2 - mossy_to_grc and mossy_to_goc must be added to connectionsData dictionary
connectionsData['mossy_to_granule'] = mossy_to_grc
connectionsData['mossy_to_golgi'] = mossy_to_goc
connectionsData['io_to_basket'][:,1] += len(cellsMaps['stellate'])

upDateConnections = dict()
# 3 - Now we can update connections IDs into the connectivity matrices
for connKey, connMat in connectionsData.iteritems():
    if connMat.shape[0] > 0:
        connLabels = connKey.split('_to_')
        preLabel = connLabels[0]
        postLabel = connLabels[1]
        if preLabel == 'ascending_axon' or preLabel == 'parallel_fiber':
            preLabel = 'granule'
        connMat[:,0] = np.array([IDsMap[preLabel][pre] for pre in connMat[:,0]])
        connMat[:,1] = np.array([IDsMap[postLabel][post] for post in connMat[:,1]])
        upDateConnections[connKey] = connMat
        print preLabel, postLabel


def ConnectCells(connMat, popPre, popPost, weight, delay):
    prePostPairs = []
    for pair in connMat:
        pre = np.where(popPre.all_cells == pair[0])[0][0]
        post = np.where(popPost.all_cells == pair[1])[0][0]
        prePostPairs.append((pre, post))
    conn = sim.FromListConnector(prePostPairs)
    ss = sim.StaticSynapse(weight=weight, delay=delay)
    return sim.Projection(popPre, popPost, conn, ss)

PopProjections = dict()
connectionParams =dict()
for key, val in configParams['simulations']['FCN_2019']['connection_models'].iteritems():
    if 'glomerulus' == key.split('_')[0]:
        key = key.replace('glomerulus', 'mossy')
    connectionParams[key] = val


for connName, conn in upDateConnections.iteritems():
    preLabel = connName.split('_to_')[0]
    if preLabel == 'ascending_axon' or preLabel == 'parallel_fiber':
        preLabel = 'granule'
    postLabel = connName.split('_to_')[1]

    connMat = conn
    popPre = cellModelsDict[preLabel]
    popPost = cellModelsDict[postLabel]
    if connName == 'purkinje_to_dcn_interneuron': # synaptic parameters for pc --> dcn interneuron are
    # equal to pc --> dcn
        newConn = 'purkinje_to_dcn'
        weight = connectionParams[newConn]['connection']['weight']
        delay = connectionParams[newConn]['connection']['delay']
    else:
        weight = connectionParams[connName]['connection']['weight']
        delay = connectionParams[connName]['connection']['delay']


    PopProjections[connName] = ConnectCells(connMat, popPre, popPost, weight, delay)
    print "Connection between {} and {} done".format(preLabel, postLabel)



populations = [population for population in cellModelsDict.itervalues()]
projections = [projection for projection in PopProjections.itervalues()]

netData = populations + projections

net = Network(*netData)

# Generate name for data directory
now = datetime.now()
current_time = now.strftime("%H_%M_%S")
targetDirName = 'scaffold_sonata_{}'.format(current_time)

export_to_sonata(net, targetDirName)

# mossy_csv = '/{}/networks/node_types_mossy.csv'.format(targetDirName)
# path = os.getcwd()+mossy_csv
#
# mf_csv = pd.read_csv(path, sep=' ')
# mf_csv['model_template'] = 'nest:parrot_neuron'
# mf_csv.to_csv(path)
