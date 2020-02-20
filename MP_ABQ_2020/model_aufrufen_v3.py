# Ausprobieren: Excel Datein reinladen / rausschreiben
# MP, 2018-02-08; v3: 2018-11-07

import os, pickle, xlrd, shutil
from shutil import copyfile
#from fit_model_data import fit_model_data
import numpy as np

DIR0 = os.path.abspath('')

# die Funktionen
# ----------------------------------------------------------------------------

def make_dir(dir_name, if_change=0, if_clear=0):
    # wechselt in einen Unterordner
    dir_abs = os.path.abspath('')
    if os.path.exists(dir_name) == 0:
        os.mkdir(dir_name)
    else:
        if if_clear:
            # does not work if not empty
            shutil.rmtree(dir_name)
            os.mkdir(dir_name)
    dir1 = dir_abs + "//" + dir_name
    if if_change:
        os.chdir(dir1)
    return dir_abs

def delete_temp_files():
    # temporaere Dateien loeschen
    temp_files = [i for i in os.listdir(DIR0) if '.rec' in i or '.rpy' in i or
                  '.dmp' in i or '.tmp' in i]# or i == 'input_model.dat']
    for file_name in temp_files:
        os.remove(file_name)
    return

def print_line(str_print='',if_3=0,n_tot=79,if_first=0):
    if if_first:
        str_print1 = str_print + ' (c) KKV, Leoben, 2018'
    else:
        str_print1 = str_print
    if str_print1 == '':
        print('-'*n_tot)
        return
    n_sides = (n_tot - len(str_print1) - 2)/2.
    if if_3:
        print('-'*n_tot)
    if n_sides%2 == 0:
        n_sides = int(n_sides)
        print('-'*n_sides+' '+str_print1.upper()+' '+'-'*n_sides)
    else:
        n_sides = int(n_sides)
        print('-'*n_sides+' '+str_print1.upper()+' '+'-'*n_sides)
    if if_3:
         print('-'*n_tot)
    return

def get_xls(dir_xls):
    xls_list = [i for i in os.listdir(dir_xls) if '.xlsx' in i and
                '~' not in i]
    if len(xls_list) == 1:
        return xls_list[0]
    else:
        k = 1
        for i in xls_list:
            print(str(k)+' '+i)
            k += 1
        i_xls = int(input('Nummer von xlsx File (0:beenden): '))
        if i_xls == 0:
            return 0
        else:
            return xls_list[i_xls - 1]

def get_dic_val(dic0, key_list):
    # Liste von Inizes uebergeben:
    # aus dict das auswaelen
    val_temp = dic0
    key_i = 0
    while type(val_temp) in [dict, list]:
        val_temp = val_temp[key_list[key_i]]
        key_i += 1
    return val_temp

def nested_set(dic, keys, value, create_missing=True):
    d = dic
    for key in keys[:-1]:
        if key in d:
            d = d[key]
        elif create_missing:
            d = d.setdefault(key, {})
        else:
            return dic
    if keys[-1] in d or create_missing:
        d[keys[-1]] = value
    return dic

def make_dic_name(par_list,val_list):
    def make_dir_str(key):
        if type(key) != list:
            return [key.replace(' ','_')]
        else:
            return ['--'.join([str(i).replace(' ','_') for i in key])]
    #
    par_list_str = [make_dir_str(par_i)[0] for par_i in par_list]
    #print(par_list_str)
    val_list_str = [str(round(val_i,3)).replace('.','_') for val_i in val_list]
    #print(val_list_str)
    return '___'.join([i_str+'__'+j_str for i_str,j_str in
                      zip(par_list_str,val_list_str)])

