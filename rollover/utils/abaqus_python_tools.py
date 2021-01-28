from __future__ import print_function
import os, sys
from datetime import datetime

from abaqus import mdb
from abaqusConstants import *


def setup_log_file(log_file='abaqus_python.log'):
    """ Create a new log file, use at beginning to avoid appending to 
    old file. Not required, but makes log output more readable.
    
    :param log_file: path to log file
    :type log_file: str
    
    """
    
    if os.path.exists(log_file):
        os.remove(log_file)
    
    with open(log_file, 'w') as fid:
        fid.write('Abaqus log file. Created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
        

def log(message, log_file='abaqus_python.log'):
    """ Write log message to STDOUT and logfile. If STDOUT redirected
    by Abaqus, also write to shell (otherwise it can be hidden)
    
    :param message: The message to write to log file/stdout
    :type message: str
    
    :param log_file: Path to log file to append to. Created if non-existent.
    :type log_file: str
    
    :returns: None
    """
    
    if os.path.exists(log_file):
        with open(log_file, 'a') as fid:
            fid.write(message+'\n')
            print(message)  # Print 'message' to STDOUT
            if not sys.__stdout__ == sys.stdout:    # If redirected by abaqus, still write to shell
                sys.__stdout__.write(message + '\n')
    else:
        setup_log_file(log_file)
        log(message, log_file)


# General use functions
def create_model(model_name):
    """ Create a model, delete model if already existing in active mdb.
    
    :param model_name: Name of model to create/overwrite
    :type model_name: str
    
    :returns: The created model
    :rtype: Model object (Abaqus)
    
    """
    
    # Delete old model if exists
    if model_name in mdb.models:    
        del(mdb.models[model_name])
        
    return mdb.Model(name=model_name, modelType=STANDARD_EXPLICIT)