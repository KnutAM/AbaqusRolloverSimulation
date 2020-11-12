"""This module is used to control the output to the Abaqus result 
(`.fil`) file

.. note:: Uses direct editing of input and should be called after all
          cae options have been set.

.. codeauthor:: Knut Andreas Meyer
"""

from __future__ import print_function

from rollover.utils import naming_mod as names
from rollover.utils import inp_file_edit as inp_edit

def add_fil_output(the_model, num_cycles):
    
    assy = the_model.rootAssembly
    if assy.isOutOfDate:
        assy.regenerate()
    
    kwb = the_model.keywordBlock
    
    rail_rp = names.rail_rp_set if names.rail_rp_set in assy.sets.keys() else None
    
    # Setup output after first rollover
    add_output(kwb, 'COORD, U', names.get_step_rolling(1), rail_rp)
    
    
    for cycle_nr in range(1,num_cycles):
        add_output(kwb, '', names.get_step_return(cycle_nr), rail_rp)
        add_output(kwb, 'U', names.get_step_rolling(cycle_nr), rail_rp)
        
        
def add_output(kwb, varstr, step_name, rail_rp=None):
    
    wheel_cn_set = names.wheel_inst + '.' + names.wheel_contact_nodes
    wheel_rp_set = names.wheel_inst + '.' + names.wheel_rp_set
    
    sets = [wheel_cn_set, wheel_rp_set]
    if rail_rp is not None:
        sets.append(rail_rp)
    
    for set in sets:
        add_str = get_node_file_output_str(set, varstr)
        inp_edit.add_at_end_of_cat(kwb, add_str, category='Step', name=step_name)
    
    
    
def get_node_file_output_str(nset, varstr, frequency=99999999):
    output_str = ('*NODE FILE, NSET=' + nset + 
                  ', FREQUENCY=%0.0f \n'
                  + varstr) % (frequency)
    return output_str