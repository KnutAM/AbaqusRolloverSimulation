import os

from abaqusGui import *
from plateDB import PlateDB
from caeExampleIcons import plateHoleData

###########################################################################
# Class definition
###########################################################################

class PlateForm(AFXForm):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, owner):

        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
                
        # Command
        #
        self.cmd = AFXGuiCommand(self, 'Plate', 'caeExamples')
        
        self.nameKw = AFXStringKeyword(self.cmd, 'name', TRUE)
        self.widthKw = AFXFloatKeyword(self.cmd, 'width', TRUE)
        self.heightKw = AFXFloatKeyword(self.cmd, 'height', TRUE)
        self.radiusKw = AFXFloatKeyword(self.cmd, 'radius', TRUE)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def getFirstDialog(self):

        return PlateDB(self)



doc_dir = '' # Should get the doc build dir

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
helpUrl = os.path.join(doc_dir, 'plugins/example.html')

pluginDesc = 'Example plugin for rollover simulation'

# Register a GUI plug-in in the Plug-ins menu.
#
toolset.registerGuiMenuButton(
    object=PlateForm(toolset), buttonText='Rollover|GUI Example...',
    kernelInitString='',
    version='1.0', author='Knut Andreas Meyer',
    applicableModules = ['Part', 'Property', 'Assembly', 'Step', 
        'Interaction', 'Load', 'Mesh', 'Job'],
    description=pluginDesc,
    helpUrl=helpUrl
)
    
# Register a GUI plug-in in a toolbox.
#
icon = FXXPMIcon(getAFXApp(), plateHoleData)
toolset.registerGuiToolButton('Examples', 
    object=PlateForm(toolset), buttonText='Rollover|GUI Example...',
    kernelInitString='', icon=icon,
    version='1.0', author='Knut Andreas Meyer',
    applicableModules = ['Part', 'Property', 'Assembly', 'Step', 
        'Interaction', 'Load', 'Mesh', 'Job'],
    description=pluginDesc,
    helpUrl=helpUrl
)
