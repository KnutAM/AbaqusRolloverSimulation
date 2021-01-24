""" Functions to be called from plugins

"""

from abaqus import *


from rollover.utils import naming_mod as names
from rollover.three_d.rail import basic as rail_basic
from rollover.three_d.rail import mesher as rail_mesh
from rollover.three_d.utils import symmetric_mesh_module as sm



def create_rail(profile, name, length, mesh_size, 
                r_x_min, r_y_min, r_x_max, r_y_max, r_x, r_y, sym_sign=0):
    """Create a rail model from plugin input
    
    :param profile: Path to an Abaqus sketch profile saved as .sat file 
                    (acis)
    :type profile: str
    
    :param name: Name of file to save rail as
    :type name: str
    
    :param length: Length of rail to be extruded
    :type length: float
    
    :param mesh_size: Mesh size to be used
    :type mesh_size: float
    
    :param r_x_min: x-coordinate of refinement cell corner nr 1. The 
                    refinement cell also specifies the contact region
    :type r_x_min: float
    
    :param r_y_min: y-coordinate of refinement cell corner nr 1
    :type r_y_min: float
    
    :param r_x_max: x-coordinate of refinement cell corner nr 2
    :type r_x_max: float
    
    :param r_y_max: y-coordinate of refinement cell corner nr 2
    :type r_y_max: float
    
    :param r_x: x-coordinate of point within refinement cell
    :type r_x: float
    
    :param r_y: y-coordinate of point within refinement cell
    :type r_y: float
    
    :param sym_sign: Direction of symmetry normal (along x-axis), if 0
                     no symmetry is applied.
    :type sym_sign: int
    
    """
    
    refinement_cell = [[r_x_min, r_y_min], [r_x_max, r_y_max]]
    point_in_refine_cell = [r_x, r_y, length/2.0]
    sym_dir = None if sym_sign == 0 else [sym_sign, 0, 0]
    rail_model = rail_basic.create(profile, length, 
                                   refine_region=refinement_cell, 
                                   sym_dir=sym_dir)
    rail_part = rail_model.parts[names.rail_part]
    rail_mesh.create_basic(rail_part, point_in_refine_cell, 
                           fine_mesh=mesh_size, coarse_mesh=mesh_size)

    mdb.saveAs(pathName=name)
    
    
def periodicize_mesh():
    """ Attempt to make the mesh periodic between the sides.
    """
    the_model = mdb.models[names.rail_model]
    rail_part = the_model.parts[names.rail_part]
    
    sm.make_periodic_meshes(rail_part, 
                            source_sets=[rail_part.sets[names.rail_side_sets[0]]], 
                            target_sets=[rail_part.sets[names.rail_side_sets[1]]])
    
    rail_part.generateMesh()