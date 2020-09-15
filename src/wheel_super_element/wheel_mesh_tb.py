# Wheel mesh toolbox. Code should be compatible with both Python 2 and 3
from __future__ import print_function
import numpy as np

def get_node_nr(inod_radial, inod_circumf, nel_radial, nel_circumf):
    return inod_radial*nel_circumf + inod_circumf 
    
    
def get_elem_nr(iel_radial, iel_circumf, nel_radial, nel_circumf):
    return iel_radial*nel_circumf + iel_circumf
    
    
def get_elem_node_nrs(iel_radial, iel_circumf, nel_radial, nel_circumf):
    # Given the element position, return the number for the 4 nodes that build up the element.
    node_indices_radial = np.array([iel_radial,
                                    iel_radial,
                                    iel_radial + 1,
                                    iel_radial + 1], dtype=np.int)
    node_indices_circumf= np.array([iel_circumf,
                                    iel_circumf + 1 if iel_circumf < (nel_circumf - 1) else 0,
                                    iel_circumf + 1 if iel_circumf < (nel_circumf - 1) else 0,
                                    iel_circumf], dtype=np.int)
    
    return get_node_nr(node_indices_radial, node_indices_circumf, nel_radial, nel_circumf)


def get_radial_node_pos(id, od, elsize):
    # Distribute radial node positions to get elsize element length at outer diameter (od) and then 
    # approx square elements while going to inner diameter (id)
    radii = [od/2.0, od/2.0 - elsize]
    while radii[-1] > id/2:
        radii.append(radii[-1] - radii[-1]*elsize/(od/2.0))
    radii = np.array(radii)
    sfac = 1 + (id/(2*radii[-1]) - 1)*(radii[0] - radii)/(radii[0]-radii[-1])
    radii = radii*sfac
    nel_radial = radii.size - 1
    return radii, nel_radial