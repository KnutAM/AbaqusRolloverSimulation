# This example file must be renamed to user_settings.py
# That file is ignored by git and can thus be used to change settings without being registered as change in code

# Overall simulation settings
simulation_name = 'rollover'
    
# Rail settings
rail_geometry = {'length': 100.0, 'height': 30.0, 'max_contact_length': 25.}
rail_mesh = {'fine': 1.0, 'coarse': 5.0}
rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}

# Wheel settings
use_substructure = True
new_substructure = False
substructureFile='c:/work/Abaqus/2017/Temp/wheel_substr1_Z1.sim'
odbFile='c:/work/Abaqus/2017/Temp/wheel_substr1.odb'

wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
wheel_mesh = {'fine': 2.0, 'coarse': 20.0, 'refine_thickness': 10.0}
wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER', 
				'contact_section': 'WHEEL_CONTACT_SECTION'}


# Material settings 
# Only dictionary "materials" required, the remaining are only support variables
elastic_steel = {'material_model': 'elastic', 'mpar': {'E': 210.e3, 'nu': 0.3}}
#plastic_steel = 
dummy_elastic = {'material_model': 'elastic', 'mpar': {'E': 1.e-6, 'nu': 0.3}}

materials = {'rail': elastic_steel, 'wheel': elastic_steel, 'shadow_rail': dummy_elastic, 'contact_trusses_wheel': dummy_elastic}