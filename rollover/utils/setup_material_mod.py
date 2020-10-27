"""This module contains functions that sets up material models

.. codeauthor:: Knut Andreas Meyer
"""
# Abaqus imports
from abaqusConstants import *
import material


def add_material(the_model, material_spec, name):
    """Add a material to the_model according to material_spec with name=name.
    
    :param the_model: The model to which the sketch will be added
    :type the_model: Model object (Abaqus)
    
    :param material_spec: Dictionary containing the fields `'material_model'` and `'mpar'`:
                          
                          - `'material_model'`: which material model to use, currently `'elastic'`, 
                            `'chaboche'`, and `'user'` are supported. 
                          - `'mpar'`: Material parameters, please see function corresponding to 
                            `'material_model'` below for detailed requirements
                            
    :type material_spec: dict
    
    :param name: The name of the material
    :type name: str (max len = 80)
    
    :returns: None 
    :rtype: None

    """
    if name in the_model.materials.keys():
        raise ValueError('A material with name ' + name + ' has already been created')
        
    the_material = the_model.Material(name=name)
    matmod = material_spec['material_model']
    mpar = material_spec['mpar']
    if matmod=='elastic':
        setup_elastic(the_material, mpar)
    elif matmod=='chaboche':
        setup_chaboche(the_material, mpar)
    elif matmod=='user':
        setup_user(the_material, mpar)
    else:
        apt.log('Material model ' + matmod + ' is not supported')
    

def setup_elastic(the_material, mpar):
    """Setup elastic material behavior
    
    :param the_material: The material to which elastic behavior will be added
    :type the_material: Material object (Abaqus)
    
    :param mpar: Dictionary containing the fields
                          
                          - `'E'`: Young's modulus
                          - `'nu'`: Poissons ratio
    :type mpar: dict
    
    :returns: None 
    :rtype: None

    """
    the_material.Elastic(table=((mpar['E'], mpar['nu']), ))
    
    
def setup_chaboche(the_material, mpar):
    """Setup plastic material behavior with the chaboche model
    
    :param the_material: The material to which elastic behavior will be added
    :type the_material: Material object (Abaqus)
    
    :param mpar: Dictionary containing the fields
                          
                          - `'E'`: Young's modulus
                          - `'nu'`: Poissons ratio
                          - `'Y0'`: Initial yield limit
                          - `'Qinf'`: Saturated isotropic yield limit increase
                          - `'biso'`: Speed of saturation for isotropic hardening
                          - `'Cmod'`: List of kinematic hardening modulii
                          - `'gamma'`: List of kinematic saturation parameters
                          
    :type mpar: dict
    
    :returns: None 
    :rtype: None

    """
    setup_elastic(the_material, mpar)
    
    kinpar = [mpar['Y0']]
    for Cmod, gamma in zip(mpar['Cmod'], mpar['gamma']):
        kinpar.append(Cmod)
        kinpar.append(gamma)
        
    the_material.Plastic(table=(tuple(kinpar),), hardening=COMBINED, dataType=PARAMETERS, 
                         numBackstresses=len(mpar['Cmod']))
    the_material.plastic.CyclicHardening(table=((mpar['Y0'], mpar['Qinf'], mpar['biso']),), 
                                         parameters=ON)


def setup_user(the_material, mpar):
    """Setup user material behavior
    
    :param the_material: The material to which elastic behavior will be added
    :type the_material: Material object (Abaqus)
    
    :param mpar: Dictionary containing the fields
                          
                          - `'user_mpar_array'`: List of user material parameters
                          - `'nstatv'`: Number of state variables for user material model
                          
    :type mpar: dict
    
    :returns: None 
    :rtype: None

    """
    the_material.UserMaterial(type=MECHANICAL, unsymm=OFF, 
                              mechanicalConstants=mpar['user_mpar_array'])
    the_material.Depvar(n=mpar['nstatv'])
