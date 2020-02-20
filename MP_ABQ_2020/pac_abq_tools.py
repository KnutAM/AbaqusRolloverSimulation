######### Funktionen zum Auswaehlen #####################
# Version 0.0: mpl, 2016-04-23
# Version 0.1: mpl, 2016-05-02, geht mit kontaktmodell-Allgemein

import math
from abaqus import *
from abaqusConstants import *
from caeModules import *
import time
import numpy as np

DIR0 = os.path.abspath('')
TOL = 1.e-4

session.journalOptions.setValues(replayGeometry=COORDINATE,
                                 recoverGeometry=COORDINATE)

# allgemeine Funktionen --------------------------------------------------------

def changeDir(folderN):
    """ in Unterordner wechseln """
    import os
    dir0 = os.path.abspath('')
    if (os.path.exists(folderN) == 0):
        os.mkdir(folderN)
    dir1 = dir0 + "//" + folderN
    # dir1=dir0+"\\"+folderN
    os.chdir(dir1)
    return dir0

def print_cmd(string):
    print >> sys.__stdout__,string

def remove_files(dir0,type_list=('.com','.sim','.prt','.msg',
                                 '.log','.rec')):
    # alle Files im Ordner
    #print_cmd(dir0)
    file_list = [i for i in os.listdir(dir0) if '.' in i]
    # zahlen-Types
    zahlen_list = tuple('.'+str(i) for i in range(1,21))
    # relevante files auswaehlen
    for file_name in file_list:
        if '.'+file_name.split('.')[-1] in (type_list + zahlen_list):
            try:
                os.remove(file_name)
            except:
                print_cmd('File '+file_name+' konnte nicht geloescht werden!')
    return

def reset_model(model_name):
    # resets the model with modelN as Name
    Mdb()
    model = mdb.Model(modelType=STANDARD_EXPLICIT, name=model_name)
    del mdb.models["Model-1"]
    return model

def __wait_for_job(job_name,interval_print=5):
    print_cmd(job_name)
    while True:
        time.sleep(interval_print)
        if os.path.exists(job_name+'.lck'):
            with file(job_name+'.sta','r') as f:
                last_line = f.read().split('\n')[-1]
            print_cmd(last_line)
        elif os.path.exists(job_name+'.sta'):
            print_cmd('-'*30+'\njob fertig!')
            break
    return

def __make_ip_out(model):
    # Integrationspunktoutput machen im inp File
    model.keywordBlock.synchVersions()
    block_list = model.keywordBlock.sieBlocks
    pos_i = [i for i, j in enumerate(block_list) if 'Output, field' in j]
    # Koordinaten an Knoten und Integrationspunkten + Volumen Integrationspunkt (IVOL)
    str_out = "**\n*Element Output, directions=YES\nCOORD,IVOL,\n**\n*Node Output\nCOORD,"
    # String einfuegen!
    for i_step, pos in enumerate(pos_i):
        model.keywordBlock.insert(pos + i_step, str_out)
    return

def __get_model_nodes_elem(model):
    n_elem = 0
    n_nodes = 0
    for inst in model.rootAssembly.instances.values():
        n_elem += len(inst.elements)
        n_nodes += len(inst.nodes)
    print_cmd('-'*30+'\ntotal nodes/elements in model: '+str(n_elem)+' / '+str(n_nodes))
    return

