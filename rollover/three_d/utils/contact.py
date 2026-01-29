"""Module to setup the rail-wheel contact

.. codeauthor:: Knut Andreas Meyer
"""

from __future__ import print_function

from abaqusConstants import *
import interaction

from rollover.utils import naming_mod as names

def setup(the_model, contact_stiffness=1.e6, 
          friction_coefficient=None, elastic_slip_fraction=0.005):
    """Add a contact property and a surface-to-surface contact in 
    `the_model` according to the given settings.
    
    :param the_model: The model to which the contact settings should be
                      applied
    :type the_model: Model object (Abaqus)

    :param contact_stiffness: The stiffness used in the normal penalty 
                              formulation. 
    :type contact_stiffness: float

    :param friction_coefficient: The friction coefficient for the
                                 tangential behavior. If none, no 
                                 tangential behavior will be defined and
                                 the contact will be frictionless .
    :type friction_coefficient: float

    :param elastic_slip_fraction: The allowed elastic tangential slip.
                                  This will adjust the penalty stiffness
                                  for the tangential contact. 
    :type elastic_slip_fraction: float
    
    :returns: None
    :rtype: None

    """
    
    int_prop = the_model.ContactProperty('InteractionProperty')
    
    int_prop.NormalBehavior(pressureOverclosure=LINEAR, contactStiffness=contact_stiffness)
                            
    int_prop.TangentialBehavior(formulation=PENALTY, table=((friction_coefficient, ), ),
                                maximumElasticSlip=FRACTION, fraction=elastic_slip_fraction)
    
    rail_inst = the_model.rootAssembly.instances[names.rail_inst]
    wheel_inst = the_model.rootAssembly.instances[names.wheel_inst]
    
    the_model.SurfaceToSurfaceContactStd(name='RailWheelContact', createStepName=names.step0, 
                                         main=rail_inst.surfaces[names.rail_full_contact_surf],
                                         secondary=wheel_inst.surfaces[names.wheel_contact_surf], 
                                         sliding=FINITE, interactionProperty='InteractionProperty')
    
