# System imports
import inspect

# Abaqus imports
from abaqusConstants import *
import section
import material

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
src_file_path = inspect.getfile(lambda: None)
if not src_file_path in sys.path:
    sys.path.append(os.path.dirname(src_file_path))
from user_settings import materials

def setup_sections(the_model, section_names):
    if 'rail' in section_names:        
        the_material = materials['rail']
        material(the_model, matmod=the_material['material_model'], mpar=the_material['mpar'], 
                 name='RailMaterial')
        the_model.HomogeneousSolidSection(name=section_names['rail'], material='RailMaterial', thickness=None)
    
    if 'wheel' in section_names:
        the_material = materials['wheel']
        material(the_model, matmod=the_material['material_model'], mpar=the_material['mpar'], 
                 name='WheelMaterial')
        the_model.HomogeneousSolidSection(name=section_names['wheel'], material='WheelMaterial', thickness=None)
    
    if 'shadow' in section_names:
        the_material = materials['shadow_rail']
        material(the_model, matmod=the_material['material_model'], mpar=the_material['mpar'], 
                 name='ShadowMaterial')
        the_model.HomogeneousSolidSection(name=section_names['shadow'], material='ShadowMaterial', thickness=None)
    
    if 'contact' in section_names:
        the_material = materials['contact_trusses_wheel']
        material(the_model, matmod=the_material['material_model'], mpar=the_material['mpar'], 
                 name='ContactTrussMaterial')
        the_model.TrussSection(name=section_names['contact'], material='ContactTrussMaterial', area=1.0)
    

def material(fe_model, matmod, mpar, name):
    fe_model.Material(name=name)
    if matmod=='elastic':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
    elif matmod=='chaboche':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
        fe_model.materials[name].Plastic(table=((mpar['Y0'], mpar['Hkin'], mpar['Hkin']/mpar['binf']),), hardening=COMBINED, dataType=PARAMETERS, numBackstresses=1)
        fe_model.materials[name].plastic.CyclicHardening(table=((mpar['Y0'], mpar['kinf'], mpar['Hiso']/mpar['kinf']),), parameters=ON)
    else:
        print('Material model ' + matmod + ' is not supported')
    