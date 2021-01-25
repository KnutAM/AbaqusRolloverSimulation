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
        
        kwa.add('wheel save folder: ', 'name', 'wheel')
        kwa.add('fine mesh: ', 'mesh_fine', 5.0)
        kwa.add('coarse mesh: ', 'mesh_coarse', 20.0)
        kwa.add('use quadratic: ', 'quadratic', 0)
        kwa.add('min angle: ', 'c_ang_min', -0.033)
        kwa.add('max angle: ', 'c_ang_max', +0.100)
        kwa.add('min x contact: ', 'c_x_min', -10.0)
        kwa.add('max x contact: ', 'c_x_max', +10.0)
        kwa.add('partition radius: ', 'partition_r', 454.0)
        
        
    def getFirstDialog(self):
        return PartDB(self)
 
 
doc_dir = '' # Should get the doc build dir

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
helpUrl = os.path.join(doc_dir, 'plugins/example.html')

pluginDesc = 'Create wheel super-element'

toolset.registerGuiMenuButton(
    object=WheelForm(toolset), buttonText='Rollover|Create wheel...',
    kernelInitString='from rollover import plugin_cmd',
    version='1.0', author='Knut Andreas Meyer',
    description=pluginDesc,
    helpUrl=helpUrl)
    
toolset.registerGuiToolButton('Rollover', 
    object=WheelForm(toolset), buttonText='Create wheel',
    kernelInitString='from rollover import plugin_cmd', # icon=icon,
    version='1.0', author='Knut Andreas Meyer',
    description=pluginDesc,
    helpUrl=helpUrl)

