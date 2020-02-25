# System imports
import sys
import os
import numpy as np

# Abaqus imports 
import assembly

# Custom imports (from present project)
# Should find better way of including by automating the path, however, __file__ doesn't seem to work...
sys.path.append(r'C:\Box Sync\PhD\MyArticles\RolloverSimulationMethodology\AbaqusRolloverSimulation\src')
import material_and_section_module as material_module
import setup_rail_module as rail_module
import setup_wheel_module as wheel_module
import setup_loading_module as loading_module
import setup_contact_module as contact_module

#Reload to allow multiple runs from abaqus (not neccessary for cluster runs)
if sys.platform.startswith('win'):
    reload(material_module)
    reload(rail_module)
    reload(wheel_module)
    reload(loading_module)
    reload(contact_module)


def main():
    # Settings
    rail_geometry = {'length': 100.0, 'height': 30.0, 'max_contact_length': 25.}
    rail_mesh = {'fine': 1.0, 'coarse': 5.0}
    rail_naming = {'part': 'RAIL', 'section': 'RAIL_SECTION', 'shadow_section': 'RAIL_SHADOW_SECTION'}
    
    wheel_geometry = {'outer_diameter': 400., 'inner_diameter': 50., 'max_contact_length': 25., 'rolling_angle': 100./(400./2.)}
    wheel_mesh = {'fine': 5.0, 'coarse': 20.0, 'refine_thickness': 10.0}
    wheel_naming = {'part': 'WHEEL', 'section': 'WHEEL_SECTION', 'rp': 'WHEEL_CENTER'}
    
    # Setup model
    model = mdb.models.values()[0]
    assy = model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    material_module.setup_sections(model, naming={'wheel': wheel_naming['section'], 
                                                  'rail': rail_naming['section'], 
                                                  'shadow': rail_naming['shadow_section']})
    
    # Setup rail
    rail_part, rail_contact_surf, bottom_reg = rail_module.setup_rail(model, assy, rail_geometry, rail_mesh, rail_naming)
    
    # Setup wheel
    wheel_part, wheel_contact_surf, ctrl_pt_reg = wheel_module.setup_wheel(model, assy, wheel_geometry, wheel_mesh, wheel_naming)
    
    # Setup loading
    loading_module.loading(model, assy, ctrl_pt_reg, bottom_reg)
    
    # Setup contact conditions
    contact_module.setup_contact(model, assy, rail_contact_surf, wheel_contact_surf)


if __name__ == '__main__':
    main()
