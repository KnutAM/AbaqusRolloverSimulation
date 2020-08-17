def print_message(message, log_file='abaqus_python.log'):
    if os.path.exists(log_file):
        f = open(log_file,'a')
    else:
        f = open(log_file,'w')
        
    f.write(message+'\n')
    f.close()
    print message  # Print 'message' to STDOUT