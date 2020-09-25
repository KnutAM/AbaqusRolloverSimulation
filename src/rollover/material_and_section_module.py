# System imports
import inspect

# Abaqus imports
from abaqusConstants import *
import section
import material

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not this_path in sys.path:
    sys.path.append(this_path)
import user_settings
import abaqus_python_tools as apt
import get_utils as get
import naming_mod as names
import user_subroutine as usub

def setup_sections():
    the_model = get.model()
    materials = user_settings.materials
    # Rail
    rail_material = materials['rail']
    material(the_model, matmod=rail_material['material_model'], mpar=rail_material['mpar'], 
                 name='rail_material')
    the_model.HomogeneousSolidSection(name=names.rail_sect, material='rail_material')
    
    # Shadow rail
    rail_shadow_material = materials['shadow_rail']
    material(the_model, matmod=rail_shadow_material['material_model'], 
             mpar=rail_shadow_material['mpar'], name='rail_shadow_material')
    the_model.HomogeneousSolidSection(name=names.rail_shadow_sect, material='rail_shadow_material')
    
    # Dummy wheel elements
    wheel_dummy_material = materials['contact_trusses_wheel']
    material(the_model, matmod=wheel_dummy_material['material_model'], 
             mpar=wheel_dummy_material['mpar'], name='wheel_dummy_material')
    the_model.TrussSection(name=names.wheel_dummy_contact_sect, material='wheel_dummy_material', 
                           area=1.0)
    
    

def material(fe_model, matmod, mpar, name):
    the_material = fe_model.Material(name=name)
    if matmod=='elastic':
        the_material.Elastic(table=((mpar['E'], mpar['nu']), ))
    elif matmod=='chaboche':
        the_material.Elastic(table=((mpar['E'], mpar['nu']), ))
        the_material.Plastic(table=((mpar['Y0'], mpar['Hkin'], mpar['Hkin']/mpar['binf']),), hardening=COMBINED, dataType=PARAMETERS, numBackstresses=1)
        the_material.plastic.CyclicHardening(table=((mpar['Y0'], mpar['kinf'], mpar['Hiso']/mpar['kinf']),), parameters=ON)
    elif matmod=='user':
        the_material.UserMaterial(type=MECHANICAL, unsymm=OFF, mechanicalConstants=mpar['user_mpar_array'])
        the_material.Depvar(n=mpar['nstatv'])
        if user_settings.material_model_folder:
            usub.copy_all_files_and_folders_from_folder(user_settings.material_model_folder + 
                                                        '/' + mpar['src_folder'])
        else:
            apt.log('material_model_folder must be specified in user_settings to use umats')
    else:
        apt.log('Material model ' + matmod + ' is not supported')
    
