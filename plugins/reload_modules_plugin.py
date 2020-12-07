from abaqusGui import getAFXApp, FXXPMIcon
from rollover.icons import reload_icon
from rollover.local_paths import doc_path
import os


helpUrl = os.path.join(doc_path, 'plugins/reload_modules.html')

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

# Register a kernel plug-in in the Plug-ins menu.
#
toolset.registerKernelMenuButton(
    moduleName='rollover.utils.reload_modules', functionName='execute()',
    buttonText='Rollover|Reload modules',
    version='1.0', author='Knut Andreas Meyer',
    description='Reload all loaded modules to update any changes',
    helpUrl=helpUrl
)

icon = FXXPMIcon(getAFXApp(), reload_icon)
toolset.registerKernelToolButton('Rollover', 
    moduleName='rollover.utils.reload_modules', functionName='execute()',
    buttonText='\tReload Modules', icon=icon,
    version='1.0', author='Knut Andreas Meyer',
    description='Reload all loaded modules to update any changes',
    helpUrl=helpUrl
)