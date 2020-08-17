# System imports
import sys
import os
import numpy as np
import inspect

# Abaqus imports 
from abaqus import mdb
import assembly
from abaqusConstants import *

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
print(sys.path)

src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))


import material_and_section_module as matmod
import rail_setup as railmod
import wheel_setup as wheelmod
import wheel_substructure_create as wheel_ssc_mod
import wheel_substructure_import as wheel_ssi_mod
import loading_module as loadmod
import contact_module as contactmod
import user_settings

# Reload to account for script updates when running from inside abaqus CAE
reload(matmod)
reload(railmod)
reload(wheelmod)
reload(wheel_ssc_mod)
reload(wheel_ssi_mod)
reload(loadmod)
reload(contactmod)
reload(user_settings)


def main():
    # Settings
    ## Overall settings
    simulation_name = user_settings.simulation_name
    
    ## Rail settings
    rail_geometry = user_settings.rail_geometry
    rail_mesh = user_settings.rail_mesh
    rail_naming = user_settings.rail_naming 
    
    ## Wheel settings
    use_substructure = user_settings.use_substructure
    new_substructure = user_settings.new_substructure
    
    wheel_geometry = user_settings.wheel_geometry
    wheel_mesh = user_settings.wheel_mesh
    wheel_naming = user_settings.wheel_naming
    
    # Create wheel substructure model
    if new_substructure:
        wheel_ssc_mod.create_wheel_substructure(wheel_geometry, wheel_mesh, wheel_naming)
    
    # Setup model
    if simulation_name in mdb.models:    # Delete old model if exists
        del(mdb.models[simulation_name])
    
    the_model = mdb.Model(name=simulation_name, modelType=STANDARD_EXPLICIT)
    assy = the_model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    
    # Setup sections
    matmod.setup_sections(the_model, section_names={'wheel': wheel_naming['section'],
                                                    'rail': rail_naming['section'], 
                                                    'shadow': rail_naming['shadow_section'],
                                                    'contact': wheel_naming['contact_section']})
    
    # Setup rail
    rail_part, rail_contact_surf, bottom_reg = railmod.setup_rail(the_model, assy, rail_geometry, rail_mesh, rail_naming)
    
    # Setup wheel
    if use_substructure:
        wheel_part, wheel_contact_surf, ctrl_pt_reg = wheel_ssi_mod.import_wheel_substructure(the_model, assy, wheel_naming, 
                                                                                              wheel_geometry, wheel_mesh)
    else:
        wheel_part, wheel_contact_surf, ctrl_pt_reg = wheelmod.setup_wheel(the_model, assy, wheel_geometry, wheel_mesh, wheel_naming)

    # Position wheel
    loadmod.preposition(assy)

    # Setup loading
    loadmod.initial_bc(the_model, assy, ctrl_pt_reg, bottom_reg)
    
    
    # Setup contact conditions
    contactmod.setup_contact(the_model, assy, rail_contact_surf, wheel_contact_surf)
    
    if simulation_name in mdb.jobs:
        del(mdb.jobs[simulation_name])
        
    the_job = mdb.Job(name=simulation_name, model=simulation_name)
    

if __name__ == '__main__':
    main()
