"""This module meshes a rail profile

.. codeauthor:: Knut Andreas Meyer
"""
# Python imports
from __future__ import print_function
import os, sys, inspect
import numpy as np

# Abaqus imports
from abaqusConstants import *
from abaqus import mdb
import mesh, part

# Project imports
from rollover.utils import naming_mod as names
from rollover.utils import get_utils as get
from rollover.utils import abaqus_python_tools as apt

from rollover.three_d.utils import symmetric_mesh_module as sm



def create_basic_mesh(rail_part, point_in_refine_cell, fine_mesh, coarse_mesh):
    """Mesh the rail with basic settings
    
    The cell containing point_in_refine_cell will get the fine_mesh size. The global mesh seed will
    be set to coarse mesh. 
    
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param point_in_refine_cell: x,y,z coordinates of a point within cell that should have fine mesh
    :type point_in_refine_cell: iterable(float)
    
    :param fine_mesh: mesh size in the contact region
    :type fine_mesh: float
    
    :param fine_mesh: global mesh size
    :type fine_mesh: float
        
    :returns: None
    :rtype: None

    """
    
    mesh_parameters = [{'point': None,
                        'size': coarse_mesh,
                        'mc': {'elemShape': TET,
                               'technique': FREE,
                               #'algorithm': ADVANCING_FRONT
                              },
                        'et': {'element_order': 2,
                               'reduced_integration': False
                              }
                        },
                        {'point': point_in_refine_cell,
                         'size': fine_mesh,
                         'mc': {'elemShape': TET,
                                'technique': FREE,
                                #'algorithm': ADVANCING_FRONT
                               },
                         'et': {'element_order': 2,
                                'reduced_integration': False
                               }
                         }
                        ]
    create_mesh(rail_part, mesh_parameters)
    

def create_mesh(rail_part, mesh_parameters):
    """Mesh the rail with advanced settings given by mesh_parameters
    
    mesh_parameters list of dictionaries with the following keys
    
    'point' (list(float)): Point in the cell to be refined
    
    'size' (float): Mesh size in given cell
    
    'mc' (dictionary): Arguments to Abaqus' setMeshControls(...) function
    
    'et' (dictionary): Specifications of the element type. This dictionary should contain the 
    following fields:
    
    et['element_order']: 1 or 2
    
    et['reduced_integration'] True or False
    
    If the first point is None, these settings will be applied as the global settings to all regions
    
    Note that the edge seeds created for one cell will be overwritten by size specifications for 
    neighbouring cells. I.e., the last specified cell will retain all its edge seeds. 
    
    :param rail_part: The part in which the sets will be created
    :type rail_part: Part (Abaqus object)
    
    :param mesh_parameters: List of dictionaries describing the mesh parameters, see above
    :type mesh_parameters: list(dict)
        
    :returns: None
    :rtype: None

    """
    
    if mesh_parameters[0]['point'] is None:
        mp = mesh_parameters[0]
        rail_part.seedPart(size=mp['size'])
        
    for mp in mesh_parameters:
        # Get region to be set parameters for
        if mp['point'] is None:
            cells = [c for c in rail_part.cells]
        else:
            cells = [rail_part.cells.findAt(tuple(mp['point']))]
        
        # Set mesh controls for region
        #  Create dictionary for mesh controls, excluding point and size which are not arguments to 
        #  setMeshControls
        mc = mp['mc']
        rail_part.setMeshControls(regions=cells, **mc)
        
        elem_types = get_elem_types(order=mp['et']['element_order'], 
                                    reduced=mp['et']['reduced_integration'])
                                    
        rail_part.setElementType(regions=cells, elemTypes=elem_types)
        
#        if mp['point'] is not None:
#            edges = [rail_part.edges[enr] for enr in cells[0].getEdges()]
#            rail_part.seedEdgeBySize(edges=part.EdgeArray(edges=edges), size=mp['size'])
        for c in cells:
            edges = [rail_part.edges[enr] for enr in c.getEdges()]
            rail_part.seedEdgeBySize(edges=part.EdgeArray(edges=edges), size=mp['size'],
                                     constraint=FINER)
            
    rail_part.generateMesh()
    
    sm.make_periodic_meshes(rail_part, 
                            source_sets=[rail_part.sets[names.rail_side_sets[0]]], 
                            target_sets=[rail_part.sets[names.rail_side_sets[1]]])
    
    rail_part.generateMesh()
    # Adding an additional generation seem to solve some issues. This should be investigated!
    # rail_part.generateMesh()
        

def get_elem_types(order, reduced):
    """Get the Abaqus element types depending on the element type specifications
    
    :param order: Element order (1st or 2nd)
    :type order: int
    
    :param reduced: Should reduced order integration be applied when possible?
    :type reduced: bool
        
    :returns: A list of element types
    :rtype: list(mesh.elemType (Abaqus object))

    """
    if order == 1:
        elem_codes = [C3D8R if reduced else C3D8, C3D6, C3D4]
    elif order == 2:
        elem_codes = [C3D20R if reduced else C3D20, C3D15, C3D10]
    
    elem_types = [mesh.ElemType(elemCode=ec, elemLibrary=STANDARD) for ec in elem_codes]
    
    return elem_types