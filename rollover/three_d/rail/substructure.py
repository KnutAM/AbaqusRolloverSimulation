"""This module is used to generate a substructure the cell in the rail
part named names.rail_substructure.

Steps:

*  Get key dimensions/information for current rail part
*  Export substructure mesh
*  Generate the substructure
*  Import the substructure back into assembly
*  Turn remaining mesh into orphan mesh. Redefine sets/surfaces.

.. codeauthor:: Knut Andreas Meyer
"""
from __future__ import print_function
import numpy as np

from abaqusConstants import *
from abaqus import mdb, session
import part, mesh, regionToolset

from rollover.utils import naming_mod as names
from rollover.utils import json_io
from rollover.three_d.rail import constraints
from rollover.three_d.utils import mesh_tools


def use_from_plugin():
    rail_model = mdb.models[names.rail_model]
    create(rail_model, regenerate=False)


def gen_from_plugin():
    rail_model = mdb.models[names.rail_model]
    create(rail_model, regenerate=True)


def add_interface_pattern_plugin():
    rail_model = mdb.models[names.rail_model]
    rail_part = rail_model.parts[names.rail_part]
    rail_part.deleteNode(nodes=rail_part.nodes)
    add_interface_mesh(rail_part)
    

def create(rail_model, regenerate=True):
    # Get key dimensions/information for current rail part
    rail_part = rail_model.parts[names.rail_part]
    rail_info = get_info(rail_part)
    
    if regenerate:
        generate(rail_model, rail_info)
    
    use_substructure(rail_model, sub_str_job=names.rail_sub_job, sub_str_id=names.rail_sub_id)
    
    
def use_substructure(rail_model, sub_str_job, sub_str_id):
    # Import substructure
    rail_model.PartFromSubstructure(name=names.rail_substructure, 
                                    substructureFile=sub_str_job + '_Z' + str(sub_str_id) + '.sim',
                                    odbFile=sub_str_job + '.odb')
    rail_part = rail_model.parts[names.rail_part]
    remove_substructure_geometry(rail_part)
    
    add_interface_mesh(rail_part)

    
def remove_substructure_geometry(rail_part):
    substructure_set = rail_part.sets[names.rail_substructure]
    del rail_part.sets[names.rail_bottom_nodes]
    
    int_faces, aux_set_name = create_boundary_face_set(rail_part, substructure_set, 
                                                       names.rail_substructure_interface_set, 
                                                       internal=True)
    
    ext_faces, aux_set_name = create_boundary_face_set(rail_part, substructure_set, 
                                                       'EXT_FACES', internal=False)
    rail_part.RemoveFaces(faceList=ext_faces.faces, deleteCells=False)
    
    aux_set_name['ext_faces'] = 'EXT_FACES'
    for key in aux_set_name:
        del rail_part.sets[aux_set_name[key]]
    
    
def get_info(rail_part):
    
    # Put bounding box with xMin, xMax, yMin, ... format in rail_info:
    rail_info = mesh_tools.convert_bounding_box(rail_part.nodes.getBoundingBox())
    
    rail_info['z_side1'] = rail_part.sets[names.rail_side_sets[0]].nodes[0].coordinates[2]
    rail_info['z_side2'] = rail_part.sets[names.rail_side_sets[1]].nodes[0].coordinates[2]
    rail_info['length'] = rail_info['zMax'] - rail_info['zMin']
    
    return rail_info

    
