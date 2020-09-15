import sys
import os
import numpy as np
import inspect


def rotate_stiffness(stiffness_matrix, ang):
    ndof = stiffness_matrix.shape[0]
    nnod = (ndof-1)/2
    
    Qfull = np.zeros((ndof,ndof))
    Q = get_rotation_matrix(ang)
    Qfull[:2,:2] = Q
    Qfull[2,2] = 1.0
    for i in range(1, nnod):
        i1 = 1+2*i
        i2 = i1+1
        Qfull[np.ix_([i1,i2],[i1,i2])] = Q
    
    return np.dot(np.dot(Qfull, stiffness_matrix), np.transpose(Qfull))


def rotate_and_translate_coordinates(coords, ang, trans_vec):
    Q = get_rotation_matrix(ang)
    Q3 = np.zeros((3,3))
    Q3[:2,:2] = Q
    Q3[2,2] = 1.0
    nnod = coords.shape[1]
    c_rot = np.zeros(coords.shape)
    trans_vec = np.array(trans_vec)
    for i in range(nnod):
        c_rot[:, i] = np.dot(Q3, coords[:, i]) + trans_vec
    
    return c_rot


def get_rotation_matrix(ang):
    return np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])


def get_preposition_motion():
    rolling_par = get_rolling_parameters()
    radius = rolling_par['radius']
    rolling_angle = -0.5*rolling_par['angle']
    rgeom = user_settings.rail_geometry
    
    vector = ((rgeom['length'] - rgeom['max_contact_length'])/2.0, radius, 0.0)
    
    return rolling_angle, vector
    

def create_uel(stiffness_matrix, coords):
    # Need to save this first as loadmod.get_preposition_motion require this file to exist.
    np.save('uel_coords.npy', coords)
    
    this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
    
    base_file = this_path + '/uel_base_file.f90'
    with open(base_file, 'r') as fid:
        uel_str = fid.read()
    
    # Rotate stiffness and coordinates to account for rotation during prepositioning
    # rotation_angle, translation_vector = get_preposition_motion()
    # krot = rotate_stiffness(stiffness_matrix, rotation_angle)
    # coords_rot = rotate_and_translate_coordinates(coords, rotation_angle, translation_vector)
    
    stiffness_str = get_stiffness_str(stiffness_matrix)
    uel_str = uel_str.split('    !<ke_to_be_defined_by_python_script>')
    uel_str = uel_str[0] + stiffness_str + uel_str[1]
    
    coord_str = get_coord_str(coords)
    uel_str = uel_str.split('    !<coords_to_be_defined_by_python_script>')
    uel_str = uel_str[0] + coord_str + uel_str[1]
    
    with open('uel.for', 'w') as fid:
        fid.write(uel_str)


def get_stiffness_str(ke):
    the_str = ''
    for i in range(ke.shape[0]):
        for j in range(ke.shape[1]):
            the_str = the_str + '    ke(%u,%u) = %23.15e\n' % (i+1,j+1,ke[i,j])
    
    return the_str
    

def get_coord_str(coords):
    the_str = '    allocate(coords(%u, %u))\n' % (coords.shape[0], coords.shape[1])
    for n, coord in enumerate(np.transpose(coords)):
        for i, c in enumerate(coord):
            the_str = the_str + '    coords(%u,%u) = %23.15e\n' % (i+1, n+1, c)
    
    return the_str