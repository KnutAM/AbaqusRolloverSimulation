Installation
************

In order to install (or rather setup) the library, the following steps 
are required. Before attempting to do so, please verify that your system
meets all the :ref:`prerequisites`.

- Download the repository:
  
  - Using git (latest): :command:`git clone --recurse-submodules https://github.com/KnutAM/AbaqusRolloverSimulation.git`,
  - zip download: `latest <https://github.com/KnutAM/AbaqusRolloverSimulation/archive/refs/heads/main.zip>`_ and `fortran_utils (latest) <https://github.com/KnutAM/fortran_utilities/archive/refs/heads/main.zip>`_
  - zip download of published version: 
    `v1.0 <https://github.com/KnutAM/AbaqusRolloverSimulation/archive/refs/tags/v1.0.zip>`_ and `fortran_utils (v0.1) <https://github.com/KnutAM/fortran_utilities/archive/refs/tags/v0.1.zip>`_
  **Note**: When using the zip downloads, you must manually copy the content of :file:`fortran_utils` to the :file:`AbaqusRolloverSimulation/usub/utils` folder
  
- From the top level in the repository, run :file:`scripts_py/setup.py`:
  :command:`python scripts_py/setup.py`. This will, amongst others, 
  create :file:`abaqus_v6.env`, which you might modify in the next step.
- To make the plugins work, Abaqus needs to find them. Unfortunately, 
  multiple locations are not supported. Therefore, you have two options:
  
  #. Add the following to :file:`abaqus_v6.env`: 
     :command:`plugin_central_dir = `<path_to_rollover_directory>/plugins'`
     This can only be done for one folder, therefore, make sure you 
     don't require this for other plugins.
  #. Alternatively, copy the :file:`plugins/rollover_plugin.py` to 
     :file:`%HOME%/abaqus_plugins` (Windows, if the environment variable :command:`HOME` exists), :file:`%HOMEDRIVE%%HOMEPATH%/abaqus_plugins` (Windows, otherwise), or :file:`~/abaqus_plugins` (Linux). This approach has the 
     downside that any fetched updates from the online 
     repositories containing changes to 
     :file:`plugins/rollover_plugin.py` will require manually 
     repeating this step.
     
- Copy :file:`abaqus_v6.env` to :file:`%HOME%` (Windows, if the environment variable :command:`HOME` exists), 
  :file:`%HOMEDRIVE%%HOMEPATH%` (Windows, otherwise),  or :file:`~`. 
  If you already have an environment file in your home directory, you need to 
  manually merge the changes (most likely you can just append the contents 
  of this new file to the old.)

.. _prerequisites:

Prerequisites
=============
The following programs must be installed:

- Abaqus, setup to compile and link user subroutines
- Python, version 2.7 or later

To verify that Abaqus works with user subroutines, run the following
command: :command:`abaqus verify -user_std`. Note, on Windows running
user subroutines from within CAE might be a problem even if the above
command works. In order to setup abaqus to work on Windows, you 
typically have to add something like the following to the 
:file:`abaqus.bat` file: 

.. code-block:: winbatch

    @call ifortvars.bat intel64 vs2013
    @call "C:\Program Files (x86)\Microsoft Visual Studio 12.0\VC\bin\amd64\vcvars64.bat" intel64 vs2013

But when opening a new Abaqus CAE session, :file:`abaqus.bat` might not
be called. If you have problems running from within CAE, you could add 
those lines to the file :file:`launcher.bat` 
(used when opening Abaqus CAE) as well. 
To locate this file, right-click on the Abaqus CAE start menu item, 
and choose "Open file location". 
This will likely take you to a shortcut. 
Repeat for that shortcut, and you should come to the 
:file:`launcher.bat`. Add the above code block to this file, 
before the call to :file:`ABQLauncher.exe`. 
