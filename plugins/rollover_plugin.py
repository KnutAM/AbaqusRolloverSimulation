import os, sys

from abaqusGui import getAFXApp, FXXPMIcon
from collections import OrderedDict
from rollover.plugins.rail_form import RailForm
from rollover.plugins.wheel_form import WheelForm
from rollover.plugins.rollover_form import RolloverForm
from rollover.plugins import icons as ic

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()

# Common options
doc_dir = '' # Should get the doc build dir
ver = '1.0'
author = 'Knut Andreas Meyer'

# Create rail
pluginDesc = 'Create rail base file for further manipulation'
helpUrl = os.path.join(doc_dir, 'plugins/example.html')
icon = FXXPMIcon(getAFXApp(), ic.rail)

toolset.registerGuiMenuButton(
    buttonText='Rollover|Create rail...',
    object=RailForm(toolset), 
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)
    
toolset.registerGuiToolButton('Rollover', 
    buttonText='\tCreate rail', icon=icon,
    object=RailForm(toolset), 
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

# Create wheel
pluginDesc = 'Create wheel super-element'
helpUrl = os.path.join(doc_dir, 'plugins/example.html')
icon = FXXPMIcon(getAFXApp(), ic.wheel)

toolset.registerGuiMenuButton(
    object=WheelForm(toolset), buttonText='Rollover|Create wheel...',
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)
    
toolset.registerGuiToolButton('Rollover', 
    buttonText='\tCreate wheel', icon=icon,
    object=WheelForm(toolset), 
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

# Create rollover
pluginDesc = 'Create rollover simulation'
helpUrl = os.path.join(doc_dir, 'plugins/example.html')
icon = FXXPMIcon(getAFXApp(), ic.rollover)

toolset.registerGuiMenuButton(
    object=RolloverForm(toolset), 
    buttonText='Rollover|Setup simulation...',
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)
    
toolset.registerGuiToolButton('Rollover', icon=icon,
    object=RolloverForm(toolset), buttonText='\tSetup simulation',
    kernelInitString='from rollover.plugins import commands',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

# Make rail mesh periodic
pluginDesc = 'Attempt to make periodic mesh'
helpUrl = os.path.join(doc_dir, 'plugins/example.html')
icon = FXXPMIcon(getAFXApp(), ic.periodize)

toolset.registerKernelMenuButton(
    moduleName='rollover.plugins.commands', 
    functionName='periodicize_mesh()',
    buttonText='Rollover|Tools|Periodize mesh',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

toolset.registerKernelToolButton('Rollover', 
    moduleName='rollover.plugins.commands', 
    functionName='periodicize_mesh()',
    buttonText='\tMake mesh periodic', icon=icon,
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)
    
# Reload modules
pluginDesc = 'Reload all loaded modules to update any changes'
helpUrl = os.path.join(doc_dir, 'plugins/reload_modules.html')
icon = FXXPMIcon(getAFXApp(), ic.reload)

toolset.registerKernelMenuButton(
    moduleName='rollover.utils.reload_modules', 
    functionName='execute()',
    buttonText='Rollover|Tools|Reload modules',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

toolset.registerKernelToolButton('Rollover', 
    moduleName='rollover.utils.reload_modules', 
    functionName='execute()',
    buttonText='\tReload Modules', icon=icon,
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)


# Substructure
helpUrl = os.path.join(doc_dir, 'plugins/substructure.html')
icon = None

pluginDesc = 'Use rail substructure (with default name)'
toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='use_from_plugin()',
    buttonText='Rollover|Substructure|Use',
    version='1.0', author='Knut Andreas Meyer',
    description='Use rail substructure (with default name)',
    helpUrl=helpUrl
)

pluginDesc = 'Generate rail substructure'
toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='gen_from_plugin()',
    buttonText='Rollover|Substructure|Generate',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)

pluginDesc = 'Add interface from substructure'
toolset.registerKernelMenuButton(
    moduleName='rollover.three_d.rail.substructure', 
    functionName='add_interface_pattern_plugin()',
    buttonText='Rollover|Substructure|Interface mesh pattern',
    version=ver, author=author, description=pluginDesc, helpUrl=helpUrl)
