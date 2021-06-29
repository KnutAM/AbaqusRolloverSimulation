# Abaqus Rollover Simulation
Documentation: [![Documentation Status](https://readthedocs.org/projects/abaqusrolloversimulation/badge/?version=latest&kill_cache=1)](https://abaqusrolloversimulation.readthedocs.io/en/latest/?badge=latest)

If you use this code in your work, please cite `Meyer, Knut Andreas, Rostyslav Skrypnyk, and Martin Pletz. 2021. “Efficient 3d Finite Element Modeling of Cyclic Elasto-Plastic Rolling Contact.” Tribology International 161: 107053. https://doi.org/10.1016/j.triboint.2021.107053.` (For latex, a [bib file](citation.bib) is available)

To clone the repository, use
`git clone --recurse-submodules https://github.com/KnutAM/AbaqusRolloverSimulation.git`

### Contributors
* Knut Andreas Meyer 
* Rostyslav Skrypnyk

### Project structure
The following top-level folders and file are provided
- `rollover`: The python library used to setup and run the Abaqus rollover simulations (imported, but not run directly)
- `scripts_abq`: Abaqus python scripts that are designed to be called as `abaqus cae noGUI=<script.py>`
- `scripts_py`: Python scripts that should be called by `python <script.py>`
- `usub`: Fortran code for user subroutines required for the rollover simulations (this relies on a submodule)
- `doc`: Documentation
- `data`: Folder containing user data (e.g. profile sketches). Everything in this folder, apart from example data, should be ignored by git.

### Requirements
* Abaqus Standard setup to compile fortran user subroutines. Note special requirements below if the `ifort` version higher than 16.
* Python 2.7 or higher.

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