def run_model(model, jobN, numPr, ifRun=1, ifRestart=0, if_check=1):
    """ Job erzeugen; ifRun==1: gleich Rechnen """
    if numPr == 0:
        n_proc = 1
    else:
        n_proc = numPr
    # Datacheck
    __get_model_nodes_elem(model)
    __make_ip_out(model)
    if if_check:
        job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                      model=model.name, name=jobN, nodalOutputPrecision=SINGLE,
                      multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                      type=ANALYSIS)
        job.submit(consistencyChecking=OFF, datacheckJob=True)
        job.waitForCompletion()
        # dat file auswerten
        with file(jobN+'.dat','r') as f:
            lines = f.read().split('\n')[-100:]
        try:
            n_mem = [i for i,line in enumerate(lines) if 'E S T I M A T E' in line][0]+6
            mem_min, mem_opt = [float(i) for i in lines[n_mem].split(' ') if i != ''][-2:]
            print_cmd('-'*30+'\nminimum/optimum required memory (MB): '+str(mem_min)+' / '+str(mem_opt))
        except:
            print_cmd('Error in preprocessor')
    #
    if ifRestart == 1:
        job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                      model=model.name, name=jobN, nodalOutputPrecision=SINGLE,
                      multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                      type=RESTART)
    else:
        job = mdb.Job(getMemoryFromAnalysis=True, memory=90, memoryUnits=PERCENTAGE,
                      model=model.name, name=jobN, nodalOutputPrecision=SINGLE,
                      multiprocessingMode=THREADS, numCpus=n_proc, numDomains=n_proc,
                      type=ANALYSIS)
        # nur voruebergehend
    if ifRun == 1 and numPr != 0:
        mdb.saveAs(pathName=jobN + '.cae')
        job.submit(consistencyChecking=OFF)
        #print_cmd(jobN)
        #wait_for_job(jobN,10)
        job.waitForCompletion()
    else:
        mdb.saveAs(pathName=jobN + '.cae')
        job.writeInput(consistencyChecking=OFF)
    return

def load_odb(model_name):
    viewport1 = session.viewports['Viewport: 1']
    odb = session.openOdb(name=model_name + '.odb')
    viewport1.setValues(displayedObject=odb)
    return odb

# Auswahl-Funktionen -----------------------------------------------------------

def getCoord(object):
    length=len(object)
    list0=[list(i[0]) for i in object.pointsOn]
    return [[i]+list0[i] for i in range(length)]

def combineL(object,listFA):
    # combine List of findAt elements
    if len(listFA)>0:
        list0=[i.pointOn for i in listFA]
        setL=object.findAt(list0[0])
        for i in list0:
            setL+=object.findAt(i)
        return setL
    else:
        return

def selectC(coord,nC,c,if_cyl=0):
    # Koordinate auswaehlen: nC: 1:x,2:y,3:z
    if c==[]:
        rList=coord
    elif isinstance(c,list) and len(c)==2: # ob oben/unten Grenze angegeben
        if if_cyl and nC == 2:
            rList=([i for i in coord if i[nC]>c[0]-TOL and i[nC]<c[1]+TOL]+
                   [i for i in coord if i[nC]>c[0]+math.pi-TOL and i[nC]<c[1]+math.pi+TOL]+
                   [i for i in coord if i[nC]>c[0]-math.pi-TOL and i[nC]<c[1]-math.pi+TOL])
        else:
            rList=[i for i in coord if i[nC]>c[0]-TOL and i[nC]<c[1]+TOL]
    else:
        if if_cyl and nC == 2:
            rList=([i for i in coord if i[nC]<c[0]+TOL and i[nC]>c[0]-TOL]+
                   [i for i in coord if i[nC]<c[0]+math.pi+TOL and i[nC]>c[0]+math.pi-TOL]+
                   [i for i in coord if i[nC]<c[0]-math.pi+TOL and i[nC]>c[0]-math.pi-TOL])
        else:
            rList=[i for i in coord if i[nC]<c[0]+TOL and i[nC]>c[0]-TOL]
    return rList

def selectFull(object,x,y,z):
    # object: zb. part.edges
    # x,y,z: a) [real]: bei real, b) []: ueberall, c) [real1,real2]: zwischen 1 und 2
    coords=getCoord(object[:])
    coords=selectC(coords,1,x)
    coords=selectC(coords,2,y)
    coords=selectC(coords,3,z)
    print(coords)
    listFA=[object[i[0]] for i in coords]
    return combineL(object,listFA)

def getCoordXY(point,axis):
    # input: point als [r,phi,z] und axis (wie unten definiert)
    # output: punkt im karthesischen Koordinatensystem
    # phi ist gegen uhrzeigersinn definiert...
    if axis[1][0]==0:
        if axis[1][1]>0:
            ang0=0
        else:
            ang0=-math.pi
    else:
    # das geht vielleicht nicht...
        ang0=atan(axis[1][1]/axis[1][0])
    #print ang0
    x=point[0]*sin(ang0-point[1])+axis[0][0]
    y=point[0]*cos(ang0-point[1])+axis[0][1]
    z=point[2]+axis[0][2]
    return [x,y,z]