def generate(rail_model, rail_info):
    substructure_model = mdb.Model(name='RAIL_SUBSTRUCTURE', objectToCopy=rail_model)
    
    rail_part = substructure_model.parts[names.rail_part]
    
    substr_cell_set_name, interface_set_name, retain_cell_set_name = setup_sets(rail_part)
    
    interface_node_coords = [n.coordinates for n in rail_part.sets[interface_set_name].nodes]
    
    save_interface_mesh(rail_part, interface_set_name)
    
    make_orphan_mesh(rail_part, rail_part.sets[retain_cell_set_name])
    
    redefine_sets(rail_part, rail_info, interface_node_coords)
    
    setup_elastic_section(substructure_model, rail_part, Emod=210.e3, nu=0.3)
    
    assy = substructure_model.rootAssembly
    rail_inst = assy.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    
    substructure_model.SubstructureGenerateStep(name='Step-1', previous='Initial', 
                                                substructureIdentifier=names.rail_sub_id, 
                                                recoveryMatrix=NONE)
    
    # Setup constraints
    sc_sets, sr_sets = constraints.create_sets(rail_part, *names.rail_side_sets)
    for c_set, r_set in zip(sc_sets, sr_sets):
        constraints.add(substructure_model, rail_info['length'], c_set, r_set_name=r_set)
    
    # Setup boundary conditions
    substructure_model.DisplacementBC(name=names.rail_bottom_bc, createStepName='Step-1', 
                                      region=rail_inst.sets[names.rail_bottom_nodes], 
                                      u1=0.0, u2=0.0, u3=0.0)
    
    substructure_model.RetainedNodalDofsBC(name='RETAINED_NODES', createStepName='Step-1', 
                                      region=rail_inst.sets[names.rail_substructure_interface_set], 
                                      u1=ON, u2=ON, u3=ON, ur1=OFF, ur2=OFF, ur3=OFF)
                                      
    # Run job
    substr_job = mdb.Job(name=names.rail_sub_job, model=substructure_model.name)
    substr_job.submit()
    substr_job.waitForCompletion()
    
    
def make_interface_orphan_surface_mesh(rail_model):
    rail_part = rail_model.parts[names.rail_part]
    
    old_set_name, interface_set_name, tmp2_set_name = setup_sets(rail_part)
    del rail_part.sets[tmp2_set_name]
        
    for face in rail_part.sets[interface_set_name].faces:
        region = mesh_tools.get_source_region(face)
        mesh_tools.create_offset_mesh(rail_part, face, region, offset_distance=0.0)
        
    
def redefine_sets(rail_part, rail_info, interface_node_coords):
    
    POS_TOL = 1.e-6
    
    def flat_face_set(axis, pos, name):
        kwargs = {axis + 'Min': pos-POS_TOL, axis + 'Max': pos+POS_TOL}
        nodes = rail_part.nodes.getByBoundingBox(**kwargs)
        set = rail_part.Set(name=name, nodes=nodes)
        
    bottom_node_set = flat_face_set('y', rail_info['yMin'], names.rail_bottom_nodes)
    side1_set = flat_face_set('z', rail_info['z_side1'], names.rail_side_sets[0])
    side2_set = flat_face_set('z', rail_info['z_side2'], names.rail_side_sets[1])
    
    interface_nodes = []
    for coord in interface_node_coords:
        # Check that node is not on side1 (this will be removed by 
        # constraints and should not be retained)
        if abs(coord[2]-rail_info['z_side1']) > POS_TOL :
            # If ok, find and add node
            kwargs = {axis + side: pos + d*POS_TOL 
                      for axis, pos in zip(['x', 'y', 'z'], coord)
                      for side, d in zip(['Min', 'Max'], [-1, 1])}
            interface_nodes.append(rail_part.nodes.getByBoundingBox(**kwargs)[0])
        
    rail_part.Set(name=names.rail_substructure_interface_set,
                  nodes=mesh.MeshNodeArray(nodes=interface_nodes))
    
    
def setup_sets(rail_part):

    # Set containing the cells to be condensed away
    substructure_set = rail_part.sets[names.rail_substructure]
    
    # Set containing the interface faces between substructure and plastic model
    interface_set_name = 'INTERFACE'
    interface_set, aux_set_name = create_boundary_face_set(rail_part, substructure_set, 
                                                           interface_set_name, internal=True)
    retain_cell_set = rail_part.sets[aux_set_name['other_cell']]
    
    for name in aux_set_name:
        if name not in ['other_cell']:
            del rail_part.sets[aux_set_name[name]]
    
    return names.rail_substructure, interface_set_name, aux_set_name['other_cell']


