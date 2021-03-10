""" Define names to be used throughout the code. All names that are 
    referenced within multiple functions should be defined in this 
    module. Recommended to import as "import naming_mod as names"
    Hence, the variables will not contain name, and will be written as 
    e.g. names.step0
"""

# Model, job and odb naming
model = 'rollover'
rail_model = 'RAIL'
job = model
rail_sub_job = 'RAIL_SUBSTRUCTURE'
rail_sub_id = 2

# Part, instance and section names
wheel_part = 'WHEEL'
rail_part = 'RAIL'
wheel_inst = wheel_part
rail_inst = rail_part
rail_sect = rail_part
rail_shadow_sect = 'SHADOW_RAIL'
wheel_dummy_contact_sect = 'WHEEL_DUMMY_CONTACT'

# Sets
wheel_contact_surf = 'WHEEL_CONTACT_SURFACE'
wheel_rp_set = 'WHEEL_RP'
wheel_inner_set = 'WHEEL_SHAFT'
wheel_sym_set = 'SYMMETRY'
wheel_contact_nodes = 'CONTACT_NODES'

rail_rp_set = 'RAIL_RP'
rail_contact_nodes = 'CONTACT_NODES'
rail_shadow_surf = 'RAIL_SHADOW_SURF'
# Contact surf excluding shadow regions:
rail_contact_surf = 'RAIL_CONTACT_SURFACE'
# Contact surf including shadow regions:
rail_full_contact_surf = 'RAIL_FULL_CONTACT_SURFACE'
rail_bottom_nodes = 'BOTTOM_NODES'
rail_sym_set = 'SYMMETRY'
rail_set = 'RAIL_SET'
rail_side_sets = ['SIDE1_SET', 'SIDE2_SET']
rail_shadow_set = 'SHADOW_RAIL'
rail_shadow_sets = [rail_shadow_set + s for s in ['L', 'R', 'M']]
rail_substructure = 'RAIL_SUBSTRUCTURE'
rail_substructure_interface_set = 'RAIL_SUBSTR_INTERFACE'

# BC and interactions
rail_rp_bc = 'RAIL_RP'
rail_bottom_bc = 'FIX_BOTTOM'
rail_sym_bc = 'RAIL_SYM_BC'

wheel_rp_bc = 'WHEEL_CTRL'
wheel_vert_load = 'WHEEL_VLOAD'
wheel_sym_bc = 'WHEEL_SYM_BC'

# Step naming
# Formatting of names
def cycle_str(cycle_nr):
    """ Get string format for cycle number, use to get consistency 
    with how many zeros are padded. 
    :param cycle_nr: The cycle number
    :type cycle_nr: int
    
    :returns: String with the cycle number
    :rtype: str
    """
    return str(cycle_nr).zfill(5)
    
    
step0 = 'Initial'   # Abaqus default
step1 = 'Preload'   # Apply fixed displacement
step2 = 'Loading'   # Apply the contact normal load


def get_step_rolling(cycle_nr=1):
    """ Get the step name for rolling step in cycle cycle_nr
    :param cycle_nr: The cycle number
    :type cycle_nr: int
    
    :returns: The step name
    :rtype: str
    """
    
    return 'rolling_' + cycle_str(cycle_nr)


def get_step_return(cycle_nr=2):
    """ Get the step name for return step in cycle cycle_nr
    :param cycle_nr: The cycle number
    :type cycle_nr: int
    
    :returns: The step name
    :rtype: str
    """
    return 'return_' + cycle_str(cycle_nr)


def get_step_reapply(cycle_nr=2):
    """ Get the step name for reapply step in cycle cycle_nr
    :param cycle_nr: The cycle number
    :type cycle_nr: int
    
    :returns: The step name
    :rtype: str
    """
    return 'reapply_' + cycle_str(cycle_nr)


def get_step_release(cycle_nr=2):
    """ Get the step name for release step in cycle cycle_nr
    :param cycle_nr: The cycle number
    :type cycle_nr: int
    
    :returns: The step name
    :rtype: str
    """
    return 'release_' + cycle_str(cycle_nr)


# File names
## Rolover files
rollover_settings_file = 'rollover_settings.json'
loading_file = 'load_param.txt'
rp_coord_file = 'rp_coord.txt'

## Rail files
rail_settings_file = 'rail_settings.json'

## Wheel files
wheel_settings_file = 'wheel_settings.json'

substr_node_coords_file = 'contact_node_coords.npy'
substr_node_labels_file = 'contact_node_labels.npy'
substr_mtx_file = 'ke.mtx'

uel_stiffness_file = 'uel_stiffness.txt'
uel_coordinates_file = 'uel_coordinates.npy'
uel_elements_file = 'uel_elements.npy'

## Rail substructure
substructure_interface_mesh_file = 'interface_mesh.json'