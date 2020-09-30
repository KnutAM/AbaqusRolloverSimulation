# Overall simulation settings
max_contact_length = 25.0
num_cycles = 3
run_simulation = True
use_restart = False
usub_object_path = None     # 'C:/Work/Abaqus/2017/usub-std.obj'

# Numerical "trick" settings
numtrick = {'dummy_stiffness': 1.e-6,   # MPa   (Stiffness for dummy materials extending contact 
                                        #        regions)
            'move_back_time': 1.e-6,
           }

# Rail settings
rail_geometry = {'length': 50.0, 'height': 80.0, 'dummy_length': max_contact_length}
rail_mesh = {'fine': 2.0, 'coarse': 10.0}

# Wheel settings: Give name of folder in 'super_wheels' from which to take user wheel element
super_wheel = 'OD666_ID200_RL60_M02p000'
custom_super_wheel_directory = None     # Specify to use another directory than src/../super_wheels

# Field_outputs (assumes rail instance except for special keywords: FULL_MODEL, WHEEL_RP)
# Provide a dict containing the name of the field outputs as keys. Each item should be a dict with 
# the following keys:
# set   Name of rail instance set from which the variables should be saved. Note special names
#       FULL_MODEL and WHEEL_RP that are not rail exclusive, but rather self explanatory
# var   Give a tuple of Abaqus output variables, e.g. ('LE', 'U', 'S')
# freq  Output frequency. Set to -1 to have LAST_INCREMENT option invoked
# cycle How often (in terms of cycles) the output should be active. If 1, then each cycle will be 
#       saved. Otherwise, the name will be suffixed by the cycle number and one output per outputted
#       cycle will be created. 
field_outputs = {'full_field': {'set': 'FULL_MODEL',
                                'var': ('LE', 'U', 'S'),
                                'freq': 1,
                                'cycle': 10},
                'wheel_rp': {'set': 'WHEEL_RP',
                             'var': ('RM', 'U', 'UR'),
                             'freq': 1,
                             'cycle': 1},
                'contact_surf': {'set': 'CONTACT_NODES',
                                 'var': ('LE', 'U', 'S'),
                                 'freq': 1,
                                 'cycle': 1}
                }   

# Time increment settings
time_incr_param = {'nom_num_incr_rolling': 200,     # Nominal number of increments during rolling
                   'max_num_incr_rolling': 1000,    # Maximum number of increments during rolling
                  }
time_incr_param['nom_num_incr_rolling'] = 10*int(rail_geometry['length']/rail_mesh['fine'])
time_incr_param['max_num_incr_rolling'] = 100*time_incr_param['nom_num_incr_rolling']
             
# Load settings
load_parameters = {'initial_depression': 0.01,      # mm
                   'normal_load': 18.2e3,           # N/mm
                   'slip': 0.015,                   # -
                   'speed': 30e3,                   # mm/s
                   }

# Contact settings
contact_parameters = {'penalty_stiffness': 1.e6,    # N/mm
                      'friction': 0.5,              # -
                      }

# Material settings
material_model_folder = None
#material_model_folder = 'C:/Users/knutan/Documents/Work/MySoftwares/MaterialModels/compiled_abaqus'
# Only dictionary "materials" required, the remaining are only support variables to facilitate
# creating the "materials" dictionary

elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
plastic_steel = {'material_model': 'chaboche', 'mpar': {'E': 210.e3, 'nu': 0.3, 'Y0': 500., 
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

materials = {'rail': plastic_steel, 'wheel': elastic_steel, 
             'shadow_rail': dummy_elastic, 
             'contact_trusses_wheel': dummy_elastic}
