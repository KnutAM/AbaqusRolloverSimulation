import os, sys
from abaqusGui import *
from collections import OrderedDict

class RailDB(AFXDataDialog):

    def __init__(self, form):

        # Construct the base class.
        AFXDataDialog.__init__(self, form, 'Create rail', 
                               self.OK|self.CANCEL)
            
        AFXNote(self, 'This plugin creates a rail that can be ' 
                + 'modified for further use')
                      
        # Create alignment for widget
        hf = FXHorizontalFrame(self, LAYOUT_FILL_X, 0,0,0,0, 0,0,0,0)
        gb = FXGroupBox(hf, 'Parameters', LAYOUT_FILL_Y|FRAME_GROOVE)
        va = AFXVerticalAligner(gb)
        
        # Create file input
        fileHandler = DBFileHandler(form, form.profile['kw'], 
                                    form.profile['pattern'])
        va_hf = FXHorizontalFrame(va)
        AFXTextField(p=va_hf, ncols=12, labelText=form.profile['label'], 
                     tgt=form.profile['kw'], sel=0,
                     opts=AFXTEXTFIELD_STRING|LAYOUT_CENTER_Y)
        icon = afxGetIcon('fileOpen', AFX_ICON_SMALL )
        FXButton(p=va_hf, text='	Select File\nFrom Dialog', ic=icon, 
                 tgt=fileHandler, sel=AFXMode.ID_ACTIVATE,
                 opts=BUTTON_NORMAL|LAYOUT_CENTER_Y, 
                 x=0, y=0, w=0, h=0, pl=1, pr=1, pt=1, pb=1)
                 
        for label in form.kw:
            # For some (unknown?) reason, a tuple is created for each
            # item in form.kw using OrderedDict, hence we must take the
            # first item out, otherwise wrong datatype...
            AFXTextField(va, 12, label, form.kw[label][0], 0)
        
        gb = FXGroupBox(hf, 'Diagram', LAYOUT_FILL_Y|FRAME_GROOVE)
        # icon = FXXPMIcon(getAFXApp(), plateData)
        # FXLabel(gb, '', icon, pl=0, pr=0, pt=0, pb=0)


class DBFileHandler(FXObject):

    def __init__(self, form, form_kw, patterns='*'):
        self.form = form
        self.patterns = patterns
        self.patternTgt = AFXIntTarget(0)
        self.fileNameKw = form_kw
        self.readOnlyKw = AFXBoolKeyword(None, 'readOnly', AFXBoolKeyword.TRUE_FALSE)
        FXObject.__init__(self)
        FXMAPFUNC(self, SEL_COMMAND, AFXMode.ID_ACTIVATE, DBFileHandler.activate)

    def activate(self, sender, sel, ptr):
       fileDb = AFXFileSelectorDialog(getAFXApp().getAFXMainWindow(), 'Select a File',
           self.fileNameKw, self.readOnlyKw,
           AFXSELECTFILE_ANY, self.patterns, self.patternTgt)
       fileDb.setReadOnlyPatterns('*.odb')
       fileDb.create()
       fileDb.showModal()


class RailForm(AFXForm):

    def __init__(self, owner):

        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
                
        # Define command to be called
        self.cmd = AFXGuiCommand(self, 'create_rail', 'plugin_cmd')
        
        # Define keywords to be input arguments to function in self.cmd
        self.profile = {'kw': AFXStringKeyword(self.cmd, 'profile', TRUE, defaultValue=''),
                        'label': 'rail sketch file',
                        'pattern': 'Sketch files (*.sat)'}
        
        # Define in dictionary to be able to use loop to create text fields
        self.kw = OrderedDict() # Need to use OrderedDict to ensure that 
                                # the fields appear in the given order
        self.kw['rail cae name: '] = AFXStringKeyword(self.cmd, 'name', TRUE, defaultValue='RAIL'),
        self.kw['rail length: '] = AFXFloatKeyword(self.cmd, 'length', TRUE, defaultValue=50.0),
        self.kw['mesh size: '] = AFXFloatKeyword(self.cmd, 'mesh_size', TRUE, defaultValue=5.0),
        self.kw['r_xmin: '] = AFXFloatKeyword(self.cmd, 'r_x_min', TRUE, defaultValue=-10.0),
        self.kw['r_ymin: '] = AFXFloatKeyword(self.cmd, 'r_y_min', TRUE, defaultValue=-10.0),
        self.kw['r_xmax: '] = AFXFloatKeyword(self.cmd, 'r_x_max', TRUE, defaultValue=+10.0),
        self.kw['r_ymax: '] = AFXFloatKeyword(self.cmd, 'r_y_max', TRUE, defaultValue=+10.0),
        self.kw['r_x: '] = AFXFloatKeyword(self.cmd, 'r_x', TRUE, defaultValue=0.0),
        self.kw['r_y: '] = AFXFloatKeyword(self.cmd, 'r_y', TRUE, defaultValue=-1.0),
        self.kw['sym_sign: '] = AFXIntKeyword(self.cmd, 'sym_sign', TRUE, defaultValue=0),
        
    def getFirstDialog(self):
        return RailDB(self)



doc_dir = '' # Should get the doc build dir

toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
helpUrl = os.path.join(doc_dir, 'plugins/example.html')

pluginDesc = 'Create rail base file for further manipulation'
modules = ['Part', 'Property', 'Assembly', 'Step', 
           'Interaction', 'Load', 'Mesh', 'Job']
toolset.registerGuiMenuButton(
    object=RailForm(toolset), buttonText='Rollover|Create rail...',
    kernelInitString='from rollover import plugin_cmd',
    version='1.0', author='Knut Andreas Meyer',
    description=pluginDesc,
    helpUrl=helpUrl
)
    
toolset.registerGuiToolButton('Rollover', 
    object=RailForm(toolset), buttonText='Create rail',
    kernelInitString='from rollover import plugin_cmd', # icon=icon,
    version='1.0', author='Knut Andreas Meyer',
    description=pluginDesc,
    helpUrl=helpUrl
)

toolset.registerKernelMenuButton(
    moduleName='rollover.plugin_cmd', 
    functionName='periodicize_mesh()',
    buttonText='Rollover|Periodicize mesh',
    version='1.0', author='Knut Andreas Meyer',
    description='Attempt to make periodic mesh',
    helpUrl=helpUrl
)

toolset.registerKernelToolButton('Rollover', 
    moduleName='rollover.plugin_cmd', 
    functionName='periodicize_mesh()',
    buttonText='Periodicize',
    version='1.0', author='Knut Andreas Meyer',
    description='Attempt to make periodic mesh',
    helpUrl=helpUrl
)
