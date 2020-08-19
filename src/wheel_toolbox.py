# Python libraries
import numpy as np

# Abaqus libraries
import part
import mesh

def define_contact_nodes(the_part, geometry, the_mesh):    
    nodes = get_contact_nodes(geometry, the_mesh, the_part.nodes)
    contact_nodes_set_name = 'CONTACT_NODES'
    contact_nodes = the_part.Set(name=contact_nodes_set_name, nodes=nodes)
    
    return contact_nodes, contact_nodes_set_name
    

def get_contact_nodes(geometry, the_mesh, nodes):
    x0 = 0.0
    y0 = geometry['outer_diameter']/2.0
    min_radius = geometry['outer_diameter']/2.0 - the_mesh['fine']/100
    max_angle = geometry['rolling_angle']/2.0 + geometry['max_contact_length']/geometry['outer_diameter']
    
    node_list = []
    for n in nodes:
        # Coordinates relative wheel center
        xrel = n.coordinates[0] - x0
        yrel = n.coordinates[1] - y0
        radius = np.sqrt(xrel**2 + yrel**2)
        if radius > min_radius:
            angle = np.arccos(-yrel/radius)
            if  angle < max_angle:
                node_list.append(n)
    
    return mesh.MeshNodeArray(node_list)