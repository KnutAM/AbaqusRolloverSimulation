from abaqusGui import getAFXApp, FXXPMIcon
#from rollover.icons import reload_icon
from rollover.local_paths import doc_path
import os


helpUrl = os.path.join(doc_path, 'plugins/substructure.html')

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

# Register a kernel plug-in in the Plug-ins menu.
#
toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='use_from_plugin()',
    buttonText='Rollover|Substructure|Use',
    version='1.0', author='Knut Andreas Meyer',
    description='Use rail substructure (with default name)',
    helpUrl=helpUrl
)

toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='gen_from_plugin()',
    buttonText='Rollover|Substructure|Generate',
    version='1.0', author='Knut Andreas Meyer',
    description='Generate and use rail substructure',
    helpUrl=helpUrl
)

toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='add_interface_pattern_plugin()',
    buttonText='Rollover|Substructure|Interface mesh pattern',
    version='1.0', author='Knut Andreas Meyer',
    description='Generate and use rail substructure',
    helpUrl=helpUrl
)
