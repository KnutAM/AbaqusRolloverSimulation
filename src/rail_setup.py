# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqusConstants import *
import assembly
import part
import sketch
import mesh
import section

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not src_path in sys.path:
    sys.path.append(src_path)

from material_and_section_module import setup_sections
import user_settings

def test_script():
    # Settings
    rail_geometry = user_settings.rail_geometry
    rail_mesh = user_settings.rail_mesh
    rail_naming = user_settings.rail_naming  
    
    # Setup model
    model = mdb.models.values()[0]
    assy = model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    setup_sections(model, naming={'rail': rail_naming['section'], 
                                  'shadow': rail_naming['shadow_section']})
    
    rail_part, rail_contact_surf = setup_rail(model, assy, rail_geometry, rail_mesh, rail_naming)
    
    
def setup_rail(model, assy, geometry, mesh, naming):
    # Input
    #   model       The full abaqus model section_name
    #   assy        The full assembly (for all parts)
    #   geometry    Dictionary describing the geometry
    #    req.        'length', 'height', 'max_contact_length'
    #   mesh        Dictionary describing the mesh parameters
    #    req.        'fine'
    #   naming      Dictionary containing the names for part, section etc.
    #    req.        'part', 'section', 'shadow_section'
    #   
    # Output
    #   part                The rail part
    #   contact_surface     Surface
    #   
    # Modified
    #   model       The rail parts, sketches etc. will be added
    #   assy        adding surfaces, the rail part, etc. 
    # -------------------------------------------------------------------------
    
    # Create part and add instance to assembly
    part = model.Part(name=naming['part'], dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    inst = assy.Instance(name=naming['part'], part=part, dependent=ON)
    
    # Sketch the rail profile
    sketch = sketch_rail(model, geometry, mesh)
    
    # Make the base shell
    part.BaseShell(sketch=sketch)
    sketch.unsetPrimaryObject()
    
    # Partitioning
    partition_sketch = partition_rail(model, geometry, mesh)
    part.PartitionFaceBySketch(faces=part.faces.findAt(((0.0, -1.0, 0.0),)), sketch=partition_sketch)
    
    # Assign sections
    define_sections(part, geometry, mesh, naming)
    
    # Mesh rail part
    mesh_rail(part, geometry, mesh)
    
    # Find and connect node pairs (right and left vertical faces, as well as shadow_pairs)
    lr_pairs = find_rail_node_pairs_left_right(part, geometry, mesh)
    shadow_pairs = find_shadow_nodes(part, geometry, mesh)
    connect_nodes(model, assy, part, geometry, mesh, (lr_pairs, shadow_pairs))
    
    # Define contact surface
    rail_contact_surface = define_contact_surface(assy, inst, geometry, mesh)
    top_edge = part.edges.findAt(((0., 0., 0.),))
    part.Set(edges=top_edge, name='CONTACT_NODES') # Only contact nodes not in shadow set
    
    # Define bottom region (where boundary conditions will be applied)
    bottom_edge = part.edges.findAt(((0., -geometry['height'], 0.),))
    bottom_region = part.Set(edges=bottom_edge, name='BOTTOM_NODES')
    
    return part, rail_contact_surface, bottom_region

    
def sketch_rail(model, geometry, mesh):
    # Input:
    # geometry      Dictionary containing geometry information
    #  req. fields: length, height, shadow_line_length
    # mesh          Dictionary containing mesh information
    #  req. fields: fine
    # 
    # Output (model is modified)
    #  sketch       The created sketch for the rail part
    # ---
    
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, mesh)
    
    sketch = model.ConstrainedSketch(name='__rail_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    
    dx = geometry['length']/2.0
    dy = geometry['height']
    dxs = -(dx + shadow_line_length)
    dys = -mesh['fine']
    sketch.Line(point1=( dx,  0.), point2=( dx, -dy))
    sketch.Line(point1=( dx, -dy), point2=(-dx, -dy))
    sketch.Line(point1=(-dx, -dy), point2=(-dx, dys))
    sketch.Line(point1=(-dx, dys), point2=(dxs, dys))
    sketch.Line(point1=(dxs, dys), point2=(dxs,  0.))
    sketch.Line(point1=(dxs,  0.), point2=( dx, 0.))
    
    return sketch


def partition_rail(model, geometry, mesh):
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, mesh)
    
    partition_sketch = model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    partition_sketch.Line(point1=(-geometry['length']/2.0-shadow_line_length-1., -mesh['fine']), 
                          point2=(geometry['length']/2.0+1., -mesh['fine']))
    partition_sketch.Line(point1=(-geometry['length']/2.0, 0.), point2=(-geometry['length']/2.0, -mesh['fine']))
    
    return partition_sketch
    
    
