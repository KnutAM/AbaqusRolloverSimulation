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
        material(the_model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='RailMaterial')
        the_model.HomogeneousSolidSection(name=section_names['rail'], material='RailMaterial', thickness=None)
    
    if 'wheel' in section_names:
        material(the_model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='WheelMaterial')
        the_model.HomogeneousSolidSection(name=section_names['wheel'], material='WheelMaterial', thickness=None)
    
    if 'shadow' in section_names:
        material(the_model, matmod='elastic', mpar={'E': 1.e-6, 'nu': 0.3}, name='ShadowMaterial')
        the_model.HomogeneousSolidSection(name=section_names['shadow'], material='ShadowMaterial', thickness=None)
    
    if 'contact' in section_names:
        material(the_model, matmod='elastic', mpar={'E': 1.e-6, 'nu': 0.3}, name='ContactTrussMaterial')
        the_model.TrussSection(name=section_names['contact'], material='ContactTrussMaterial', area=1.0)
    

def material(fe_model, matmod, mpar, name):
    fe_model.Material(name=name)
    if matmod=='elastic':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
    elif matmod=='chaboche':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
        print('Warning, chaboche model only implemented as elastic model so far')
    else:
        print('Material model ' + matmod + ' is not supported')
    