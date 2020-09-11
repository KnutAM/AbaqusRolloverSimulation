
# Overall simulation settings
simulation_name = 'rollover'
substructure_path = ('C:/Users/knutan/Documents/Work/ProjectsWorkFolders/MU34/' + 
                     'Project_2020_C_RolloverSimulation/substructures')
max_contact_length = 16.0
num_cycles = 3

# Numerical "trick" settings
numtrick = {'dummy_stiffness': 1.e-6,   # MPa   (Stiffness for dummy materials extending contact 
                                        #        regions)
            'extrap_roll_length': 1.0,  # mm    (Rolling length for last and first increment for 
                                        #        each cycle. The first increment extrapolates the 
                                        #        last in the previous cycle)
            'move_back_time': 1,
           }

# Rail settings
rail_geometry = {'length': 30.0, 'height': 30.0, 
                 'max_contact_length': max_contact_length}
rail_mesh = {'fine': 2.0, 'coarse': 5.0}

super_element_path = substructure_path + '/super_elements/R200_M02p00_A00p150'

wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 200., 
                  'max_contact_length': max_contact_length, 
                  'rolling_angle': 30./(400./2.)}
wheel_mesh = {'fine': 2.0, 'coarse': 20.0, 'refine_thickness': 10.0}
                
substructure_name = ('substr_' + str(int(wheel_mesh['fine'])).zfill(2) + '_' + 
                     str(int(100*(wheel_mesh['fine']-int(wheel_mesh['fine'])))))

# Material settings
# Only dictionary "materials" required, the remaining are only support variables
elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
plastic_steel = {'material_model': 'chaboche', 'mpar': {'E': 210.e3, 'nu': 0.3, 'Y0': 200., 
                                                        'Hkin': 5.e3, 'binf': 500., 'Hiso': 1.e3, 
                                                        'kinf': 100.}
                }
chaboche_umat = {'material_model': 'user', 
                 'mpar': {'nstatv': 8, 'umat': 'chaboche.obj', 
                 'user_mpar_array': (210.e3, 0.3, 500., 1.e3, 1.e-2, 5.e3, 2.e-4)}
                }
dummy_elastic = {'material_model': 'elastic', 'mpar': {'E': numtrick['dummy_stiffness'], 'nu': 0.3}
                }

materials = {'rail': elastic_steel, 'wheel': elastic_steel, 
             'shadow_rail': dummy_elastic, 
             'contact_trusses_wheel': dummy_elastic}
             
# Time increment settings
time_incr_param = {'nom_num_incr_rolling': 50,      # Nominal number of increments during rolling
                   'max_num_incr_rolling': 200,     # Maximum number of increments during rolling
                  }
             
# Load settings
load_parameters = {'initial_depression': 0.01,      # mm
                   'normal_load': 5000,             # N
                   'slip': 0.02,                    # -
                   'speed': 30,                     # mm/s
                   }

# Contact settings
contact_parameters = {'penalty_stiffness': 1.e6,    # N/mm
                      'friction': 0.2,              # -
                      }
                      
