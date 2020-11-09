"""This module is used to include a previously created rail part in the 
rollover analysis

.. codeauthor:: Knut Andreas Meyer
"""

from abaqus import mdb
from abaqusConstants import *

from rollover.utils import naming_mod as names
from rollover.three_d.rail import shadow_regions as rail_shadow_regions
from rollover.three_d.rail import constraints as rail_constraints


def from_file(the_model, rail_model_file, shadow_extents):
    """Include a previously created rail part in the given model.
    Shadow regions and constraints are added, and an instance of the 
    rail part is 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param rail_model_file: The path to the model database (.cae file)
                            containing a model: names.rail_model that
                            again contains the part names.rail_part. 
    :type rail_model_file: str
    
    :param shadow_extents: How far to extend the shadow mesh in each 
                           direction. See `extend_lengths` in 
                           :py:func:`rollover.three_d.rail.shadow_regions.create`
    :type shadow_extents: list[ float ] (len=2)
    
    :returns: None
    :rtype: None

    """
    
    get_part_from_file(the_model, rail_model_file)
    
    rail_part = the_model.parts[names.rail_part]
    rail_length = get_rail_z_extent(rail_part)
    
    rail_shadow_regions.create(the_model, shadow_extents)
    
    the_model.rootAssembly.Instance(name=names.rail_inst, part=rail_part, dependent=ON)
    rail_constraints.create(the_model, rail_length)
    
    
def get_rail_z_extent(rail_part):
    """Get the dimension of `rail_part` along the z-direction.
    
    :param the_model: The meshed part 
    :type the_model: Part object (Abaqus)
    
    :returns: Dimension of `rail_part` along the z-direction.
    :rtype: float
    
    """
    
    rail_part_bb = rail_part.nodes.getBoundingBox()
    
    return rail_part_bb['high'][2] - rail_part_bb['low'][2]
    
    
def get_part_from_file(the_model, rail_model_file):
    """Add the rail part from the rail_model_file, along with materials
    and sections, to the_model. 
    
    :param the_model: The full model 
    :type the_model: Model object (Abaqus)
    
    :param rail_model_file: The path to the model database (.cae file)
                            containing a model: names.rail_model that
                            again contains the part names.rail_part. 
    :type rail_model_file: str
    
    :returns: None
    :rtype: None

    """
    
    mdb.openAuxMdb(pathName=rail_model_file)
    mdb.copyAuxMdbModel(fromName=names.rail_model, toName=names.rail_model)
    mdb.closeAuxMdb()
    source_rail_model = mdb.models[names.rail_model]
    the_model.Part(names.rail_part, source_rail_model.parts[names.rail_part])
    the_model.copyMaterials(sourceModel=source_rail_model)
    the_model.copySections(sourceModel=source_rail_model)
    
    del mdb.models[names.rail_model]

