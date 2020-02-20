# Kontaktmodell Rollen (2D und 3D)
#-------------------------------------------------------------------------------
# 2019-02-08: Adaption mit besseren zentralen Files fuer ABAQexcel
#-------------------------------------------------------------------------------
from abaqus import *
from abaqusConstants import *
from caeModules import *
import os, sys, shutil
import numpy as np

session.journalOptions.setValues(replayGeometry=COORDINATE,
                                 recoverGeometry=COORDINATE)
DIR0 = os.path.abspath('')
#sys.path.append('L:/Dokus_LKKV/001_Bibliothek/KKV-Scripts_SoftwareTools/Abaqus_PYscripts_Python_3/xls_py_abaqus-v1_0')
from func_rollmodell_2_3d import makeModel2D,makeModel3D
import Pickler

mm=0.001; MPa=1.e6; TOL = 1e-6

# allgemeine Funktionen --------------------------------------------------------

def make_dir(dir_name, if_change=0, if_clear=0):
    # wechselt in einen Unterordner
    dir_abs = os.path.abspath('')
    if os.path.exists(dir_name) == 0:
        os.mkdir(dir_name)
    else:
        if if_clear:
            shutil.rmtree(dir_name)
            os.mkdir(dir_name)
    dir1 = dir_abs + "//" + dir_name
    if if_change:
        os.chdir(dir1)
    return dir_abs

# Funktionen zum Modellaufbau --------------------------------------------------

def modell_erstellen(calc_dir, model_name = 'rechnung0', n_pr=2):
    #
    dir0 = make_dir(calc_dir, if_change=1)
    Mdb()
    #
    input_d = Pickler.load('input_model.dat')
    #
    dir_name = ''
    # Modell modell_erstellen
    abmess = input_d['Abmessungen']
    #
    # Reibwert
    mu = input_d['Friction coefficient']
    #
    if input_d['Geometrievariante'][0] == '3D':
        # Belastung
        if input_d['Belastung'][0] == 'slip':
            load = (input_d['Rolllaenge'], input_d['Normal load'] * 1000 / 2, 'a',
                    input_d['Belastung'][1], 0)
        else:
            load = (input_d['Rolllaenge'], input_d['Normal load'] * 1000 / 2, 'b',
                    0, input_d['Belastung'][1])
        #
        makeModel3D(dir_name,'run-cycle',input_d['Radius Rad'],input_d['Radius Schiene'],
                       abmess['length'],abmess['height'],abmess['depth'],
                       abmess['element length'],load,nCycles=int(input_d['Number Cycles']),
                       matName=input_d['Material variant'],
                       nPr=int(input_d['Anzahl Prozessoren']),
                       rad_rigid=input_d['ob Rad starr'],
                       mu=input_d['Friction coefficient'],
                       uy00=input_d['uy0'],
                       fullOut=input_d['ob full Output'],
                       ob_rad_starr=input_d['ob Rad starr'])
    else:
        # Belastung
        if input_d['Belastung'][0] == 'slip':
            load = (input_d['Rolllaenge'], input_d['Geometrievariante'][2], 'a',
                    input_d['Belastung'][1], 0)
        else:
            load = (input_d['Rolllaenge'], input_d['Geometrievariante'][2], 'b',
                    0, input_d['Belastung'][1])
        #
        makeModel2D(dir_name, 'run-cycle', input_d['Geometrievariante'][1], 0,
                   abmess['length'], abmess['height'], 0, abmess['element length'][:3],
                   load, nCycles=int(input_d['Number Cycles']), matName=input_d['Material variant'],
                   nPr=int(input_d['Anzahl Prozessoren']),biasS=abmess['element length'][-1],
                   rad_rigid=input_d['ob Rad starr'],
                   mu=input_d['Friction coefficient'],
                   fullOut=input_d['ob full Output'],
                   ob_rad_starr=input_d['ob Rad starr'],
                   elem_type=input_d['Geometrievariante'][3])
    os.chdir(dir0)
    return

# Modell aufrufen --------------------------------------------------------------
calc_dir = str(sys.argv[-1])
#calc_dir = 'calculations/Plastic_Rolls_roll'

# run in directory calc_dir
modell_erstellen(calc_dir)
