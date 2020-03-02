# This example file must be copied to a file called user_settings.py
# That file is ignored by git and can thus be used to change settings without 
# being registered as change in code

# Overall simulation settings
simulation_name = 'rollover'
substructure_path = ('C:/Box Sync/PhD/MyArticles/' +
                    'RolloverSimulationMethodology/substructures')
max_contact_length = 25.0

# Rail settings
rail_geometry = {'length': 100.0, 'height': 30.0, 
                 'max_contact_length': max_contact_length}
rail_mesh = {'fine': 1.0, 'coarse': 5.0}
rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 
               'shadow_section': 'RAIL_SHADOW_SECTION'}

# Wheel settings
use_substructure = True
new_substructure = False

wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 
                  'max_contact_length': max_contact_length, 
                  'rolling_angle': 100./(400./2.)}
wheel_mesh = {'fine': 2.0, 'coarse': 20.0, 'refine_thickness': 10.0}
wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 
                'rp': 'WHEEL_CENTER', 'contact_part': 'WHEEL_CONTACT', 
                'contact_section': 'WHEEL_CONTACT_SECTION'}
                
substructure_name = ('substr_' + str(int(wheel_mesh['fine'])).zfill(2) + '_' + 
                     str(int(100*(wheel_mesh['fine']-int(wheel_mesh['fine'])))))

# Material settings 
# Only dictionary "materials" required, the remaining are only support variables
elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
#plastic_steel = 
dummy_elastic = {'material_model': 'elastic', 'mpar': {'E': 1.e-6, 'nu': 0.3}}

materials = {'rail': elastic_steel, 'wheel': elastic_steel, 
             'shadow_rail': dummy_elastic, 
             'contact_trusses_wheel': dummy_elastic}
             
             
# Load settings
load_parameters = {'initial_depression': 0.1, 'normal_load': 5000, 'slip': 0.0}