def create_boundary_face_set(the_part, cell_set, face_set_name, internal=True):
    
    set_name = {'full_cell': 'ALL_CELLS_SET',
                'other_cell': 'OTHER_CELLS_SET',
                'other_face': 'OTHER_FACES_SET',
                'the_face': 'THE_FACES_SET'}
    
    full_cell_set = the_part.Set(name=set_name['full_cell'], cells=the_part.cells)
                                  
    other_cell_set = the_part.SetByBoolean(name=set_name['other_cell'], 
                                            sets=(full_cell_set, cell_set), operation=DIFFERENCE)
                                            
    # Create face sets for each cell set
    the_face_set = make_face_set_from_cell_set(the_part, cell_set, set_name['the_face'])
    other_face_set = make_face_set_from_cell_set(the_part, other_cell_set, set_name['other_face'])
    
    # Create internal/external boundary face set
    op = INTERSECTION if internal else DIFFERENCE
    face_set = the_part.SetByBoolean(name=face_set_name, sets=(the_face_set, other_face_set),
                                     operation=op)
    
    return face_set, set_name

    
def make_face_set_from_cell_set(the_part, the_cell_set, face_set_name):
    faces = []
    for c in the_cell_set.cells:
        for f_ind in c.getFaces():
            faces.append(the_part.faces[f_ind])
            
    return the_part.Set(name=face_set_name, faces=part.FaceArray(faces=faces))
    
    
def make_orphan_mesh(the_part, delete_mesh_cell_set):
    """
    
    """
    
    the_part.deleteMesh(regions=delete_mesh_cell_set.cells)
    ents = regionToolset.Region(vertices=the_part.vertices,
                                edges=the_part.edges,
                                faces=the_part.faces,
                                cells=the_part.cells)
    
    the_part.deleteMeshAssociationWithGeometry(geometricEntities=ents,
                                               addBoundingEntities=True)
    
    for key in the_part.features.keys():
        the_part.features[key].suppress()
    
    
def setup_elastic_section(the_model, the_part, Emod=210.e3, nu=0.3):
    material = the_model.Material(name='Elastic')
    material.Elastic(table=((Emod, nu), ))
    
    the_model.HomogeneousSolidSection(name='Elastic', material='Elastic', thickness=None)
    region = regionToolset.Region(elements=the_part.elements)
    the_part.SectionAssignment(region=region, sectionName='Elastic')
    
    
def save_interface_mesh(the_part, set_name):
    face_vertex_coord = []
    face_elements = []
    node_coord = []
    node_dict = {}
    orphan_nodes = []
    for face in the_part.sets[set_name].faces:
        region = mesh_tools.get_source_region(face)
        elems, offset_vec = mesh_tools.create_offset_mesh(the_part, face, region, 
                                                          offset_distance=0.0)
        face_vertex_coord.append([the_part.vertices[i].pointOn[0] for i in face.getVertices()])
        new_elems = []
        for elem in elems:
            new_elems.append({'connectivity': [], 'type': str(elem.type)})
            for old_ind in elem.connectivity:
                if old_ind not in node_dict:
                    # Check if we have an equal node with the same coordinates
                    new_ind = find_node_by_coord(coord=the_part.nodes[old_ind].coordinates,
                                                 nodes=orphan_nodes)
                    if new_ind is None:                    
                        new_ind = len(node_coord)
                        node_dict[old_ind] = new_ind
                        node_coord.append(the_part.nodes[old_ind].coordinates)
                        orphan_nodes.append(the_part.nodes[old_ind])
                else:
                    new_ind = node_dict[old_ind]
                    
                new_elems[-1]['connectivity'].append(new_ind)
                
        face_elements.append(new_elems[:])
    
    interface_mesh = {'face_vertex_coord': face_vertex_coord,
                      'face_elements': face_elements,
                      'node_coord': node_coord}
    
    json_io.save(names.substructure_interface_mesh_file, interface_mesh)
    
    the_part.deleteNode(nodes=orphan_nodes)
    

