Introduction
************

The rollover simulation package provides scripts and user subroutines
to Abaqus Standard (i.e. quasi-static analysis) for simulating an 
elastic wheel rolling over a rail. The rail can have complex 
geometry and material behavior, but the mesh at the end faces must be
periodic. 

|graphical_abstract_svg|

As shown to the right in the figure, the simulation effectively 
considers an infinite number of periodic cells, where the wheel spacing
equals to the simulated rail length. The purpose of this setup is to
obtain accurate displacements for much shorter rail lengths compared 
with not using the periodic boundary conditions. 

Between each simulation, the wheel is mapped back to a new starting 
position. The wheel is modeled as a linear elastic super-element 
(substructure), removing redundant degrees of freedom. The wheel must
be rotationally symmetric.

Implementation
==============
The implementation consists of (1) a python library with functions to 
setup the Abaqus simulations and (2) fortran user subroutines for 
mapping back the wheel, as well as for modeling the wheel itself.

The python library can be called either via plugins from within the 
Abaqus CAE (:doc:`using_cae`), or from the command line using various 
input files (:doc:`using_script`). Modifications of the rail can be 
done from within Abaqus CAE, making it possible to use multiple 
materials, adding geometric features, changing the mesh, and so on.

Scripts are provided for combining the included fortran subroutines 
with additional subroutines, such as material models 
(see :ref:`subroutine_compilation`).



.. |graphical_abstract_svg| image:: /img/graphical_abstract_svg.svg
          :align: middle
          :alt: more info
