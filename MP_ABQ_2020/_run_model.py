# Pakete aus Netzwerkfolder, Modell & Co lokal

import sys

dir_name = 'L:/Dokus_LKKV/001_Bibliothek/Scripts_SoftwareTools/Abaqus_PYscripts_Python_3/xls_py_abaqus-v1_0'
sys.path.append(dir_name)

from model_aufrufen_v3 import run_xls_file

run_xls_file()
