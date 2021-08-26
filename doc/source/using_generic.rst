General instructions
====================
This section describes information common to multiple methods, or steps
in the methods. 

.. _addcycles: 

Adding rolling cycles
---------------------
When adding many cycles, Abaqus CAE is rather slow. Therefore, a 
script is provided to extend a simulation by adding cycles with the same 
content repeated. Consider the case that you want to run approximately 1000 cycles. 
Abaqus CAE will spend a long time generating all the required steps. But you would 
only like to have the full stress and strain field output saved every 25th cycle. In that case, 
specify 26 cycles under ``"num cycles"`` under "loading". Request output every 25th cycle by
specifying 25 under ``"cycles"`` in the specific row in the "output" table. 
This script can then be used to duplicate the last 25 steps 40 times via direct input file editing. 
In total, 1001 cycles will then be simulated with the specific output each 25th cycle. 

To add cycles, call the python script `append_extra_cycles.py` with the 
multiplication factor (e.g. 40 above) as the first argument and the input file as the 
second argument. The input file defaults to "rollover.inp".
If called with multiplication factor 4 in the above example, 101 cycles
would be created. 

.. _runsim: 

Running simulation
------------------
To run the simulation the following (generated) files are 
required to be in the simulation directory:

*  ``rollover.inp`` (can have different name): The Abaqus input file
*  ``load_param.txt`` (must have this name): 
   Automatically generated file in the same 
   directory as ``rollover.inp`` when creating rollver. 
   Describes the loading parameters 
*  ``uel_stiffness.txt`` (must have this name): 
   File specifying the wheel stiffness matrix. 
   Automatically generated when creating the wheel, automatically copied
   to the same directory as ``rollover.inp`` when creating rollover
*  ``rp_coord.txt`` (must have this name): 
   File specifying the location of the reference points.
   Automatically generated in the same folder as ``rollover.inp`` 
   when creating rollover.

In addition, the user subroutine object file must be available, but 
it does not need to reside in the simulation directory, but can be in 
a separate directory and its path specified as <path_to_usub>.

Run the simulation by

.. code-block:: bash

   abaqus job=rollover user=<path_to_usub>


.. _jsonformat: 

The json format
---------------
The ``json`` format is used for the input data. Mostly, the files 
should be written with a similar formatting as for a Python dictionary. 
However, there are a few important differences:

*  Booleans are written ``true`` and ``false``, 
   as opposed to ``True`` and ``False``.
*  All strings (keywords and variables) must be enclosed in double 
   quotes (single quotes are not accepted).
*  Exponential formats must be written ``A.BeC`` 
   (as opposed to ``A.eC``) where ``A``, ``B``, and ``C`` are integers. 
   E.g. ``1.0e-3`` is ok, but not ``1.e-3``.
*  Python's ``None`` is written as ``null``.
*  Comma is not allowed after the last item in a dictionary

To ensure the correct data format, one can write the following code in 
Python to generate the ``json`` file:

.. code-block:: python

   import json
   filename = 'example.json'	# Give the filename that you want to save to

   # Define the parameters you want to save as a Python dictionary
   param = {'key1': [1,2,3],	# Example of list data
           'key2': 'this is a string example data' # Example of string data
           }
   with open(filename, 'w') as fid:
      # Using indent=1 for nicer output, but not required
      json.dump(param, fid, indent=1)	

.. _datafolder: 

The data folder and how to specify paths
----------------------------------------
In the repository, there is a folder named "data". This contains some
examples (which are version controlled). However, additional contents 
added to the subfolders are ignored by the version control and are 
suitable for adding data that can be reused later. Examples include 
profile sketches, generated wheels and rails, and 
compiled user subroutines. 

To simplify the use of contents from this folder, path inputs in the 
``*_settings.json`` files can be relative the data folder. To do this, 
the path should start by ``":/"``, e.g. ``":/rails/rail_example.cae"``.
Otherwise, and absolute or relative (to the Abaqus working directory) 
path can be specified. 

.. _sketchcreation:

Creating a profile sketch
-------------------------
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
