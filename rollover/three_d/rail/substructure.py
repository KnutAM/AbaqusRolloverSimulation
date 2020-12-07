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

from abaqusConstants import *
from abaqus import mdb, session
import part, mesh, regionToolset

from rollover.utils import naming_mod as names
from rollover.three_d.rail import constraints
from rollover.three_d.utils import mesh_tools


def use_on_current():
    rail_model = mdb.models[session.sessionState[session.currentViewportName]['modelName']]
    create(rail_model, regenerate=False)


def gen_on_current():
    rail_model = mdb.models[session.sessionState[session.currentViewportName]['modelName']]
    create(rail_model, regenerate=True)
    

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
    

    
def remove_substructure_geometry(rail_part):
    substructure_set = rail_part.sets[names.rail_substructure]
    del rail_part.sets[names.rail_bottom_nodes]
    
    int_faces, aux_set_name = create_boundary_face_set(rail_part, substructure_set, 
                                                       names.rail_substructure_interface_set, 
                                                       internal=True)
    
    ext_faces, aux_set_name = create_boundary_face_set(rail_part, substructure_set, 
                                                       'EXT_FACES', internal=False)
    rail_part.RemoveFaces(faceList=ext_faces.faces, deleteCells=True)
    
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
    