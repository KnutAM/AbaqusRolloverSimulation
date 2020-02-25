from abaqusConstants import *
import section
import material

def setup_sections(model, naming):
    material(model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='RailMaterial')
    model.HomogeneousSolidSection(name=naming['rail'], material='RailMaterial', thickness=None)
    
    material(model, matmod='elastic', mpar={'E': 210.e3, 'nu': 0.3}, name='WheelMaterial')
    model.HomogeneousSolidSection(name=naming['wheel'], material='WheelMaterial', thickness=None)
    
    material(model, matmod='elastic', mpar={'E': 1.e-6, 'nu': 0.3}, name='ShadowMaterial')
    model.HomogeneousSolidSection(name=naming['shadow'], material='ShadowMaterial', thickness=None)
    

def material(fe_model, matmod, mpar, name):
    fe_model.Material(name=name)
    if matmod=='elastic':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
    elif matmod=='chaboche':
        fe_model.materials[name].Elastic(table=((mpar['E'], mpar['nu']), ))
        print('Warning, chaboche model only implemented as elastic model so far')
    else:
        print('Material model ' + matmod + ' is not supported')
    