def add_interface_mesh(rail_part):
    try:
        interface_mesh = json_io.read(names.substructure_interface_mesh_file)
    except IOError as e:
        print('Could not find/read the interface, IOError was:')
        print(e)
        print('Either fix this, or manually ensure matching meshes')
        return
    etype_2_shape = {'M3D3': TRI3, 'M3D4': QUAD4, 'M3D6': TRI6, 'M3D8': QUAD8, 'M3D8R': QUAD8,
                     'STRI3': TRI3, 'S3': TRI3, 'S3R': TRI3, 'S3RS': TRI3, 'STRI65': TRI6,
                     'S4': QUAD4, 'S4R': QUAD4, 'S4RS': QUAD4, 'S4RSW': QUAD4, 'S4R5': QUAD4,
                     'S8': QUAD8, 'S8R': QUAD8, 'S8R5': QUAD8}
                     
    orph_nodes = mesh.MeshNodeArray(nodes=[rail_part.Node(coord) 
                                           for coord in interface_mesh['node_coord']])
    orph_elements = []
    for face_elements in interface_mesh['face_elements']:
        orph_elements.append([])
        for element in face_elements:
            elnodes = [orph_nodes[i] for i in element['connectivity']]
            elem_shape = etype_2_shape[element['type']]
            try:
                orph_elements[-1].append(rail_part.Element(nodes=elnodes, elemShape=elem_shape))
            except Exception as e:
                print(element['type'])
                raise e
    
    for face in rail_part.sets[names.rail_substructure_interface_set].faces:
        if_face_ind = find_matching_face(rail_part, face, interface_mesh['face_vertex_coord'])
        face_points = [rail_part.vertices[vi].pointOn[0] for vi in face.getVertices()]
        if len(face_points) < 3:
            print('Interface faces must have at least 3 vertices for automatic matching mesh '
                  + 'to be created. Please manually ensure matching mesh.')
            return
        face_points = face_points[:3]
        
        add_elems = mesh.MeshElementArray(elements=orph_elements[if_face_ind])
        add_region = regionToolset.Region(elements=add_elems)
        rail_part.Set(name='face' + str(if_face_ind), elements=add_elems)
        point_nodes = get_matching_nodes(rail_part, face_points, add_region)
        rail_part.copyMeshPattern(elemFaces=add_region, targetFace=face, 
                                  nodes=point_nodes, coordinates=face_points)
    
    
    geom_set = rail_part.Set(name='_TMP_all_cells', 
                             cells=rail_part.cells, faces=rail_part.faces)
    assoc_set = rail_part.Set(name='_TMP_all_assoc', nodes=geom_set.nodes)
    all_set = rail_part.Set(name='_TMP_all_nodes', nodes=rail_part.nodes)
    rem_set = rail_part.SetByBoolean(name='_TMP_rem_nodes', sets=(all_set, assoc_set),
                                     operation=DIFFERENCE)
    rail_part.deleteNode(nodes=rem_set.nodes)
    for set_name in ['_TMP_all_cells', '_TMP_all_assoc', '_TMP_all_nodes', '_TMP_rem_nodes']:
        del rail_part.sets[set_name]

    
    
def find_matching_face(the_part, base_face, faces_vert_coord):
    tol = 1.e-6
    base_vert_coords = [np.array(the_part.vertices[i].pointOn[0]) 
                        for i in base_face.getVertices()]
    
    for face_ind, vert_coords in enumerate(faces_vert_coord):
        dist = []
        for base_coord in base_vert_coords:
            all_dist = []
            for coord in vert_coords:
                all_dist.append(np.linalg.norm(base_coord - np.array(coord)))
            dist.append(min(all_dist))
        dist = np.array(dist)
        if all(dist<tol):
            return face_ind
    
    print('Attempted to find match to face with vertices')
    print(base_vert_coords)
    print('Among the following faces with vertex coords')
    for i, vc in enumerate(faces_vert_coord):
        print('Face ' + str(i+1))
        print(vc)
        
    raise ValueError('Could not find match face with ')
        
        
def get_matching_nodes(the_part, face_points, element_region):
    tol = 1.e-4
    point_nodes = []
    for i, face_point in enumerate(face_points):
        found = False
        for element in element_region.elements:
            for node in element.getNodes():                    
                if np.linalg.norm(np.array(face_point) - np.array(node.coordinates)) < tol:
                    point_nodes.append(node)
                    found = True
                    break
            if found:
                break
                
        
    if len(point_nodes) != len(face_points):
        print('Searching for nodes at points:')
        print(face_points)
        print('But found only ' + str(len(point_nodes)) + ' matches')
        raise ValueError('Could not find matching nodes')
        
    return point_nodes
    
    
def find_node_by_coord(coord, nodes):
    tol = 1.e-6
    
    coord = np.array(coord)
    for i, node in enumerate(nodes):
        if np.linalg.norm(coord - np.array(node.coordinates)) < tol:
            return i
        
    # Could not find a matching node, return None
    return None
    

