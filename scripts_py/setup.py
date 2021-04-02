""" :file:`setup.py` sets up local adaptions by creating the following files 
that are ignored by git:

- :file:`rollover/local_paths.py`:
  This module contains the following variables:
    
    - :file:`rollover_repo_path`: Path to the git repository
    
    - :file:`data_path`: Path to the data folder (which will contain examples
      and user data
       
- :file:`abaqus_v6.env`:
  This file should be added either to the working directory of the 
  simulation, or to the user's home directory 
  (:file:`%HOME%` on Windows and :file:`~` on Linux)
  
- :file:`data/usub/usub_rollover.obj` or 
  :file:`data/usub/usub_rollover.o`: 
  Basic user subroutine required to run rollover simulation.

"""

from __future__ import print_function
import os, sys, shutil
import create_usub

# Fix to make FileNotFoundError available in Python 2 (a bit more general though...)
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


def main(argv):
    print('Running initial setup of rollover.')
    print('Use input argument 0 to supress compilation of subroutine')
    rollover_repo_path, data_path = create_local_paths()
    print('local path module, "local_paths.py", created')
    create_abaqus_env(rollover_repo_path)
    print('abaqus environment file, "abaqus_v6.env", created')
    compile = True
    if len(argv)>1:
        if int(argv[1]) == 0:
            compile = False
    if compile:
            print('compiling abaqus user subroutine')
            compile_default_usub(data_path)
            print('subroutine compilation completed')
    

def create_local_paths():
    this_path = os.path.dirname(os.path.abspath(__file__))
    rollover_repo_path = os.path.dirname(this_path)

    data_path = os.path.abspath(rollover_repo_path + '/data')
    usub_path = os.path.abspath(rollover_repo_path + '/usub')
    doc_path = os.path.abspath(rollover_repo_path + '/doc/build')
    
    data_path = data_path.replace('\\', '/')
    usub_path = usub_path.replace('\\', '/')
    doc_path = doc_path.replace('\\', '/')
    

    with open(rollover_repo_path + '/rollover/local_paths.py', 'w') as fid:
        fid.write('# Automatically generated module by ' + os.path.abspath(__file__) + '\n')
        fid.write('# Defines the local paths for the rollover library, this allows examples\n')
        fid.write('# to run without additional changes\n')
        fid.write('# This file should not be version controlled, ' + __file__ + ' is.\n\n')
        
        fid.write('# Path to top of repository\n')
        fid.write('rollover_repo_path = "' + rollover_repo_path + '"\n\n')
        
        fid.write('# Path to data folder (containing examples and user generated data)\n')
        fid.write('data_path = "' + data_path + '"\n\n')
        
        fid.write('# Path to user subroutine folder\n')
        fid.write('usub_path = "' + usub_path + '"\n\n')
        
        fid.write('# Path to documentation folder\n')
        fid.write('doc_path = "' + doc_path + '"\n\n')
    
    return rollover_repo_path, data_path
        

def create_abaqus_env(rollover_repo_path):
    rollover_path_spec = get_rollover_path_spec(rollover_repo_path)
    ifort_adaptation = get_ifort_adaptation()
    
    with open(rollover_repo_path + '/abaqus_v6.env', 'w') as fid:
        fid.write(rollover_path_spec)
        fid.write(ifort_adaptation)
    
    
def get_rollover_path_spec(rollover_repo_path):
    rollover_path_spec = ('import sys \n' 
                          + 'rollover_repo_path = "' + rollover_repo_path + '"\n'
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

    
def compile_default_usub(data_path):
    folder_list, file_list = create_usub.get_default_usubs()
    tmp_dir = create_usub.create_tmpdir(folder_list)
    os.chdir(tmp_dir)
    usub_file = create_usub.combine_usub_files(file_list)
    usub_ofile = create_usub.make_library(usub_file)
    os.chdir('..')
    usub_data_path = os.path.abspath(data_path + '/usub/')
    if not os.path.exists(usub_data_path):
        os.mkdir(usub_data_path)
    usub_ofile_name = 'usub_rollover.' + usub_ofile.split('.')[-1]
    try:
        shutil.copyfile(tmp_dir + '/' + usub_ofile,
                        usub_data_path + '/' + usub_ofile_name)
    except FileNotFoundError as e:
        print('Compilation failed, please see build.log file in ' + tmp_dir)
        raise e
    
    shutil.rmtree(tmp_dir)
    

if __name__ == '__main__':
    main(sys.argv)
