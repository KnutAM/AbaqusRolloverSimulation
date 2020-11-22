import sys, os, re

repo_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not repo_path in sys.path:
    sys.path.append(repo_path)
    
from rollover.utils import naming_mod as names

def main(argv):
	num_multiply = int(argv[1]) if len(argv) > 1 else 2
	inp_fname = argv[2] if len(argv) > 2 else 'rollover.inp'
		
	step_def_str, num_cycles = get_step_def_str(inp_fname)
	
	for n in range(1,num_multiply):
		step_def_str = increment_step_def_str(step_def_str, num_cycles)
		append_step_def_str_to_inp(inp_fname, step_def_str)
        
	
def get_step_def_str(inp_fname):
    step_def_str = ''
    start_appending = False
    num_cycles = 0
    with open(inp_fname, 'r') as inp:
        for line in inp:
            if line.startswith('*Step, name=' + names.get_step_rolling(2)):
                start_appending = True
            if start_appending:
                if not line.startswith('** '):
                    if line.startswith('*Step, name=return_'):
                        num_cycles = num_cycles + 1
                    step_def_str = step_def_str + line
    
    return step_def_str, num_cycles
    
    
def increment_step_def_str(step_def_str, num_cycles):
    # Compile regular expressions to identify new step definitions
    regex = re.compile('^\*Step, name=([\w]*)_([\d]*)', re.MULTILINE)
    
    # Write function to increment the cycle number
    def incr_str(re_match):
        str_parts = re_match.group().split('_')
        str_parts[-1] = str(int(str_parts[-1]) + num_cycles).zfill(5)
        return '_'.join(str_parts)
        
    step_def_str, num_repl = regex.subn(incr_str, step_def_str)
    
    if num_repl != 4*num_cycles:
        print('num_cycles: ', num_cycles)
        print('num_repl: ', num_repl)
        print('4*num_cycles: ', 4*num_cycles)
        print('something went wrong...')
    
    return step_def_str
    
    
def append_step_def_str_to_inp(inp_fname, step_def_str):
    with open(inp_fname, 'a') as inp:
        inp.write('\n' + step_def_str)
    

            
    
if __name__ == '__main__':
	main(sys.argv)