def make_dict_from_xls(file_name):
    # xls laden und auslesen
    def drop_brac(str0):
        return str(str0.split(' (')[0])
    # die Werte bekommen (Scalar oder List)
    def get_values(ws, n_line, i0=1):
        def make_str(x):
            # make normal string, if unicode
            try:
                #UNICODE_EXISTS = bool(type(unicode))
                if type(x) == unicode:
                    return str(x)
                else:
                    return x
            except NameError:
                return x
        #
        list0 = [ws.cell_value(n_line, j) for j in
                 range(i0, len(ws.row(n_line)))]
        list0 = [make_str(i) for i in list0 if i != '']
        if len(list0) == 1:
            return list0[0]
        else:
            return list0
    # schauen, ob 'X' am Anfang oder '&' drinnen
    def check_x(val):
        if '&' in str(val):
            if_var = 1
        else:
            if_var = 0
        #
        if str(val)[0] == 'X' or str(val)[0] == 'x':
            print('gfunden!')
            return float(val[1:].replace(',','.')),1,if_var
        else:
            return val,0,if_var
    #
    workbook = xlrd.open_workbook(file_name)
    ws = workbook.sheet_by_index(0)
    # das dictionary der Angaben erstellen
    input_d = {}
    # neue Variante, Schleife
    for i in range(2, ws.nrows):
        if not ws.cell_value(i, 0) == '':
            if i < ws.nrows-1:
                if ws.cell_value(i+1, 0) == '' and ws.cell_value(i+1, 1) != '':
                    # ws.cell_value(i, 1) == '':
                    str_sub = str(ws.cell_value(i, 0))
                    print(str_sub,type(str_sub))
                    input_d[str_sub] = {}
                else:
                    input_d[drop_brac(ws.cell_value(i, 0))] = get_values(ws, i)
            else:
                input_d[drop_brac(ws.cell_value(i, 0))] = get_values(ws, i)
        else:
            input_d[str_sub][drop_brac(ws.cell_value(i, 1))] = get_values(ws, i, 2)
    #
    # Liste zum Optimieren (opt_list) und Liste zum variieren (var_list)
    opt_list = []
    var_list = []
    # Die Optimierungssachen finden
    for key,val in input_d.items():
        if type(val) == list:
            for i,val_i in enumerate(val):
                val_cor,if_cor,if_var = check_x(val_i)
                if if_cor == 1:
                    opt_list += [[key,i]]
                    input_d[key][i] = val_cor
                if if_var == 1:
                    var_list += [[key,i]]
        elif type(val) == dict:
            for key_l,val_l in val.items():
                if type(val_l) == list:
                    for i,val_i in enumerate(val_l):
                        val_cor,if_cor,if_var = check_x(val_i)
                        if if_cor == 1:
                            opt_list += [[key,key_l,i]]
                            input_d[key][key_l][i] = val_cor
                        if if_var == 1:
                            var_list += [[key,key_l,i]]
                else:
                    val_cor,if_cor,if_var = check_x(val_l)
                    if if_cor == 1:
                        opt_list += [[key,key_l]]
                        input_d[key][key_l] = val_cor
                    if if_var == 1:
                        var_list += [[key,key_l]]
        else:
            val_cor,if_cor,if_var = check_x(val)
            if if_cor == 1:
                opt_list += [[key]]
                input_d[key] = val_cor
            if if_var == 1:
                var_list += [[key]]
    #
    # Ausgabe zum Anschauen
    print_line('ABAQEXCEL',1, if_first=1)
    print_line('excel input',1)
    for i, j in input_d.items():
        print(str(i)+': '+str(j))
    print_line('varied parameters',1)
    return input_d, opt_list, var_list

def run_abaqus_file(dir_run,input_d,opt_list=[]):
        # Angabefile fuer ABAQUS Modell
        with open(dir_run+'/input_model.dat', 'wb') as f:
            pickle.dump(input_d, f, protocol=2)
        # Abaqus Starten (noch machen: Optimieren!!!)
        if input_d['run/evaluate'] == 'run (CAE)' and opt_list == []:
            os.system('abaqus cae script='+input_d['model file']+' -- '+dir_run)
        elif ((input_d['run/evaluate'] == 'run (background)'or
              'inp' in input_d['run/evaluate']) and opt_list == []):
            os.system('abaqus cae noGUI='+input_d['model file']+' -- '+dir_run)
        elif opt_list != []:
            fit_model_data(var_name)

