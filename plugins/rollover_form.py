import os, sys
from abaqusGui import *
from collections import OrderedDict
import rollover_gui_utils as rgu


class RolloverForm(AFXForm):

    def __init__(self, owner):

        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
        
        # Define form title/name
        self.title = 'Create wheel'
        
        # Define command to be called
        self.cmd = AFXGuiCommand(self, 'create_rollover', 'plugin_cmd')
        
        # Define keywords to be input arguments to function in self.cmd
        self.kw = OrderedDict() 
        self.settings = OrderedDict()
        kwa = rgu.KwAdder(self.cmd, self.kw)
        
        # Rail settings
        r = []
        r.append(kwa.add('.cae file: ', 'rail', ':/rails/rail_example.cae'))
        r.append(kwa.add('shadow extents: ', 'shadow', '15.0, 15.0'))
        r.append(kwa.add('use ref pt.: ', 'use_rp', 0))
        self.settings['rail'] = r[:]
        
        # Wheel settings
        w = []
        w.append(kwa.add('folder: ', 'wheel', ':/wheels/wheel_example'))
        w.append(kwa.add('translation: ', 'trans', '0.0, 460.0, 0.0'))
        w.append(kwa.add('stiffness: ', 'stiffness', 210.0e3))
        self.settings['wheel'] = w[:]
        
        # Contact settings
        c = []
        c.append(kwa.add('friction coeff: ', 'mu', 0.5))
        c.append(kwa.add('contact stiff: ', 'k_c', 1.e6))
        self.settings['contact'] = c[:]
        
        # Loading settings
        ls = []
        ls.append(kwa.add('initial depression: ', 'uz_init', 0.2))
        ls.append(kwa.add('time inbetween: ', 't_ib', 1.e-6))
        ls.append(kwa.add('inbetween max incr: ', 'n_inc_ib', 100))
        ls.append(kwa.add('rolling length: ', 'L_roll', 50.0))
        ls.append(kwa.add('rolling radius: ', 'R_roll', 920.0/2.0))
        ls.append(kwa.add('max increments: ', 'max_incr', 1000))
        ls.append(kwa.add('min increments: ', 'min_incr', 50))
        ls.append(kwa.add('num cycles: ', 'N', 1))
        ls.append(kwa.add('cycles spec: ', 'cycles', '1'))
        ls.append(kwa.add('wheel load: ', 'load', '150.0e3'))
        ls.append(kwa.add('speed: ', 'speed', '30.0e3'))
        ls.append(kwa.add('slip: ', 'slip', '0.01511'))
        ls.append(kwa.add('rail ext: ', 'rail_ext', '0.0'))
        self.settings['loading'] = ls[:]
        
        # Output settings table
        self.outp_table_head = ['name', 'set', 'variables', 'frequency',
                                'cycle']
        self.outp_table_kw = AFXTableKeyword(self.cmd, 'output_table', 
                                             TRUE)
        types = {0: AFXTABLE_TYPE_STRING, 1: AFXTABLE_TYPE_INT}
        for i, ti in enumerate([0, 0, 0, 1, 1]):
            self.outp_table_kw.setColumnType(i, types[ti])
                               
        
    def getFirstDialog(self):
        return RolloverDB(self)

class RolloverDB(AFXDataDialog):

    def __init__(self, form):

        # Construct the base class.
        AFXDataDialog.__init__(self, form, form.title, 
                               self.OK|self.CANCEL)
            
        fw = 50 # Field width for text input
        # Create alignment for widget
        TabBook = FXTabBook(p=self)
        tab = dict()
        vf = dict()
        va = dict()
        for title in form.settings:
            tab[title] = FXTabItem(p=TabBook, text=title)
            vf_opts = FRAME_RAISED|FRAME_THICK|LAYOUT_FILL_X
            vf[title] = FXVerticalFrame(TabBook, opts=vf_opts)        
            va[title] = AFXVerticalAligner(vf[title])
            for label in form.settings[title]:
                if title == 'rail' and label == '.cae file: ':
                    rgu.add_file_input(form, form.kw[label],
                                       'Model Database (*.cae)',
                                       aligner=va[title],
                                       label=label, fw=fw)
                elif title == 'wheel' and label == 'folder: ':
                    rgu.add_file_input(form, form.kw[label],
                                       'Folder (*)',
                                       aligner=va[title],
                                       label=label, fw=fw,
                                       fh_opts=AFXSELECTFILE_DIRECTORY)
                else:
                    AFXTextField(va[title], fw, label, 
                                 form.kw[label])
        
        # Create table input for output settings
        tab['output'] = FXTabItem(p=TabBook, text='output')
        vf_opts = FRAME_RAISED|FRAME_THICK|LAYOUT_FILL_X
        vf['output'] = FXVerticalFrame(TabBook, opts=vf_opts)  
        num_row = 2
        num_col = 6
        table = AFXTable(vf['output'], 
                         numVisRows=num_row, numVisColumns=num_col, 
                         numRows=num_row, numColumns=num_col, 
                         tgt= form.outp_table_kw, 
                         opts=AFXTABLE_EDITABLE|LAYOUT_FILL_X)
        table.setPopupOptions(AFXTable.POPUP_CUT
                              |AFXTable.POPUP_COPY
                              |AFXTable.POPUP_PASTE
                              |AFXTable.POPUP_INSERT_ROW
                              |AFXTable.POPUP_DELETE_ROW)
        table.setLeadingRows(1)
        table.setLeadingColumns(1)
        type = {0: AFXTable.TEXT, 1: AFXTable.INT}
        for i, it in enumerate([0, 0, 0, 1, 1]):
            table.setColumnWidth(i+1, 100)
            table.setColumnType(i+1, type[it])
        t_head = '\t'.join([head for head in form.outp_table_head])
        table.setLeadingRowLabels(t_head)
        table.setStretchableColumn(table.getNumColumns()-1)
        table.showHorizontalGrid(True)
        table.showVerticalGrid(True)
        

