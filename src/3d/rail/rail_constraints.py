"""This module adds the linear constraints to enforce symmetry conditions on the rail
Constraints between points in the same position in the xy-plane are added by the following equations

.. math::

    u_x^{(\\mathrm{c})} &= u_x^{(\\mathrm{r})} \\
    u_y^{(\\mathrm{c})} &= u_y^{(\\mathrm{r})} \\
    u_z^{(\\mathrm{c})} &= u_z^{(\\mathrm{r})} + 
    u_z^{(\\mathrm{rp})} \\frac{(z^{(\\mathrm{c})} - z^{(\\mathrm{r})})}{L_\\mathrm{rail}} + 
    (y-y^{(\\mathrm{rp})})\\phi_x^{(\\mathrm{rp})}
    
:math:`u_x^{(\\mathrm{c})}, u_y^{(\\mathrm{c})}, u_z^{(\\mathrm{c})}, u_x^{(\\mathrm{r})}, 
u_y^{(\\mathrm{r})}, u_z^{(\\mathrm{r})}` are the :math:`x`, :math:`y` and :math:`z` displacements of 
the constrained, :math:`(\\mathrm{c})`, and retained, :math:`(\\mathrm{r})`, degrees of freedom. 
:math:`x, y` are the :math:`x` and :math:`y` coordinates of the points, and :math:`z^{(\\mathrm{c})}` 
and :math:`z^{(\\mathrm{r})}` are the :math:`z`-coordinates of the constrained and retained points 
respectively. :math:`x^{(\\mathrm{rp})}, y^{(\\mathrm{rp})}, z^{(\\mathrm{rp})}` are the :math:`x,y,z` 
coordinates of the reference point. 
:math:`u_x^{(\\mathrm{rp})}, u_y^{(\\mathrm{rp})}, u_z^{(\\mathrm{rp})}` are the displacements of the 
reference point and 
:math:`\\phi_x^{(\\mathrm{rp})}, \\phi_y^{(\\mathrm{rp})}, \\phi_z^{(\\mathrm{rp})}` are its rotations 
around the :math:`x,y,z` axes. Finally, :math:`L_\\mathrm{rail}` is the length of the rail. 

The nodes at the bottom of the rail are constrained according to above, but with 
:math:`u_x^{(\\mathrm{r})} = u_y^{(\\mathrm{r})} = u_z^{(\\mathrm{r})} = 0` and 
:math:`z^{(\\mathrm{r})} = 0`


Test of documentation, including example from 
https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#math. Only the inline 
math environment seem to work properly. 

.. math::

   (a + b)^2  &=  (a + b)(a + b) \\
              &=  a^2 + 2ab + b^2
    

.. codeauthor:: Knut Andreas Meyer
"""

import sys, os
import numpy as np

import abaqus
from abaqusConstants import *
import regionToolset, mesh

import naming_mod as names

def add_rail_constraints(rail_part):
    rail_rp = add_ctrl_point(rail_part)
    

def add_ctrl_point(rail_part, z_coord):
    """Add the rail control point that is used to determine rail tension and bending 
    
    :param rail_part: The rail part
    :type rail_part: Part (Abaqus object)
    
    :param z_coord: The z-coordinate of the control point
    :type z_coord: float
    
    :returns: None
    :rtype: None

    """
    
    rail_rp = rail_part.ReferencePoint(point=(0.0, 0.0, z_coord))
    rail_part.Set(name=rail_rp_set, referencePoints=(rail_rp,))
    

def constrain_sides(retained_side_set, constrained_side_set):
    pass
    
    
def constrain_bottom(bottom_set):
    pass
    

def constrain_shadow_region(shadow_set, contact_set):
    pass
