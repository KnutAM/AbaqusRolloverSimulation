from __future__ import print_function
import os, sys
from datetime import datetime

# Make output to log to 
def setup_log_file(log_file='abaqus_python.log'):
    if os.path.exists(log_file):
        os.remove(log_file)
    
    with open(log_file, 'w') as fid:
        fid.write('Abaqus log file. Created ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
        

def log(message, log_file='abaqus_python.log'):
    if os.path.exists(log_file):
        with open(log_file, 'a') as fid:
            fid.write(message+'\n')
            print(message)  # Print 'message' to STDOUT
            if not sys.__stdout__ == sys.stdout:    # If redirected by abaqus, still write to shell
                sys.__stdout__.write(message + '\n')
    else:
        setup_log_file(log_file)
        log(message, log_file)
