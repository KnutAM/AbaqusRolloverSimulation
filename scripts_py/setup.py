""" Script to setup local adaptions, creates the following files that 
are ignored by git:

- `rollover/local_paths.py`
  This module contains the following variables:
    - `rollover_repo_path`: Path to the git repository
    - `data_path`: Path to the data folder (which will contain examples
       and user data
       
- `abaqus_v6.env`
  This file should be added either to the working directory of the 
  simulation, or to the user's home directory (%HOME% on Windows and ~ 
  on Linux)

"""

import os

def main():
    rollover_repo_path = create_local_paths()
    create_abaqus_env(rollover_repo_path)
    

def create_local_paths():
    this_path = os.path.dirname(os.path.abspath(__file__))
    rollover_repo_path = os.path.dirname(this_path)

    data_path = os.path.abspath(rollover_repo_path + '/data')
    usub_path = os.path.abspath(rollover_repo_path + '/usub')

    with open(rollover_repo_path + '/rollover/local_paths.py', 'w') as fid:
        fid.write('# Automatically generated module by ' + os.path.abspath(__file__) + '\n')
        fid.write('# Defines the local paths for the rollover library, this allows examples\n')
        fid.write('# to run without additional changes')
        fid.write('# This file should not be version controlled, ' + __file__ + ' is.\n\n')
        
        fid.write('# Path to top of repository\n')
        fid.write('rollover_repo_path = ' + rollover_repo_path + '\n\n')
        
        fid.write('# Path to data folder (containing examples and user generated data)\n')
        fid.write('data_path = ' + data_path + '\n\n')
        
        fid.write('# Path to user subroutine folder\n')
        fid.write('# usub_path = ' + usub_path + '\n\n')
    
    return rollover_repo_path
        

def create_abaqus_env(rollover_repo_path):
    rollover_path_spec = get_rollover_path_spec(rollover_repo_path)
    ifort_adaptation = get_ifort_adaptation()
    
    with open(rollover_repo_path + '/abaqus_v6.env', 'w') as fid:
        fid.write(rollover_path_spec)
        fid.write(ifort_adaptation)
    
    
    
def get_rollover_path_spec(rollover_repo_path):
    rollover_path_spec = ('import sys \n' 
                          + 'rollover_repo_path = ' + rollover_repo_path + '\n'
                          + 'if rollover_repo_path not in sys.path:\n'
                          + '    sys.path.append(rollover_repo_path)\n'
                          + 'del rollover_repo_path \n')
    return rollover_path_spec

    
def get_ifort_adaptation():
    if os.name == 'posix':  # Linux
        keyword_sign = '-'
    else:                   # Windows
        keyword_sign = '/'
    
    ifort_strs = get_shell_output('ifort ' + keyword_sign + 'logo').split()
    try:
        version = [int(n) for n in ifort_strs[ifort_strs.index('Version')+1].split('.')]
    except:
        try:
            version = [int(n) for n in input('Could not identify ifort version automatically, please give the version (e.g. 16.0.1)')]
        except:
            print('Could not read input of version')
            print('If your version > 16, you will have to add the '
                  + '"nostandard-realloc-lhs" compiler option to abaqus_v6.env yourself')
            version = None
    
    add_compile_option = ''
    if version is not None:
        if version[0] > 16:
            add_compile_option = ('compile_fortran.append("'
                                  + keyword_sign 
                                  + 'nostandard-realloc-lhs")')
    
    return add_compile_option
            
    
def get_shell_output(cmd):
    tmp_file = 'setup_output_tmp.tmp'
    os.system(cmd + ' > ' + tmp_file + ' 2>&1')
    with open(tmp_file, 'r') as fid:
        out_str = fid.read()
    os.remove(tmp_file)
    
    return out_str

    
if __name__ == '__main__':
    main()
