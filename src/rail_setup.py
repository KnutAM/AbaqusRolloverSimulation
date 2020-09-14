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
import naming_mod as names
import get_utils as get


def setup_rail():
    the_model = get.model()
    the_assy = get.assy()
    # Create part and add instance to assembly
    rail_part = the_model.Part(name=names.rail_part, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    rail_inst = the_assy.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    
    # Sketch the rail profile
    rail_sketch = sketch_rail()
    
    # Make the base shell
    rail_part.BaseShell(sketch=rail_sketch)
    rail_sketch.unsetPrimaryObject()
    
    # Partitioning
    partition_sketch = partition_rail()
    rail_part.PartitionFaceBySketch(faces=rail_part.faces.findAt(((0.0, -1.0, 0.0),)), sketch=partition_sketch)
    
    # Assign sections
    define_sections()
    
    # Mesh rail part
    mesh_rail()
    
    # Find and connect node pairs (right and left vertical faces, as well as shadow_pairs)
    lr_pairs = find_rail_node_pairs_left_right()
    shadow_pairs = find_shadow_nodes()
    connect_nodes((lr_pairs, shadow_pairs))
    
    # Define contact surface
    define_contact_surface()
    top_edge = rail_part.edges.findAt(((0., 0., 0.),))
    rail_part.Set(edges=top_edge, name=names.rail_contact_nodes) # Only contact nodes not in shadow set
    
    # Define bottom region (where boundary conditions will be applied)
    bottom_edge = rail_part.edges.findAt(((0., -user_settings.rail_geometry['height'], 0.),))
    bottom_region = rail_part.Set(edges=bottom_edge, name=names.rail_bottom_nodes)

    
def sketch_rail():
    the_model = get.model()
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel()
    
    sketch = the_model.ConstrainedSketch(name='__rail_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    
    dx = user_settings.rail_geometry['length']/2.0
    dy = user_settings.rail_geometry['height']
    dxs = -(dx + shadow_line_length)
    dys = -user_settings.rail_mesh['fine']
    sketch.Line(point1=( dx,  0.), point2=( dx, -dy))
    sketch.Line(point1=( dx, -dy), point2=(-dx, -dy))
    sketch.Line(point1=(-dx, -dy), point2=(-dx, dys))
    sketch.Line(point1=(-dx, dys), point2=(dxs, dys))
    sketch.Line(point1=(dxs, dys), point2=(dxs,  0.))
    sketch.Line(point1=(dxs,  0.), point2=( dx, 0.))
    
    return sketch


def partition_rail():
    the_model = get.model()
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel()
    rail_length = user_settings.rail_geometry['length']
    fine_mesh = user_settings.rail_mesh['fine']
    
    partition_sketch = the_model.ConstrainedSketch(name='__rail_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    partition_sketch.Line(point1=(-rail_length/2.0-shadow_line_length-1., -fine_mesh), 
                          point2=(rail_length/2.0+1., -fine_mesh))
    partition_sketch.Line(point1=(-rail_length/2.0, 0.), point2=(-rail_length/2.0, -fine_mesh))
    
    return partition_sketch
    
    
def mesh_rail():
    rail_part = get.part(names.rail_part)
    rail_length = user_settings.rail_geometry['length']
    rail_height = user_settings.rail_geometry['height']
    fine_mesh = user_settings.rail_mesh['fine']
    coarse_mesh = user_settings.rail_mesh['coarse']
    
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel()
    number_of_top_elements = int(rail_length/fine_mesh)
    
    rail_part.seedEdgeByNumber(edges=rail_part.edges.findAt(((0.0, 0.0, 0.0),)), 
                          number=number_of_top_elements, constraint=FIXED)
    rail_part.seedEdgeByNumber(edges=rail_part.edges.findAt(((-rail_length/2.0-shadow_line_length/2.0, 0.0, 0.0),)), 
                          number=number_of_shadow_elements, constraint=FIXED)
    rail_part.seedEdgeByBias(biasMethod=SINGLE, 
                        end2Edges=rail_part.edges.findAt(((-rail_length/2.0, -rail_height/2.0, 0.0),)),
                        end1Edges=rail_part.edges.findAt(((+rail_length/2.0, -rail_height/2.0, 0.0),)), 
                        minSize=fine_mesh, maxSize=coarse_mesh, constraint=FIXED)  # FIXED ensures compat. meshes
                        
    rail_part.setElementType(regions=rail_part.sets[names.rail_set], elemTypes=(mesh.ElemType(elemCode=CPE4),))
    rail_part.generateMesh()
    
    
def define_sections():
    rail_part = get.part(names.rail_part)
    rail_length = user_settings.rail_geometry['length']
    fine_mesh = user_settings.rail_mesh['fine']
    
    shadow_line_length, number_of_shadow_elements = get_shadow_rail_length_and_nel()
    
    faces = rail_part.faces.findAt(((0., -fine_mesh/2.0, 0.),),((0., -1.5*fine_mesh, 0.),))
    region = rail_part.Set(faces=faces, name=names.rail_set)
    rail_part.SectionAssignment(region=region, sectionName=names.rail_sect, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
        
    shadow_face = rail_part.faces.findAt(((-rail_length/2.0-shadow_line_length/2.0, -fine_mesh/2.0, 0.),))
    shadow_region = rail_part.Set(faces=shadow_face, name='shadow_set')
    rail_part.SectionAssignment(region=shadow_region, sectionName=names.rail_shadow_sect, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    
def get_shadow_rail_length_and_nel():
    rail_length = user_settings.rail_geometry['length']
    fine_mesh = user_settings.rail_mesh['fine']
    max_contact_length = user_settings.rail_geometry['max_contact_length']
    
    number_of_top_elements = int(rail_length/fine_mesh)
    number_of_shadow_elements = int(max_contact_length/fine_mesh)
    shadow_line_length = (rail_length/number_of_top_elements) * number_of_shadow_elements
    return shadow_line_length, number_of_shadow_elements
    
    
def find_rail_node_pairs_left_right():
    rail_part = get.part(names.rail_part)
    rail_length = user_settings.rail_geometry['length']
    rail_height = user_settings.rail_geometry['height']
    fine_mesh = user_settings.rail_mesh['fine']
    
    edges = rail_part.edges.findAt(((-rail_length/2.0, -(rail_height-fine_mesh)/2.0, 0.0),),
                              (( rail_length/2.0, -(rail_height-fine_mesh)/2.0, 0.0),))
    vertices = rail_part.vertices.findAt(((-rail_length/2.0, 0.0, 0.0),),
                                    (( rail_length/2.0, 0.0, 0.0),))
                                    
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


def find_shadow_nodes():
    rail_part = get.part(names.rail_part)
    rail_length = user_settings.rail_geometry['length']
    fine_mesh = user_settings.rail_mesh['fine']
    
    node_connect_tolerance = 1.e-6
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel()
    
    # First identify the two nodes already linked, these should not be included
    vertices = rail_part.vertices.findAt(((-rail_length/2.0, 0.0, 0.0),),
                                    ((-rail_length/2.0, -fine_mesh, 0.0),))
    # No connect nodes
    nc_nodes = [vertices[0].getNodes()[0], vertices[1].getNodes()[0]]
    
    # Find the coordinates of the nodes to connect
    shadow_x_center = -(rail_length+shadow_line_length)/2.0
    shadow_edges = rail_part.edges.findAt(((shadow_x_center, 0.0, 0.0),),
                                     ((shadow_x_center, -fine_mesh, 0.0),))
    true_edges = rail_part.edges.findAt(((0.0, 0.0, 0.0),),
                                   ((0.0, -fine_mesh, 0.0),))
    
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
            dist = (yzcoords[1][:,0]-rail_length-sc[0])**2 + (yzcoords[1][:,1]-sc[1])**2 + (yzcoords[1][:,2]-sc[2])**2
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
    
    
def connect_nodes(node_pairs_lists):
    # Input
    # node_paris_lists      Multiple lists of node pairs (i.e. node_pairs_lists[0] is a list 
    #                       containing node pairs. A node pair is a list of 2 nodes that should be 
    #                       connected
    #
    
    the_model = get.model()
    the_assy = get.assy()
    rail_part = get.part(names.rail_part)
    rail_length = user_settings.rail_geometry['length']
    fine_mesh = user_settings.rail_mesh['fine']

    node_pairs = []
    for node_pairs_list in node_pairs_lists:
        for node_pair in node_pairs_list:
            node_pairs.append(node_pair)
            
    set_nr = 1
    for np in node_pairs:
        set_names = ['NodeConnectSet' + side + '-' + str(set_nr) for side in ['Left', 'Right']]
        node_seq_left = rail_part.nodes.sequenceFromLabels((np[0].label,))
        node_seq_right = rail_part.nodes.sequenceFromLabels((np[1].label,))
        rail_part.Set(nodes=node_seq_left, name=set_names[0])
        rail_part.Set(nodes=node_seq_right, name=set_names[1])
        set_nr = set_nr + 1
    
    the_assy.regenerate()
    for set_nr in range(len(node_pairs)):
        eq_names = ['NodeConnectSet' + side + '-' + str(set_nr+1) for side in ['Left', 'Right']]
        # Link x-degree of freedom
        the_model.Equation(name='NodeConnectConstraintX-'+str(set_nr), terms=((1.0, 
        'RAIL.'+eq_names[0], 1), (-1.0, 'RAIL.'+eq_names[1], 1)))
        # Link y-degree of freedom
        the_model.Equation(name='NodeConnectConstraintY-'+str(set_nr), terms=((1.0, 
        'RAIL.'+eq_names[0], 2), (-1.0, 'RAIL.'+eq_names[1], 2)))
        # For 3D link also z-degree of freedom (not implemented)
        
        
def define_contact_surface():
    the_assy = get.assy()
    rail_inst = get.inst(names.rail_inst)
    rail_length = user_settings.rail_geometry['length']
    (shadow_line_length, number_of_shadow_elements) = get_shadow_rail_length_and_nel()
    rail_contact_surface = the_assy.Surface(side1Edges=rail_inst.edges.findAt(((0.,0.,0.),), 
        (((-rail_length-shadow_line_length)/2.0, 0.0, 0.0),)), 
        name=names.rail_contact_surf)
