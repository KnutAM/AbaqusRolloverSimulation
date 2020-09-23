[//]: # "To preview markdown file in Emacs type C-c C-c p"

# Abaqus Rollover Simulation
Script to setup rollover simulation in Abaqus for CHARMEC

## Contributors
* Knut Andreas Meyer 
* Rostyslav Skrypnyk

## Running for the first time 
### Requirements
* Abaqus Standard setup to compile fortran user subroutines
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

