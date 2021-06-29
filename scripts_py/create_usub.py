""" The script :file:`create_usub.py` is used to compile user 
subroutines by combining multiple input sources.

The :file:`usub/usub_3d.for` and the contents of that folder are 
automatically added. 
On the script input, specify the path to additional fortran source code
containing the Abaqus user subroutine. All content of its folder will be
added to the temporary directory and the contents of the particular file
is added to the combined user subroutine file. 
Note the following restrictions:

- Only the files containing abaqus subroutines should be given, and 
  maximum one per folder. If you have multiple subroutines, combine 
  these in one file. The remaining files, that do not have abaqus 
  subroutines can be included via include statements. Hence, the req.
  for the compilation to work is that the given subroutine file would 
  compile on its own using 
  :command:`abaqus make library=<subroutine_file>`
- No files can have the same path relative the copied folder because the
  contents of the copied folders are put in the same temporary folder.
- No module names may overlap.

Example

You have a user material subroutine called :file:`umat.for`, that uses a 
module :command:`umat_mod` in :file:`umat_mod.f90`. 
These routines are located in :file:`C:/umats/my_special_material`. 
:file:`umat.for` should then have the statement 
:command:`include 'umat_mod.f90'` before 
:command:`subroutine umat(...)`. 
To compile this subroutine together with the required subroutines for 
rollover, call the present script from some folder on your computer as:

:command:`python <path_to_create_usub.py> C:/umats/my_special_material/umat.for`

"""
from __future__ import print_function
import os, shutil, sys, time

# Fix to make FileNotFoundError available in Python 2 (IOError a bit more general though...)
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


def main(argv):
    folder_list, file_list = get_default_usubs()
    for inparg in argv[1:]:
        file_list.append(os.path.basename(inparg))
        folder_list.append(os.path.dirname(inparg))
    
    tmp_dir = create_tmpdir(folder_list)
    os.chdir(tmp_dir)
    usub_file = combine_usub_files(file_list)
    usub_ofile = make_library(usub_file)
    os.chdir('..')
    try:
        shutil.copy(tmp_dir + '/' + usub_ofile, '.')
    except FileNotFoundError as e:
        print('Compilation failed, please see build.log file in ' + tmp_dir)
        raise e
    
    print('User subroutine sucessfully generated')
    
    
def get_default_usubs():
    """ Return the default user subroutines
    
    :returns: Two lists containing the default (required) subroutines
              for the rollover simulation to work.
    :rtype: list[ list[ str ] ]
    
    """
    
    this_dir = os.path.dirname(os.path.abspath(__file__))
    usub_dir = os.path.abspath(this_dir + '/../usub')
    usub_name = 'usub_3d.for'
    
    return [usub_dir], [usub_name]
    
    
def create_tmpdir(folder_list):
    """ Create a temporary directory named 'tmp_src_dir'.
    Given a list of folder, copy all their contents into the created
    folder while preserving the folder structure.
    
    :param folder_list: List of folders from whose content should be 
                        copied
    :type folder_list: list[ str ]
    
    :returns: Name of the created temporary directory
    :rtype: str
    
    """
    
    tmp_dir_name = 'tmp_src_dir'
    
    if os.path.exists(tmp_dir_name):
        shutil.rmtree(tmp_dir_name)
        
    os.mkdir(tmp_dir_name)
    
    for folder in folder_list:
        for item in os.listdir(folder):
            item_path = os.path.abspath(folder + '/' + item)
            if os.path.isdir(item_path):
                shutil.copytree(item_path, tmp_dir_name + '/' + item)
            else:
                shutil.copy(item_path, tmp_dir_name)
    
    return tmp_dir_name


def combine_usub_files(file_list):
    """ Combine the user subroutine files in file_list to one file. Any 
    `!DEC$ FREEFORM` in the files are commented and `!DEC$ FREEFORM` is
    added to the top of the file. Includes can still be used in these 
    files, so only files containing Abaqus subroutines should be in this
    list.
    
    :param file_list: List of files to be combined
    :type file_list: List[ str ]
    
    :returns: Name of the combined user subroutine file
    :rtype: str
    
    """
    
    combined_file_name = 'usubs_combined.for'
    with open(combined_file_name, 'w') as fid:
        fid.write('!DEC$ FREEFORM\n')
        for file in file_list:
            with open(file, 'r') as sub:
                sub_str = sub.read()
            sub_str = sub_str.replace('!DEC$ FREEFORM', '!!DEC$ FREEFORM')
            fid.write('\n! Contents from ' + file + '\n')
            fid.write(sub_str)
            
    return combined_file_name


def make_library(usub_file):
    """ Given a fortran source file, call abaqus make library to 
    generate the object file whose name will be returned. 
    
    :param usub_file: Name of the fortran source file to be compiled
    :type usub_file: str
    
    :returns: Name of the compiled object file
    :rtype: str
    
    """
    
    check_utils()
    
    base_name = usub_file.split('.')[0]
    
    # Make platform independent
    obj_suff = '.o' if os.name == 'posix' else '.obj'
    lib_suff = '.so' if os.name == 'posix' else '.dll'
    
    object_file = base_name + '-std' + obj_suff
    shared_lib = 'standardU' + lib_suff
    
    # Remove previously compiled files (pot. from copied dirs)
    # Otherwise compilation with fail.
    for file in [object_file, shared_lib]:
        if os.path.exists(file):
            os.remove(file)
    
    # Compile subroutine
    
    def run_compilation(abaqus_name):
        print('Compiling with "' + abaqus_name + '"')
        os.system(abaqus_name + ' make library=' + base_name + ' > build.log 2>&1')
    
    # Try to compile by calling "abaqus" first. 
    # We assume this to be the default if multiple versions are installed
    run_compilation('abaqus')
    
    # If the default did not work, try the latest available version 
    # starting from the current year +1 back untill 2016.
    year = int(time.strftime('%Y')) + 1
    min_year = 2016
    abq_user_cmd = None
    while not os.path.exists(object_file):
        run_compilation('abq' + str(year))
        year = year - 1
        if year < min_year:
            break
    
    # If none of the default names worked, 
    # let the user choose the correct name. 
    if not os.path.exists(object_file):
        abq_user_cmd = input('Could not find your abaqus installation. \n'
                             + 'Please input your abaqus command.\n'
                             + 'If you run a job with "abaqus job=<input_file>", ' 
                             + 'write "abaqus":\n')
        run_compilation(abq_user_cmd)
    
    return object_file


def check_utils():
    if not os.path.exists("utils/src"):
        print("Could not find fortran_utils")
        print("If you downloaded using zip-files, please ensure that the content of fortran_utils is copied to the usub/utils folder")
        print("If you used git, with '--recurse-submodules', this is a bug so please report an issue")
        raise FileNotFoundError("fortran_utils not found") 

    
if __name__ == '__main__':
    main(sys.argv)
