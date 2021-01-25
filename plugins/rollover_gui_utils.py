import os, sys
from abaqusGui import *
from collections import OrderedDict
 
class KwAdder():
    """ Class to add AFX?Keyword items to a given dictionary.
    Usage
    cmd = AFXGuiCommand(...)
    kw = OrderedDict()
    kwa = KwAdder(cmd, kw)
    kwa.add(key, label, default)  # Add AFX?Keyword to kw, with label
                                  # or variable name from label, and of
                                  # type given by default's datatype
    """
    
    def __init__(self, cmd, kw_dict):
        """
        param cmd: The command for the AFXGui
        type cmd: AFXGuiCommand
        
        param kw_dict: Dictionary in which to put the AFX?Keywords
        type kw_dict: OrderedDict
        
        :returns: Instance of KwAdder class
        :rtype: KwAdder
        
        """
        self.cmd = cmd
        self.kw = kw_dict
        
    def add(self, key, label, default):
        """ Add key in self.kw with entry AFX?Keyword which has variable
        name from label and ? is determined by the type of default.
        
        :param key: dictionary key
        :type key: str
        
        :param label: The label to use in AFX?Keyword, which will 
                      correspond to argument name in function called by
                      self.cmd
        :type label: str
        
        :param default: The default value for given entry
        :type default: float, int, or str
        
        :returns: None
        """
        
        if isinstance(default, float):
            self.kw[key] = AFXFloatKeyword(self.cmd, label, TRUE, 
                                           defaultValue=default)
        elif isinstance(default, int):
            self.kw[key] = AFXIntKeyword(self.cmd, label, TRUE, 
                                         defaultValue=default)
        elif isinstance(default, str):
            self.kw[key] = AFXStringKeyword(self.cmd, label, TRUE,
                                            defaultValue=default)
        else:
            raise ValueError('AFX?Keyword not supported for type'
                             + type(default))
 
class PartDB(AFXDataDialog):

    def __init__(self, form):

        # Construct the base class.
        AFXDataDialog.__init__(self, form, form.title, 
                               self.OK|self.CANCEL)
            
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
            AFXTextField(va, 12, label, form.kw[label], 0)
        
        # gb = FXGroupBox(hf, 'Diagram', LAYOUT_FILL_Y|FRAME_GROOVE)


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