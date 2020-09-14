[//]: # (To preview markdown file in Emacs type C-c C-c p)

# Abaqus Rollover Simulation
Script to setup rollover simulation in Abaqus for CHARMEC

Contributors

* Knut Andreas Meyer 

## Running for the first time 
### Requirements

* Abaqus Standard setup to compile fortran user subroutines

* Abaqus environment file setup to look for user subroutines in the current working directory (this can be done by editing/making abaqus_v6.env and adding the line usub_lib_dir='<path_to_working_directory>')

### Steps

1) Create a new file in the src/ directory named "user_settings.py" and copy the contents from "user_settings_example.py"

2) Run the script "src/wheel_super_element/create_super_wheel_element.py" from Abaqus

3) This will create files "uel.for" and "uel_coords.npy" in the Abaqus working directory. Copy these files to a folder you choose.

4) In this folder, call "abaqus make library=uel.for" (If linux, rename uel.for to uel.f)

5) Edit user_settings.py to update super_element_path to the folder containing the uel.for that you created previously. 

6) Run "src/rollover_model.py" from Abaqus
