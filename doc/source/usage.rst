How to use
**********

This document describes the overall workflow for how to setup and run a 
rollover simulation. For more details, please see :doc:`tutorials` and 
:doc:`examples`.

|program_work_flow|

|program_work_flow_png|


.. |program_work_flow| image:: /img/program_work_flow.pdf
          :align: middle
          :alt: more info
          
.. |program_work_flow_png| image:: /img/program_work_flow.png
          :align: middle
          :alt: more info

The rollover simulation consists of an elastic wheel rolling over a rail. 
To apply the "wormhole" boundary condition for the wheel, a set of user
subroutines (usub) are used. So in order to setup the simulation, the 
user must do the following steps

1. Create the rail ("Rail ``.cae`` file")
2. Create the wheel ("Wheel folder")
3. Compile the user subroutines ("usub (``.obj/.o`` file)")
4. Create the rollover simulation ("Input files")

Normally, the usub step is not required each time. This only changes if
additional user subroutines (e.g. umat) are also being used in the 
simulation. The following sections describe in detail how each of these 
four steps are conducted.

Create the rail
===============

Create a basic rail
-------------------
A basic rail is created by calling the abaqus script `create_rail.py`
from a folder containing a file `rail_settings.json` This file should 
contain the following settings:

- ``"material"`` (optional): Describes the material model and 
  parameters to be applied to the entire rail. See "Material 
  specification" below. If not given, an elastic material will be set.
- ``"rail_profile"`` (mandatory): Path to an Abaqus sketch, saved as a 
  ``.sat`` file, describing the profile of the rail in the xy-plane. See
  "Creating a profile sketch" for further details.
- ``"rail_length"`` (mandatory): The length (z) of the rail to be 
  created
- ``"rail_name"`` (mandatory): The name of the ``.cae`` file to be 
  created
- ``"refine_region"`` (optional): ``[[xmin, ymin], [xmax, ymax]]`` 
  Describes a rectangle within which the fine mesh will be applied and
  from which the contact surface will be defined. If not given, the 
  entire rail will be finely meshed, and the entire surface will be set 
  as contact surface.
- ``"point_in_refine_cell"`` (mandatory): ``[x,y,z]`` A point that is 
  inside the refined cell (i.e. both within "refine_region" and inside 
  the sketched profile). 
- ``"fine_mesh"`` (mandatory): The element size for the fine mesh
- ``"coarse_mesh"`` (mandatory): The element size for the coarse mesh.
- ``"sym_dir"`` (optional): The direction of the symmetry plane. If not
  given, no symmetry is assumed. If given, should be ``[1,0,0]`` or 
  ``[-1,0,0]``.
  
Material specification
^^^^^^^^^^^^^^^^^^^^^^
The material specification should contain the following settings:

- ``"material_model"``: Name of the material model to use
- ``"mpar"``: Material parameters, given with new keywords.

The supported material models are described below. Note, however, that 
after the rail ``.cae`` file has been created, you can freely edit the 
material model specification.

elastic
"""""""
.. code-block:: none

    "material_model": "elastic"
    "mpar": {"E": <Elastic modulus>, "nu": <Poissons ratio>}

chaboche
""""""""
.. code-block:: none

    "material_model": "chaboche",
    "mpar": {"E": <Elastic modulus>, "nu": <Poissons ratio>, 
             "Y0": <Initial yield>, "Qinf": <Isotropic saturation>,
             "biso": <Isotropic hardening rate>,
             "Cmod": [<Kinematic modulus 1>, ..., <Kinematic modulus N>],
             "gamma": [<Kinematic saturation speed 1>, ..., 
                       <Kinematic saturation speed N>]
            }

user
""""
.. code-block:: none

    "material_model": "user",
    "mpar": {"user_mpar_array": [<param 1>, ..., <param N>],
             "nstatv": <num_state_variables>
            }

Creating a profile sketch
^^^^^^^^^^^^^^^^^^^^^^^^^
To create a profile sketch in Abaqus CAE, perform the following steps:

1. Open Abaqus CAE
2. Double-click "Sketches" in the model tree
3. Give your sketch a name (this will have no effect later) and press
   "Continue"
4. Draw a profile and exit the sketch. 
5. Go "File"-"Export"-"Sketch..." and choose a location to save the 
   sketch.
6. In the new dialog box, select the sketch you want to export and press 
   "OK"
7. Choose the ACIS version. Just make sure that it can be read by your 
   system, press ok and you are done.
   
.. note:: The sketch will only contain the geometry, so if you later 
          want to edit a dimension later, you need to save the .cae
          file containing the sketch. Then you can edit the sketch in 
          this file later and export it again. 


Modifying the basic rail
------------------------
To script all details of how the rail should be meshed, and if there 
should be inclusions, cracks, etc. is rather cumbersome and not time 
efficient. Therefore, it is chosen to allow the user to edit the rail
part as an intermediate step. In general, creating the basic rail above
is not necessary, but highly recommended as it ensures that correct 
names are given to sets and surfaces. When modifying the rail part, it 
is therefore important not to change set names etc. With large geometric 
modifications, it might also be necessary to redefine these sets to 
capture the correct parts. A summary of the requirements for the rail
part that is used later when generating the rollover is given here.

*  The model should be named "RAIL"
*  The part should be named "RAIL"
*  Sets

   *  "BOTTOM_NODES" should contain all nodes at the bottom of the 
      rail
   *  "SIDE1_SET" should contain all nodes on the face at z=0
   *  "SIDE2_SET" should contain all nodes on the face at z=L where L is 
      the length of the rail.
   *  If present, "SYMMETRY" should contain all nodes on the symmetry face
      at x=0

.. Padding

*  Surfaces

   *  "RAIL_CONTACT_SURFACE" should be the surface where potential 
      contact with the wheel can occur.

.. Padding

*  Mesh

   *  The rail must be meshed, and no constraints should be added (i.e. 
      one cannot use incompatible meshes because this introduces 
      constraints between the nodes). 
   *  The mesh in "SIDE1_SET" and "SIDE2_SET" must match. I.e. the mesh 
      in "SIDE2_SET" should be a translation from the mesh in "SIDE1_SET".

.. Padding

*  Sections, including material definitions, must be defined on cells 
   of the part.


When working with TET elements, the script 
``make_rail_mesh_symmetric.py`` can be used to ensure a symmetric mesh.
Otherwise, if HEX meshes are used as a mapped mesh, this will also give
the same mesh on both sides. 


Create the wheel
================


Compile user subroutines
========================


Create the rollover simulation
==============================
