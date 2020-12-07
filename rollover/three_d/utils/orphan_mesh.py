



def convert_to(the_part, exclude_cells):
    """ Convert part of a meshed part to an orphan mesh part 
    maintaining sets and surfaces
    
    :param the_part: The part to be converted
    :type the_part: Part object (Abaqus)
    
    :param exclude_cells: Cells in the_part that should not be included
                          in the orphan mesh
    :type exclude_cells: list[ Cell object (Abaqus) ]
    
    """
    
    # Save key set and surface information
    sets_info = {key: get_set_info(the_part, key) for key in the_part.sets.keys()}
    surfs_info = {key: get_surf_info(the_part.surfaces[key]) for key in the_part.surfaces.keys()}
    
    # Make orphan mesh part
    
    
    # Redefine sets and surfaces
        
    
    
def get_set_info(the_set):
    """ Get information about the set, such that it can be regenerated 
    even after the mesh is redefined (i.e. after changes to node and 
    element numbering)
    
    :param the_set: The set to aquire info about
    :type the_set: Set object (Abaqus)
    
    :returns: Dictionary with the following fields:
    
    * 'nodes': list of lists (len=3) with node coordinates for all nodes
      involved in the_set (either inside, or part of element)
    * 'node_inds': Indicies in list 'nodes' that belong to the set
      themselves (i.e. excluding those only part of an element)
    * 'elems': list of lists with indices corresponding to list 'nodes'
      
    :rtype: dict
    
    """
    
    set_info = {'nodes': [], 'node_inds': [], 'elems': []}
    old_nodes = []
    old_set_nodes = the_set.nodes
    for elem in the_set.elements:
        set_info['elems'].append([])
        for enod in elem.getNodes():
            try: 
                ind = old_nodes.index(enod)
            except ValueError:
                # Could not find enod in old_nodes, add it
                old_nodes.append(enod)
                ind = len(old_nodes)-1
                
                # Also add the node coordinates 
                set_info['nodes'].append(enod.coordinates)
                
                # If node inside set, add its new index to 'node_inds'
                if enod in old_set_nodes:
                    set_info['node_inds'].append(ind)
                    
                
            set_info['elems'][-1].append(ind)
    
    return set_info
    

def get_surf_info(the_surf):
    """ Get information about the_surf, such that it can be regenerated 
    even after the mesh is redefined (i.e. after changes to node and 
    element numbering)
    
    :param the_surf: The surface to aquire info about
    :type the_surf: Surface object (Abaqus)
    
    :returns: Dictionary with the following fields:
    
    * 'nodes': list of lists (len=3) with node coordinates for all nodes
      involved in the_set (either inside, or part of element)
    * 'elem_faces': list of list of indicies in list 'nodes' that belong 
      to the surface for each element face. 
      
    :rtype: dict
    
    """
    
    surf_info = {'nodes': [], 'elem_faces': []}
    old_nodes = []
    for face in the_surf.faces:
        for ef in face.getElementFaces():
            surf_info['elem_faces'].append([])
            for ef_nod in ef.getNodes():
                try:
                    ind = old_nodes.index(ef_nod)
                except ValueError:
                    old_nodes.append(ef_nod)
                    ind = len(old_nodes) - 1
                    
                    surf_info['nodes'].append(ef_nod.coordinates)
                    
                surf_info['elem_faces'][-1].append(ind)
    
    return surf_info
