# Define names to be used throughout the code. All names that are referenced 
# within multiple functions should be defined in this module.
# Recommended to import as import naming_mod as names
# Hence, the variables will not contain name, and will be written as e.g. 
# names.step0

# Formatting of names
def cycle_str(cycle_nr):    # Format cycle nr
    return str(cycle_nr).zfill(5)

# Model, job and odb naming
def get_model(cycle_nr):
    return 'rollover_' + cycle_str(cycle_nr)

def get_job(cycle_nr):
    return get_model(cycle_nr)      # job and model name can be different, but no reason for that

def get_odb(cycle_nr):
    return get_job(cycle_nr)   # odb and job name should always be the same
    
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
wheel_rp_set = 'RP'
wheel_contact_nodes = 'CONTACT_NODES'
rail_contact_nodes = 'CONTACT_NODES'
rail_bottom_nodes = 'BOTTOM_NODES'

# Step naming
step0 = 'Initial'   # Abaqus default
step1 = 'Preload'   # Apply fixed displacement
step2 = 'Loading'   # Apply the contact normal load

def get_step_roll_start(cycle_nr):
    return 'rolling_start_' + cycle_str(cycle_nr)
    

def get_step_rolling(cycle_nr):
    return 'rolling_' + cycle_str(cycle_nr)
    

def get_step_roll_end(cycle_nr):
    return 'rolling_end_' + cycle_str(cycle_nr)
    
    
def get_step_return(cycle_nr):
    return 'return_' + cycle_str(cycle_nr)
    

# BC and interactions
fix_rail_bc = 'FIX_BOTTOM'
rp_ctrl_bc = 'RP_CTRL'
rp_vert_load = 'RP_LOAD'
def get_contact(cycle_nr):
    return 'Contact_' + cycle_str(cycle_nr)
    
def get_lock_rail_bc(cycle_nr):
    return 'lock_rail_' + cycle_str(cycle_nr)