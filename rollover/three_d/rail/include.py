"""This module is used to include a previously created rail part in the 
rollover analysis

.. codeauthor:: Knut Andreas Meyer
"""

from abaqus import mdb
from abaqusConstants import *

from rollover.local_paths import data_path
from rollover.utils import naming_mod as names
from rollover.three_d.rail import shadow_regions as rail_shadow_regions
from rollover.three_d.rail import constraints as rail_constraints
from rollover.three_d.rail import substructure as rail_substruct


def from_file(the_model, model_file, shadow_extents, use_rail_rp=False):
    """Include a previously created rail part in the given model.
    Shadow regions and constraints are added, and an instance of the 
    rail part is 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param model_file: The path to the model database (.cae file)
                       containing a model: names.rail_model that again 
                       contains the part names.rail_part. 
    :type model_file: str
    
    :param shadow_extents: How far to extend the shadow mesh in each 
                           direction. See `extend_lengths` in 
                           :py:func:`rollover.three_d.rail.shadow_regions.create`
    :type shadow_extents: list[ float ] (len=2)
    
    :param use_rail_rp: Should a reference point for the rail be used 
                        and included in the constraint equations?
    :type use_rail_rp: bool
    
    :returns: Number of nodes, Number of elements
    :rtype: list[ int ]

    """
    
    has_substruct = get_part_from_file(the_model, model_file)
    
    rail_part = the_model.parts[names.rail_part]
    rail_length = get_rail_z_extent(rail_part)
    
    rail_shadow_regions.create(the_model, shadow_extents)
    num_nodes = len(rail_part.nodes)
    num_elems = len(rail_part.elements)
    if has_substruct:
        substr_part = the_model.parts[names.rail_substructure]
        substr_part.Set(name='RETAINED_NODES', 
                        nodes=substr_part.nodes.sequenceFromLabels(substr_part.retainedNodes))
        ss_inst = the_model.rootAssembly.Instance(name=names.rail_substructure, part=substr_part, 
                                                  dependent=ON)
        num_nodes += len(substr_part.nodes)
        num_elems += len(substr_part.elements)
        
    rail_inst = the_model.rootAssembly.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    num_nodes += len(the_model.rootAssembly.nodes)
    
    rail_constraints.create(the_model, rail_length, use_rail_rp, has_substruct)
    
    if has_substruct:
        # Apply tie between the compatible meshes
        retained=rail_inst.sets[names.rail_substructure_interface_set]
        constrained=ss_inst.sets['RETAINED_NODES']
        the_model.Tie(name='SUBSTRUCTURE_TIE', main=retained, secondary=constrained,
                      positionToleranceMethod=SPECIFIED, positionTolerance=1.e-6,
                      adjust=ON)
    
    return num_nodes, num_elems
    
    
def get_rail_z_extent(rail_part):
    """Get the dimension of `rail_part` along the z-direction.
    
    :param the_model: The meshed part 
    :type the_model: Part object (Abaqus)
    
    :returns: Dimension of `rail_part` along the z-direction.
    :rtype: float
    
    """
    
    rail_part_bb = rail_part.nodes.getBoundingBox()
    
    return rail_part_bb['high'][2] - rail_part_bb['low'][2]
    
    
def get_part_from_file(the_model, model_file):
    """Add the rail part from the rail_model_file, along with materials
    and sections, to the_model. 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param model_file: The path to the model database (.cae file)
                       containing a model: names.rail_model that again 
                       contains the part names.rail_part. 
    :type model_file: str
    
    :returns: None
    :rtype: None

    """
    if model_file.startswith(':/'):
        model_file = data_path + model_file[1:]
    mdb.openAuxMdb(pathName=model_file)
    mdb.copyAuxMdbModel(fromName=names.rail_model, toName=names.rail_model)
    mdb.closeAuxMdb()
    source_rail_model = mdb.models[names.rail_model]
    the_model.Part(names.rail_part, source_rail_model.parts[names.rail_part])
    the_model.copyMaterials(sourceModel=source_rail_model)
    the_model.copySections(sourceModel=source_rail_model)
    
    has_substruct = names.rail_substructure in source_rail_model.parts.keys()
    if has_substruct:
        the_model.Part(names.rail_substructure, source_rail_model.parts[names.rail_substructure])
    
    del mdb.models[names.rail_model]

    return has_substruct