# gibt winkel positiv oder negativ zurueck. passt mir aber eh ganz gut
def getCoordCyl(point,axis):
    # input: punkt in karthesischen Koordinaten(point), achse fuer zyl KS
    # [[x0,y0,z0],[x1,y1,0]]: Zentrum bei x0,y0,z0; phi=0 bei x2,y2,z2-Richtung
    # output: Punkt Koordinaten im zyl. KS
    r=((point[0]-axis[0][0])**2+(point[1]-axis[0][1])**2)**0.5
    if (point[1]-axis[0][1])==0. and (point[0]-axis[0][0])!=0.:
        if (point[0]-axis[0][0])>0:
            phi=-math.pi/2
        else:
            phi=math.pi/2
    else:
        phi=-atan((point[0]-axis[0][0])/(point[1]-axis[0][1]))
    z=point[2]-axis[0][2]
    return [r,phi,z]

def makeCylC(coordL,axis):
    # input: liste von karthesischen Koordinaten(coordL), achse fuer zyl KS
    # [[x0,y0,z0],[x1,y1,0]]: Zentrum bei x0,y0,z0; phi=0 bei x2,y2,z2-Richtung
    # output: Koordinaten Liste im zyl. KS
    return [getCoordCyl(i,axis) for i in coordL]

def selectFullC(object,r,phi,z,axis,if_print=0):
    # object: zb. part.edges
    # r,phi(Radiant),z: a) [real]: bei real, b) []: ueberall, c) [real1,real2]: zwischen 1 und 2
    coords=[[i[0]]+getCoordCyl(i[1:4],axis) for i in getCoord(object[:])]
    #coords=makeCylC(coords,axis)
    if if_print:
        #print_cmd(np.array(coords)[:,2])
        str_out = str(phi[0])+', '+str(phi[0]+math.pi)+', '+str(phi[0]-math.pi)
        #print_cmd(str_out)
    coords=selectC(coords,1,r,1)
    coords=selectC(coords,2,phi,1)
    coords=selectC(coords,3,z,1)
    #print coords
    listFA=[object[i[0]] for i in coords]
    return combineL(object,listFA)

############ ??? ########## stimmt das mit ersten zum zweiten?! ################
def edgeBiased(part,edge,nC,dir,axis):
    # edges sortieren: in nC-Richtung(1:x,2:y,3:z) positiv(dir=1) oder
    # negativ (dir=-1) sortieren
    # Ausgabe: 0: zu end1Edges, 1: zu end2Edges
    vert=edge.getVertices()
    if axis==[]:
        vertC=[list(part.vertices[i].pointOn[0]) for i in vert]
    else:
        vertC=[getCoordCyl(list(part.vertices[i].pointOn[0]),axis) for i in vert]
    #print vertC
    if vertC[1][nC-1] > vertC[0][nC-1] and dir==1 or vertC[1][nC-1] < vertC[0][nC-1] and dir==-1:
        res=1
    else:
        res=0
    return res

# wenn karthesiche Koordinaten: axis=[]
def edgeBiasedList(part,edges,nC,dir,axis,lGrob,lFein,ifInst=0,model=0):
    # edges sortieren: in nC-Richtung(1:x,2:y,3:z) positiv(dir=1) oder
    # negativ (dir=-1) sortieren
    if model==0:
        mdb.models[mdb.models.keys()[0]]
    # Ausgabe: end1Edges, end2Edges
    bList=[edgeBiased(part,i,nC,dir,axis) for i in edges]
    #print bList
    edge1L=combineL(part.edges,[edges[i] for i in range(len(bList)) if bList[i]==0])
    edge2L=combineL(part.edges,[edges[i] for i in range(len(bList)) if bList[i]==1])
    if ifInst==0:
        part.seedEdgeByBias(biasMethod=SINGLE, constraint=FINER,
            end1Edges=edge1L, end2Edges=edge2L, maxSize=lGrob, minSize=lFein)
    else:
        model.rootAssembly.seedEdgeByBias(biasMethod=SINGLE, constraint=FINER,
            end1Edges=edge1L, end2Edges=edge2L, maxSize=lGrob, minSize=lFein)
    print("done")

