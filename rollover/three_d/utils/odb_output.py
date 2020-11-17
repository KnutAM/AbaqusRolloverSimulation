"""This module is used to control the output to the Abaqus result 
(`.fil`) file

.. note:: Uses direct editing of input and should be called after all
          cae options have been set.

.. codeauthor:: Knut Andreas Meyer
"""

from __future__ import print_function

from abaqusConstants import *

from rollover.utils import naming_mod as names
from rollover.utils import inp_file_edit as inp_edit
from rollover.utils import abaqus_python_tools as apt

def add(the_model, field_output_requests, num_cycles):
    """Add the user specified field output requests. Default outputs are
    deleted. 
    
    :param the_model: The model to which the output requests will be 
                      added
    :type the_model: Model object (Abaqus)
    
    :param field_output_requests: A dictionary with field output 
                                  request specifications. Each field 
                                  should be a dictionary containing the 
                                  following fields:
                                  
                                  - `set`: Which set the output applies 
                                     to. Refers to sets in the rail 
                                     instance, except special sets:
                                     
                                     - 'FULL_MODEL': The entire model
                                     - 'WHEEL_RP': Wheel ctrl point
                                     
                                  - `var`: List of variables to save, 
                                     e.g. ('U', 'S')
                                  - `freq`: How often to output during 
                                    step. I.e. every incr=1. Set to -1 
                                    for only last increment.
                                  - `cycle`: How often to output cycles,
                                    i.e. 1 implies every cycle, 10 
                                    implies every 10th cycle, etc. 
    :type field_output_requests: dict
    
    :returns: None
    :rtype: None
    
    """
    
    assy = the_model.rootAssembly
    wheel_inst = assy.instances[names.wheel_inst]
    rail_inst = assy.instances[names.rail_inst]
    
    # Delete default outputs
    for fo in the_model.fieldOutputRequests.keys():
        del the_model.fieldOutputRequests[fo]
    for ho in the_model.historyOutputRequests.keys():
        del the_model.historyOutputRequests[ho]

    # Add user specified outputs
    for foname in field_output_requests:
        fout = field_output_requests[foname]
        if fout['set'] == 'FULL_MODEL':
            region = MODEL
        elif fout['set'] == 'WHEEL_RP':
            region = wheel_inst.sets[names.wheel_rp_set]
        else:
            region = rail_inst.sets[fout['set']]
        
        freq = LAST_INCREMENT if fout['freq']==-1 else fout['freq']
        
        fout_obj = the_model.FieldOutputRequest(createStepName=names.step1, name=foname,
                                                    frequency=freq, variables=fout['var'],
                                                    region=region)
        
        if fout['cycle'] > 1:
            fout_obj.deactivate(names.get_step_return(2))
            prev_step_deactive = names.get_step_return(2)
            prev_step_active = names.step1
            for cnr in range(1, num_cycles+1, fout['cycle'])[1:]:
                fout_obj = the_model.FieldOutputRequest(name=foname + names.cycle_str(cnr),
                                                        objectToCopy=fout_obj)
                fout_obj.reset(prev_step_deactive)
                fout_obj.move(fromStepName=prev_step_active, toStepName=names.get_step_rolling(cnr))
                try:
                    fout_obj.deactivate(names.get_step_return(cnr+1))
                except:
                    pass    # This is ok if it is the last cycle, then no subsequent step exists
                
                prev_step_active = names.get_step_rolling(cnr)
                prev_step_deactive = names.get_step_return(cnr+1)