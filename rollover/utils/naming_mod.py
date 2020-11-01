# Define names to be used throughout the code. All names that are referenced 
# within multiple functions should be defined in this module.
# Recommended to import as "import naming_mod as names"
# Hence, the variables will not contain name, and will be written as e.g. 
# names.step0

# Model, job and odb naming
model = 'rollover'
job = model

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
rail_rp_set = 'RAIL_RP'
wheel_contact_nodes = 'CONTACT_NODES'
rail_contact_nodes = 'CONTACT_NODES'
rail_contact_surf = 'RAIL_CONTACT_SURFACE'
rail_bottom_nodes = 'BOTTOM_NODES'
rail_set = 'RAIL_SET'
rail_side_sets = ['SIDE1_SET', 'SIDE2_SET']
rail_shadow_set = 'SHADOW_RAIL'
rail_shadow_sets = [rail_shadow_set + s for s in ['1', '2']]

# BC and interactions
fix_rail_bc = 'FIX_BOTTOM'
wheel_ctrl_bc = 'WHEEL_CTRL'
wheel_vert_load = 'WHEEL_VLOAD'
contact = 'CONTACT'

# Step naming
# Formatting of names
def cycle_str(cycle_nr):    # Format cycle nr
    return str(cycle_nr).zfill(5)
    
step0 = 'Initial'   # Abaqus default
step1 = 'Preload'   # Apply fixed displacement
step2 = 'Loading'   # Apply the contact normal load

def get_step_rolling(cycle_nr=1):
    return 'rolling_' + cycle_str(cycle_nr)
    
def get_step_return(cycle_nr=2):
    return 'return_' + cycle_str(cycle_nr)
    
def get_step_reapply(cycle_nr=2):
    return 'reapply_' + cycle_str(cycle_nr)
    
def get_step_release(cycle_nr=2):
    return 'release_' + cycle_str(cycle_nr)
    
    
# File names
## Wheel files
wheel_settings_file = 'wheel_settings.json'

substr_node_coords_file = 'contact_node_coords.npy'
substr_node_labels_file = 'contact_node_labels.npy'
substr_mtx_file = 'ke.mtx'

uel_stiffness_file = 'uel_stiffness.txt'
uel_coordinates_file = 'uel_coordinates.npy'
uel_elements_file = 'uel_elements.npy'