# Auswertefunktionen (aus ABQ/Python Seminar, 2019) ----------------------------

def get_fo(odb,step_name,i_frame,res_ordner='results'):
    # Field Output auswerten
    frame_auswert = odb.steps[step_name].frames[i_frame]
    # -------------------------------------------------
    # Integrationspunkte (COORD,IVOL,S)
    coords_ip_list = np.array([i.data for i in frame_auswert.fieldOutputs['COORD'].
                      getSubset(position=INTEGRATION_POINT).values])
    ivol_list = np.array([i.data for i in frame_auswert.fieldOutputs['IVOL'].values])
    # Spannungen: ((S11,S22,S33,S12),...)
    s_list = np.array([i.data for i in frame_auswert.fieldOutputs['S'].values])

    coords_n_list = np.array([i.data for i in frame_auswert.fieldOutputs['COORD'].
                      getSubset(position=NODAL).values])
    u_list = np.array([i.data for i in frame_auswert.fieldOutputs['U'].values])

    list_component_labels_ip = (frame_auswert.fieldOutputs['COORD'].componentLabels+('IVOL',)+
                                frame_auswert.fieldOutputs['S'].componentLabels)
    odb_name = odb.name[:-4].split('/')[-1]
    with open(res_ordner+'/'+odb_name+'_res_ip_'+step_name+'_'+str(i_frame).zfill(2)+'.dat','w') as f:
        f.write(' '.join(list_component_labels_ip)+'\n')
        np.savetxt(f,np.column_stack((coords_ip_list,ivol_list,s_list)))

    list_component_labels_n = (frame_auswert.fieldOutputs['COORD'].componentLabels+
                               frame_auswert.fieldOutputs['U'].componentLabels)
    #with open(odb.name[:-4]+'_res_n_'+step_name+'_'+str(i_frame)+'.dat','w') as f:
    with open('{}/{}_res_n_{}_{}.dat'.format(res_ordner,odb_name,step_name,str(i_frame).zfill(2)),'w') as f:
        f.write(' '.join(list_component_labels_n)+'\n')
        np.savetxt(f,np.column_stack((coords_n_list,u_list)))
    return

def auswert_field(odb_name):
    odb = session.openOdb(name=odb_name+'.odb')
    vp = session.viewports['Viewport: 1']

    vp.setValues(displayedObject=odb)
    vp.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
    # Schleife ueber alle Stepnamen
    for step_name in odb.steps.keys():
        # Schleife ueber alle frame-indizes des aktuellen Steps
        for i_frame in range(len(odb.steps[step_name].frames)):
            get_fo(odb,step_name,i_frame)
    return

def get_history_output(odb_name, res_ordner='results', step_name='',h=20.,b=30.):
    odb = session.openOdb(name=odb_name+'.odb')
    if step_name != '':
        step1 = odb.steps[step_name]
    else:
        step1 = odb.steps.values()[0]

    # historyRegion: der Referenzpunkt (bei Assembly: Energien des Modells)
    hr = [hr for name_hr,hr in step1.historyRegions.items() if 'Node' in name_hr][0]

    # Daten von HistoryOutput bekommen
    u1 = np.array(hr.historyOutputs['U1'].data)
    rf1 = np.array(hr.historyOutputs['RF1'].data)

    # nur Zeitspalte bzw. Datenspalten nehmen
    time = u1[:,0]
    u1 = u1[:,1]
    rf1 = rf1[:,1]

    # Ausgabe der Steifigkeit: RF1/U1
    print_cmd('mittlerer E-Modul Platte: '+str(b*rf1[-1]/(u1[-1]*h))+' MPa')
    print_cmd('-'*70)
    # zum Ausprobieren
    step_name = step1.name

    # Spalten verbinden und in .dat-File schreiben
    with open('{}/{}_res_ho_{}.dat'.format(res_ordner,odb_name,step1.name),'w') as f:
        f.write(' '.join(['time','U1','RF1'])+'\n')
        np.savetxt(f,np.column_stack((time,u1,rf1)))
    return

#
