# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import odbAccess


def get_nodal_results(odb_name):
    # Read results from odb file and return the following numpy arrays
    # outer_node_coord  [(x,y,z), node_nr]              Coordinates for outer nodes
    # outer_node_RF     [stpnr, (RF1, RF2), node_nr]    Reaction forces for outer nodes
    # rp_node_RF        [stpnr, (RF1, RF2, RM3)]        Reaction forces/moments for rp node
    # -------------------------------------------------------------------------------------
    
    odb = odbAccess.openOdb(path=odb_name + '.odb')
    assy = odb.rootAssembly
    inst = assy.instances['SUPER_WHEEL']
    outer_nodes = inst.nodeSets['OUTER_CIRCLE'].nodes
    rp_node = assy.nodeSets['RP'].nodes[0][0]
    
    num_steps = 4
    outer_node_variable_keys = ['RF1', 'RF2']
    rp_node_variable_keys = ['RF1', 'RF2', 'RM3']
        
    # Save node coordinates
    outer_node_coord = np.zeros((3, len(outer_nodes)))
    inod = 0
    for node in outer_nodes:
        outer_node_coord[:, inod] = np.array(node.coordinates)
        inod = inod + 1
    
    # Save node reaction forces (and moment for rp node)
    outer_node_RF = np.zeros((4, len(outer_node_variable_keys), len(outer_nodes)))
    rp_node_RF = np.zeros((4, len(rp_node_variable_keys)))
    istp = 0
    for stp_key in odb.steps.keys():
        history_regions = odb.steps[stp_key].historyRegions
        node_hr = {int(label.split('.')[-1]):hr     # Get nodal history regions
                   for label, hr in history_regions.items() if 'Node' in label}
        
        inod = 0
        for node in outer_nodes:
            ikey = 0
            for key in outer_node_variable_keys:
                ndata = node_hr[node.label].historyOutputs[key].data
                outer_node_RF[istp, ikey, inod] = ndata[-1][-1]
                ikey = ikey + 1
            inod = inod + 1
        ikey = 0
        for key in rp_node_variable_keys:
            ndata = node_hr[rp_node.label].historyOutputs[key].data
            rp_node_RF[istp, ikey] = ndata[-1][-1]
            ikey = ikey + 1
        istp = istp + 1
    
    odb.close()
    
    return outer_node_coord, outer_node_RF, rp_node_RF
    