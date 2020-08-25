
# Overall simulation settings
simulation_name = 'rollover'
substructure_path = ('C:/Users/knutan/Documents/Work/ProjectsWorkFolders/MU34/Project_2020_C_RolloverSimulation/substructures')
max_contact_length = 16.0

# Rail settings
rail_geometry = {'length': 30.0, 'height': 30.0, 
                 'max_contact_length': max_contact_length}
rail_mesh = {'fine': 0.5, 'coarse': 5.0}
rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 
               'shadow_section': 'RAIL_SHADOW_SECTION'}

# Wheel settings
use_substructure = True
new_substructure = False

wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 
                  'max_contact_length': max_contact_length, 
                  'rolling_angle': 30./(400./2.)}
wheel_mesh = {'fine': 0.5, 'coarse': 20.0, 'refine_thickness': 10.0}
wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 
                'rp': 'WHEEL_CENTER', 'contact_part': 'WHEEL_CONTACT', 
                'contact_section': 'WHEEL_CONTACT_SECTION'}
                
substructure_name = ('substr_' + str(int(wheel_mesh['fine'])).zfill(2) + '_' + 
                     str(int(100*(wheel_mesh['fine']-int(wheel_mesh['fine'])))))

# Material settings 
# Only dictionary "materials" required, the remaining are only support variables
elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
plastic_steel = {'material_model': 'chaboche', 'mpar': {'E': 210.e3, 'nu': 0.3, 'Y0': 200., 'Hkin': 5.e3, 'binf': 500., 'Hiso': 1.e3, 'kinf': 100.}}
chaboche_umat = {'material_model': 'user', 'mpar': {'nstatv': 8, 'umat': 'chaboche.obj', 
                                                    'user_mpar_array': (210.e3, 0.3, 500., 1.e3, 1.e-2, 5.e3, 2.e-4)}}
dummy_elastic = {'material_model': 'elastic', 'mpar': {'E': 1.e-6, 'nu': 0.3}}

materials = {'rail': plastic_steel, 'wheel': elastic_steel, 
             'shadow_rail': dummy_elastic, 
             'contact_trusses_wheel': dummy_elastic}
             
             
# Load settings
load_parameters = {'initial_depression': 0.01, 'normal_load': 5000, 'slip': 0.02}
contact_parameters = {'penalty_stiffness': 1.e6, 'friction': 0.2}