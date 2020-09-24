# Overall simulation settings
max_contact_length = 16.0
num_cycles = 3
use_restart = False
usub_object_path = None
run_simulation = False

# Numerical "trick" settings
numtrick = {'dummy_stiffness': 1.e-6,   # MPa   (Stiffness for dummy materials extending contact 
                                        #        regions)
            'move_back_time': 1.e-6,
           }

# Rail settings
rail_geometry = {'length': 30.0, 'height': 30.0, 'max_contact_length': max_contact_length}
rail_mesh = {'fine': 2.0, 'coarse': 5.0}

# Wheel settings: Give name of folder in 'super_wheels' from which to take user wheel element
super_wheel = 'OD400_ID200_M04p000'
custom_super_wheel_directory = None     # Specify to use another directory than src/../super_wheels


# Time increment settings
time_incr_param = {'nom_num_incr_rolling': 50,      # Nominal number of increments during rolling
                   'max_num_incr_rolling': 200,     # Maximum number of increments during rolling
                  }
             
# Load settings
load_parameters = {'initial_depression': 0.01,      # mm
                   'normal_load': 5000,             # N
                   'slip': 0.02,                    # -
                   'speed': 30e3,                   # mm/s
                   }

# Contact settings
contact_parameters = {'penalty_stiffness': 1.e6,    # N/mm
                      'friction': 0.2,              # -
                      }

# Material settings
material_model_folder = None
#material_model_folder = 'C:/Users/knutan/Documents/Work/MySoftwares/MaterialModels/compiled_abaqus'
# Only dictionary "materials" required, the remaining are only support variables to facilitate
# creating the "materials" dictionary

elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
plastic_steel = {'material_model': 'chaboche', 'mpar': {'E': 210.e3, 'nu': 0.3, 'Y0': 200., 
                                                        'Hkin': 5.e3, 'binf': 500., 'Hiso': 1.e3, 
                                                        'kinf': 100.}
                }

chaboche_umat = {'material_model': 'user', 
                 'mpar': {'nstatv': 8, 
                          'src_folder': 'chaboche',
                          'user_mpar_array': (210.e3, 0.3, 500., 1.e3, 1.e-2, 5.e3, 2.e-4)
                          }
                }
                
dummy_elastic = {'material_model': 'elastic', 'mpar': {'E': numtrick['dummy_stiffness'], 'nu': 0.3}
                }

materials = {'rail': elastic_steel, 'wheel': elastic_steel, 
             'shadow_rail': dummy_elastic, 
             'contact_trusses_wheel': dummy_elastic}
