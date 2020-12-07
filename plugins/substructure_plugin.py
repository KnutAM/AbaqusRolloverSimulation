from abaqusGui import getAFXApp, FXXPMIcon
#from rollover.icons import reload_icon
from rollover.local_paths import doc_path
import os


helpUrl = os.path.join(doc_path, 'plugins/substructure.html')

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

# Register a kernel plug-in in the Plug-ins menu.
#
toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', functionName='use_on_current()',
    buttonText='Rollover|Substructure (use)',
    version='1.0', author='Knut Andreas Meyer',
    description='Use rail substructure (with default name)',
    helpUrl=helpUrl
)

toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', functionName='gen_on_current()',
    buttonText='Rollover|Substructure (generate)',
    version='1.0', author='Knut Andreas Meyer',
    description='Generate and use rail substructure',
    helpUrl=helpUrl
)