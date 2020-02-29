from abaqusConstants import *
import section
import material

def setup_sections(the_model, naming):
    if 'rail' in naming:        
        material(the_model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='RailMaterial')
        the_model.HomogeneousSolidSection(name=naming['rail'], material='RailMaterial', thickness=None)
    
    if 'wheel' in naming:
        material(the_model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='WheelMaterial')
        the_model.HomogeneousSolidSection(name=naming['wheel'], material='WheelMaterial', thickness=None)
    
    if 'shadow' in naming:
        material(the_model, matmod='elastic', mpar={'E': 1.e-6, 'nu': 0.3}, name='ShadowMaterial')
        the_model.HomogeneousSolidSection(name=naming['shadow'], material='ShadowMaterial', thickness=None)
    
    if 'contact' in naming:
        material(the_model, matmod='elastic', mpar={'E': 1.e-6, 'nu': 0.3}, name='ContactTrussMaterial')
        the_model.TrussSection(name=naming['contact'], material='ContactTrussMaterial', area=1.0)
    

def material(fe_model, matmod, mpar, name):
    fe_model.Material(name=name)
    if matmod=='elastic':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
    elif matmod=='chaboche':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
        print('Warning, chaboche model only implemented as elastic model so far')
    else:
        print('Material model ' + matmod + ' is not supported')
    