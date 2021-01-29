Workflow
********

In order to create a simulation, three objects are required:

#. An Abaqus Model Database (.cae) file containing the rail
#. A folder with data for a wheel super element
#. A user subroutine, that includes the subroutines supplied in the 
   present repository. 
   
The two former, as well as the simulation itself, can be created using 
either plugins in Abaqus CAE or via scripts. 
Details for each method, in addition to some general instructions,
are provided: 

.. toctree::
   :maxdepth: 1
   
   using_cae
   using_script
   using_generic

A default subroutine is compiled when running :file:`setup.py`. For 
further information on how to compile custom subroutines, please see
:ref:`subroutine_compilation`. 