def run_xls_input(file_name):
    # xls laden und auslesen
    input_d, opt_list, var_list = make_dict_from_xls(file_name)
    var_name = input_d['Variantenname']
    print('varied parameter list: '+str(var_list))
    print('optimization list: '+str(opt_list))
    #raise ValueError
    #
    make_dir('calculations')
    if input_d['run/evaluate'] != 'evaluate':
        make_dir('calculations/'+var_name, if_clear=1)
        shutil.copyfile(file_name, 'calculations/'+var_name+'/_Angaben_'+var_name+'.xlsx')
    # --------------------------------------------------
    # wenn meherere Varianten gerechnet werden sollen
    if var_list != []:
        # alle moeglichkeiten: z.B. ['Lochliste','r',2]
        #string_var = get_dic_val(input_d, var_prop)
        #if ',' not in get_dic_val(input_d, var_prop):
        var_dic = [np.linspace(*[float(i) for i in
                   get_dic_val(input_d, var_prop).replace(',','.').split('&')])
                   for var_prop in var_list]
        #
        #print('debug line, var_dic: ',var_dic)
        # die Parameter-Varianten erstellen
        # ----------------------------------------------------------------------
        def make_var_list(dic_var):
            if len(dic_var) > 1:
                par_grid = np.meshgrid(*dic_var)
                #print('debug par_grid: ',par_grid)
                var_list = zip(*tuple([par_i.ravel() for par_i in par_grid]))
                #var_list = zip(*tuple([float(par_i.ravel()) for par_i in par_grid]))
            else:
                var_list = [[float(val)] for val in dic_var[0]]
            return var_list
        #
        varianten_list = make_var_list(var_dic)
        # Export the Variant List
        # extra in dict:
        dict_out = {}
        dict_out['par_name_list'] = var_list
        dict_out['load_case_list'] = varianten_list
        dict_out['dir_list'] = [make_dic_name(var_list,val_i) for val_i in varianten_list]
        with open('calculations/'+var_name+'/load_cases_dict.dat','wb') as f:
            pickle.dump(dict_out, f, protocol=2)
        #
        print_line('load cases')
        print('varianten_list ('+str(len(varianten_list))+' Varianten)')
        print(varianten_list)
        if'run' in input_d['run/evaluate']:
            print_line('run in abaqus',1)
        # ----------------------------------------------------------------------
        for val_i in varianten_list:
            # + special item for subdir
            str_temp = make_dic_name(var_list,val_i)
            #
            dir_temp = 'calculations/'+var_name+'/'+str_temp
            make_dir(dir_temp)
            input_d_temp = input_d
            for i_set in range(len(var_list)):
                input_d_temp = nested_set(input_d_temp, var_list[i_set],
                                          val_i[i_set], 1)
            #
            # Versuch in Funktionen
            run_abaqus_file(dir_temp,input_d_temp,opt_list=[])
    else:
        if 'run' in input_d['run/evaluate']:
            print_line('computations in abaqus',1)
        run_abaqus_file('calculations/'+input_d['Variantenname'],
                        input_d,opt_list=opt_list)
    return input_d

# -----------------------------------------------------------------------------

def run_xls_file():
    # Name der xls-Datei
    file_name = get_xls(DIR0)
    # Angaben laden und Modell erstellen
    if file_name != 0:
        input_d = run_xls_input(file_name)
        # Auswerten
        if input_d['run/evaluate'] != 'write inp':
            if '.py' in input_d['evaluation file']:
                print_line('model evaluation',1)
                os.system('python '+input_d['evaluation file']+' '+
                          'calculations/'+input_d['Variantenname'])
        delete_temp_files()

if __name__ == '__main__':
    run_xls_file()