def mesh_rail(part, geometry, the_mesh):

    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, the_mesh)
    number_of_top_elements = int(geometry['length']/the_mesh['fine'])
    
    part.seedEdgeByNumber(edges=part.edges.findAt(((0.0, 0.0, 0.0),)), 
                          number=number_of_top_elements, constraint=FIXED)
    part.seedEdgeByNumber(edges=part.edges.findAt(((-geometry['length']/2.0-shadow_line_length/2.0, 0.0, 0.0),)), 
                          number=number_of_shadow_elements, constraint=FIXED)
    part.seedEdgeByBias(biasMethod=SINGLE, 
                        end2Edges=part.edges.findAt(((-geometry['length']/2.0, -geometry['height']/2.0, 0.0),)),
                        end1Edges=part.edges.findAt(((+geometry['length']/2.0, -geometry['height']/2.0, 0.0),)), 
                        minSize=the_mesh['fine'], maxSize=the_mesh['coarse'], constraint=FIXED)  # FIXED ensures compat. meshes
                        
    part.setElementType(regions=part.sets['rail_set'], elemTypes=(mesh.ElemType(elemCode=CPE4),))
    part.generateMesh()
    
    
def define_sections(part, geometry, mesh, naming):
    # Create 2 sections, one for the actual rail and one for the shadow part, named by 
    # naming['section'] and naming['shadow_section'] respectively
    
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, mesh)
    
    faces = part.faces.findAt(((0., -mesh['fine']/2.0, 0.),),((0., -1.5*mesh['fine'], 0.),))
    region = part.Set(faces=faces, name='rail_set')
    part.SectionAssignment(region=region, sectionName=naming['section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
        
    shadow_face = part.faces.findAt(((-geometry['length']/2.0-shadow_line_length/2.0, -mesh['fine']/2.0, 0.),))
    shadow_region = part.Set(faces=shadow_face, name='shadow_set')
    part.SectionAssignment(region=shadow_region, sectionName=naming['shadow_section'], offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    
def get_shadow_rail_length_and_nel(geometry, mesh):
    number_of_top_elements = int(geometry['length']/mesh['fine'])
    number_of_shadow_elements = int(geometry['max_contact_length']/mesh['fine'])
    shadow_line_length = (geometry['length']/number_of_top_elements) * number_of_shadow_elements
    return shadow_line_length, number_of_shadow_elements
    
    
def find_rail_node_pairs_left_right(part, geometry, mesh):
    edges = part.edges.findAt(((-geometry['length']/2.0, -(geometry['height']-mesh['fine'])/2.0, 0.0),),
                              (( geometry['length']/2.0, -(geometry['height']-mesh['fine'])/2.0, 0.0),))
    vertices = part.vertices.findAt(((-geometry['length']/2.0, 0.0, 0.0),),
                                    (( geometry['length']/2.0, 0.0, 0.0),))
                                    
    # Find nodes that are within a tolerance from each other in y-z coordinates
    yzcoords = []
    nodes = []
    for e in edges:
        nodes.append(e.getNodes())
        coordmat = np.zeros((len(nodes[-1]), 2))
        ind = 0
        for n in nodes[-1]:
            coord = n.coordinates
            coordmat[ind, :] = np.array([coord[1], coord[2]])
            ind = ind + 1
            
        yzcoords.append(coordmat)
    
    node_pairs = [[vertices[0].getNodes()[0], vertices[1].getNodes()[0]]]
    indl = 0
    crs = yzcoords[1]
    for cl in yzcoords[0]:
        dist = (crs[:,0]-cl[0])**2 + (crs[:,1]-cl[1])**2
        indr = np.argmin(dist)
        node_pairs.append([nodes[0][indl], nodes[1][indr]])
        indl = indl + 1
    
    return node_pairs


def find_shadow_nodes(part, geometry, mesh):
    node_connect_tolerance = 1.e-6
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, mesh)
    length = geometry['length']
    # First identify the two nodes already linked, these should not be included
    vertices = part.vertices.findAt(((-geometry['length']/2.0, 0.0, 0.0),),
                                    ((-geometry['length']/2.0, -mesh['fine'], 0.0),))
    # No connect nodes
    nc_nodes = [vertices[0].getNodes()[0], vertices[1].getNodes()[0]]
    
    # Find the coordinates of the nodes to connect
    shadow_x_center = -(geometry['length']+shadow_line_length)/2.0
    shadow_edges = part.edges.findAt(((shadow_x_center, 0.0, 0.0),),
                                     ((shadow_x_center, -mesh['fine'], 0.0),))
    true_edges = part.edges.findAt(((0.0, 0.0, 0.0),),
                                   ((0.0, -mesh['fine'], 0.0),))
    
    yzcoords = []
    nodes = []
    for edges in [shadow_edges, true_edges]:
        tmp_coords = []
        nodes.append([])
        for e in edges:
            edge_nodes = e.getNodes()            
            for n in edge_nodes:
                nodes[-1].append(n)
                coord = n.coordinates
                tmp_coords.append(n.coordinates)
        yzcoords.append(np.array(tmp_coords))
        
    # Determine matching nodes
    number_already_used = 0
    node_pairs = []
    for sn, sc in zip(nodes[0], yzcoords[0]):  # Shadow nodes, shadow coordinates
        if sn != nc_nodes[0] and sn != nc_nodes[1]:
            dist = (yzcoords[1][:,0]-length-sc[0])**2 + (yzcoords[1][:,1]-sc[1])**2 + (yzcoords[1][:,2]-sc[2])**2
            ind = np.argmin(dist)
            if dist[ind] < node_connect_tolerance**2:
                node_pairs.append([sn, nodes[1][ind]])
            else:
                print("WARNING: No matching nodes found, minimum distance = " + str(np.sqrt(dist[ind])))
        else:
            # Found node that has already been used, this is expected to occur twice
            number_already_used = number_already_used + 1
            
    if number_already_used != 2:
        print('Expected to find a node that has been used twice, but found ' + str(number_already_used))
        
    return node_pairs
    
    
def connect_nodes(model, assy, rail, geometry, mesh, node_pairs_lists):
    node_pairs = []
    for node_pairs_list in node_pairs_lists:
        for node_pair in node_pairs_list:
            node_pairs.append(node_pair)
            
    set_nr = 1
    for np in node_pairs:
        names = ['NodeConnectSet' + side + '-' + str(set_nr) for side in ['Left', 'Right']]
        node_seq_left = rail.nodes.sequenceFromLabels((np[0].label,))
        node_seq_right = rail.nodes.sequenceFromLabels((np[1].label,))
        rail.Set(nodes=node_seq_left, name=names[0])
        rail.Set(nodes=node_seq_right, name=names[1])
        set_nr = set_nr + 1
    
    assy.regenerate()
    for set_nr in range(len(node_pairs)):
        names = ['NodeConnectSet' + side + '-' + str(set_nr+1) for side in ['Left', 'Right']]
        # Link x-degree of freedom
        model.Equation(name='NodeConnectConstraintX-'+str(set_nr), terms=((1.0, 
        'RAIL.'+names[0], 1), (-1.0, 'RAIL.'+names[1], 1)))
        # Link y-degree of freedom
        model.Equation(name='NodeConnectConstraintY-'+str(set_nr), terms=((1.0, 
        'RAIL.'+names[0], 2), (-1.0, 'RAIL.'+names[1], 2)))
        # For 3D link also z-degree of freedom (not implemented)
        
        
def define_contact_surface(assy, inst, geometry, mesh):
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel(geometry, mesh)
    rail_contact_surface = assy.Surface(side1Edges=inst.edges.findAt(((0.,0.,0.),), 
        (((-geometry['length']-shadow_line_length)/2.0, 0.0, 0.0),)), 
        name='RAIL_CONTACT_SURFACE')
        
    return rail_contact_surface
        

if __name__ == '__main__':
    test_script()
