import os, sys
from abaqusGui import *
from collections import OrderedDict
from rollover_gui_utils import PartDB, KwAdder


class WheelForm(AFXForm):

    def __init__(self, owner):

        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
        
        # Define form title/name
        self.title = 'Create wheel'
        
        # Define command to be called
        self.cmd = AFXGuiCommand(self, 'create_wheel', 'plugin_cmd')
        
        # Define keywords to be input arguments to function in self.cmd
        profile = ':/wheel_profiles/rs200_ro460_ri300_w60.sat'
        self.profile = {'kw': AFXStringKeyword(self.cmd, 'profile', 
                                               TRUE, 
                                               defaultValue=profile),
                        'label': 'wheel sketch file',
                        'pattern': 'Sketch files (*.sat)'}
        
        # Define in dictionary to be able to use loop to create text fields
        self.kw = OrderedDict() # Need to use OrderedDict to ensure that 
                                # the fields appear in the given order
        kwa = KwAdder(self.cmd, self.kw)
        
        kwa.add('wheel save folder: ', 'name', 'wheel_example')
        kwa.add('mesh: ', 'mesh', '5.0, 20.0')
        kwa.add('use quadratic: ', 'quadratic', 0)
        kwa.add('angle interval: ', 'ang_int', '-0.033, 0.167')
        kwa.add('x contact interval: ', 'x_int', '-10.0, 10.0')
        kwa.add('partition line y: ', 'partition_y', -454.0)
        
        
    def getFirstDialog(self):
        return PartDB(self)
 


