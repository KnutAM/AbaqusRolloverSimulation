[//]: # "To preview markdown file in Emacs type C-c C-c p"

# Abaqus Rollover Simulation
Python library to setup rollover simulation in Abaqus for CHARMEC

## Contributors
* Knut Andreas Meyer 
* Rostyslav Skrypnyk

## Project structure

The following top-level folders and file are provided

- `rollover`: The python library used to setup and run the Abaqus rollover simulations (imported, but not run directly)
- `scripts_abq`: Abaqus python scripts that are designed to be called as `abaqus cae noGUI=<script.py>`
- `scripts_py`: Python scripts that should be called by `python <script.py>`
- `usub`: Fortran code for user subroutines required for the rollover simulations
- `doc`: Documentation
- `tests`: ***To be completed*** 
- `data`: Folder containing user data (e.g. profile sketches). Everything in this folder, apart from example data, should be ignored by git.
- `abaqus_v6.env`: Abaqus environment file that allows the user to setup their local environment. See "Abaqus environment file".

## Running for the first time 

### Requirements
* Abaqus Standard setup to compile fortran user subroutines. Note special requirements below if ifort version higher than 16
* Python 2.7 or higher

### Steps
1. Create a new file in the `src/` directory named `user_settings.py` and copy the contents from `user_settings_example.py`
2. Run the python script `src/wheel_super_element/create_super_wheel.py`
3. This will a folder with files `uel.for`, `uel_coords.npy` and `uel_info.json` in the `super_wheels` folder 
5. Edit `user_settings.py` to update `super_wheel` to the name of the folder created in the previous step. 
6. Run `src/rollover/rollover_model.py` from Abaqus (i.e. `abaqus cae noGUI="<path_to_project_dir\src\rollover\rollover_model.py"`)

## Using material subroutines

To use a material subroutine see the material `chaboche_umat` in `user_settings_example.py` for inspiration. Furthermore, the variable the `material_model_folder` must  be set, pointing to a folder containing folders with sources for different material models. The field `'material_model'` must be set to  `'user'` and the field `'mpar'` must contain a dictionary with the following fields:

* `'nstatv'`: Give an int for how many state variables the material model requires

* `'src_folder'`: Give the name of the folder in `material_model_folder` containing a file named `umat.for`/`umat.f`. The folder must contain all required files such that calling `abaqus make library=umat` (or `umat.f` ) would work in that folder (This will not be done however, the content will be copied)

* `'user_mpar_array'`: A tuple containing the material parameter that should be supplied to the user material routine

### Abaqus environment file

`abaqus_v6.env`, *explain the addition of path!*

As Abaqus (up to at least 2020) is compiled with ifort 16.0 or lower, some new compiler features are not available. If you have a later compiler this can cause problems. One common problem is that automatic allocation of lhs assignments was introduced in ifort 17.0, and this will cause undefined symbol error when used with Abaqus. To circumvent this issue, it is possible to add a compiler option `nostandard-realloc-lhs` using the `abaqus_v6.env ` file. This file must be located either in your home directory or in the current working directory. An example of such a modification has been provided in this repository, but note that this file must be manually moved for it to have any effect. 

## Coding guidelines
All functions and modules should be documented with docstrings according to the Sphinx's autodoc format, see e.g. [Sphinx RTD Tutorial](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html). 

### PEP 8
The [PEP 8 standard](https://www.python.org/dev/peps/pep-0008) should be complied to, with the following exceptions:
- Line length up to 99 chars allowed (as opposed to 79 chars) (Note that docstrings or comments are limited to 72 chars)


### Inclusive language

#### Contact and constraint terminology

Traditionally master/slave are used to describe contact sides in finite elements, and this is still used by Abaqus. In the present project this terminology shall be avoided when possible (i.e., except when required by the Abaqus API). 

- Contact: Replace by primary/secondary
- Linear constraints: Replace by retained/constrained