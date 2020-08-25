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
    

# Step naming
step0 = 'Initial'   # Abaqus default
step1 = 'Preload'   # Apply fixed displacement
step2 = 'Loading'   # Apply the contact normal load

def get_step_rolling(cycle_nr):
    return 'rolling_' + cycle_str(cycle_nr)
    
def get_step_return(cycle_nr):
    return 'return_' + cycle_str(cycle_nr)
    

# BC and interactions
def get_contact(cycle_nr):
    return 'Contact_' + cycle_str(cycle_nr)
    
def get_lock_rail_bc(cycle_nr):
    return 'lock_rail_' + cycle_str(cycle_nr)