# Rolling Model functions (2D und 3D), MP, 2020-02-20 -- -----------------------

from abaqus import *
from abaqusConstants import *
from caeModules import *
import numpy as np
from pac_abq_tools import *
import Pickler, os

TOL = 1.e-5
DIR0 = os.path.abspath('')

# general functions for both 2D and 3D models ----------------------------------
def make_mat_sec(model, input_d):
    """ Materialien und Sections erstellen (Rad immer el, Schiene: ifPl plastisch) """
    matName = input_d['Material variant']
    if3D = input_d['Geometrievariante'][0]
    wheel_rigid = input_d['ob Rad starr']
    # Materialien und Sections
    #
    matR260 = model.Material(name='R260')
    matR260.Elastic(table=((205000.0, 0.3),))
    matR260.Plastic(dataType=PARAMETERS, hardening=COMBINED, numBackstresses=6,
                    table=((320.0, 350000.0, 5000.0, 80000.0, 1000.0, 15000.0, 150.0, 10000.0, 20.0,
                            8000.0, 20.0, 190.0, 0.01),))
    matR260.plastic.CyclicHardening(parameters=ON, table=((320.0, -40.0, 0.04),))
    #
    mat_ideal_pl_iso =  model.Material(name='ideal-iso')
    mat_ideal_pl_iso.Elastic(table=((205000.0, 0.3),))
    mat_ideal_pl_iso.Plastic(table=((340.0, 0.0), (341.0, 3.0)))
    mat_ideal_pl_kin = model.Material(name='ideal-kin')
    mat_ideal_pl_kin.Elastic(table=((205000.0, 0.3),))
    mat_ideal_pl_kin.Plastic(hardening=KINEMATIC, table=((340.0, 0.0), (341.0, 3.0)))
    #
    # charmec variants
    bc2_list = (8.046400E+04, 1.933308E+05, 4.514129E+02, 2.122685E+02, 5.921574E-03,
                2.897014E-01, 1.450191E+03, 3.412643E-03, 0.000000E+00, 1.014782E+04,
                3.102063E-03, 0.000000E+00)
    af2_list = (8.046400E+04, 1.933308E+05, 5.907098E+02, 1.036594E+03, 1.679601E+00,
                1.000000E+00, 1.062461E+03, 1.972404E-03, 0.000000E+00, 9.877505E+03,
                5.647541E-03, 0.000000E+00)
    ob2_list = (8.046400E+04, 1.933308E+05, 4.538269E+02, 3.697411E+02, 7.355355E-03,
                3.711531E-01, 8.920645E+03, 3.315568E-03, 2.579515E+00, 1.045574E+03,
                3.688427E-03, 1.515467E+00)
    mat_bc2 = model.Material(name='charmec_bc2')
    mat_af2 = model.Material(name='charmec_af2')
    mat_ob2 = model.Material(name='charmec_ob2')
    #
    mat_bc2.Depvar(n=28)
    mat_af2.Depvar(n=28)
    mat_ob2.Depvar(n=28)
    #
    mat_bc2.UserMaterial(mechanicalConstants=bc2_list)
    mat_af2.UserMaterial(mechanicalConstants=af2_list)
    mat_ob2.UserMaterial(mechanicalConstants=ob2_list)
    # andere Sachen
    mat = model.Material(name='steel')
    if 'charmec' in matName:
        mat.Elastic(table=((211983.02, 0.31725381),))
    else:
        mat.Elastic(table=((210000., 0.3),))
    #
    ifPl = 0
    if ifPl == 1:
        mat.Plastic(table=((sYield, 0.0), (sYield + 100, 100 / plMod)))
    #
    matEl = model.Material(name='steel-elastisch')
    if 'charmec' in matName:
        matEl.Elastic(table=((211983.02, 0.31725381),))
    else:
        matEl.Elastic(table=((210000., 0.3),))
    #
    matEl.Plastic(hardening=KINEMATIC, table=((30000.0, 0.0), (40000.0, 3.0)))
    model.HomogeneousSolidSection(material=str(matName), name='steel')
    model.HomogeneousSolidSection(material='steel-elastisch', name='steel-el')
    #
    for i in model.parts.items():
        if 'Starr' not in i[0]:
            if if3D == '3D':
                if 'Schiene-F' in i[0]:
                    i[1].setElementType(elemTypes=(mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD,
                                        kinematicSplit=AVERAGE_STRAIN, secondOrderAccuracy=OFF,
                                        hourglassControl=DEFAULT),), regions=i[1].sets['ALL'])
                else:
                    i[1].setElementType(elemTypes=(mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD,
                                                            kinematicSplit=AVERAGE_STRAIN, secondOrderAccuracy=OFF,
                                                            hourglassControl=DEFAULT),),
                                        regions=i[1].sets['ALL'])

            else:
                if 'charmec' in matName:
                    str_elem = 'CPE4'
                else:
                    str_elem = 'CPE4R'
                #
                i[1].setElementType(elemTypes=(mesh.ElemType(elemCode=str_elem, elemLibrary=STANDARD),
                                               mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)), regions=i[1].sets['ALL'])
            if (('Rad' in i[0] and 'plastic' not in wheel_rigid) or
                ('Rad' not in i[0] and 'plastic' in wheel_rigid)):
                #print_cmd(str(i[0])+': elastisch')
                matT = 'steel-el'
            else:
                if 'charmec' in matName:
                    if 'Schiene-F' in i[0]:
                        matT = 'steel'
                    else:
                        matT = 'steel-el'
                else:
                    #print_cmd(str(i[0])+': el/pl')
                    matT = 'steel'
            #
            print_cmd('Zuweisung von Section: '+str(i[0]))
            i[1].SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE,
                                   region=i[1].sets['ALL'], sectionName=matT, thicknessAssignment=FROM_SECTION)
    return

def make_assembly(model, parts, input_d):
    """ Assembly und Interactions """
    if3D = input_d['Geometrievariante'][0]
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])
    if if3D == '2D':
        [bFF, bF, bG] = [bFF/2., bF/2., bG/2.]
    lRoll = input_d['Rolllaenge']
    rRad = input_d['Radius Rad']
    wheel_rigid = input_d['ob Rad starr']
    mu = input_d['Friction coefficient']
    [schieneF, schieneG, radF, radG] = parts
    # noch machen
    x0 = (bFF - lRoll)/2.
    #
    if wheel_rigid != 'Yes':
        ang0 = (bF - bFF) / rRad / 2
    else:
        ang0 = 0

    assembly = model.rootAssembly
    assembly.DatumCsysByDefault(CARTESIAN)
    instSF = assembly.Instance(dependent=ON, name='Schiene-Fein-1', part=schieneF)
    instSG = assembly.Instance(dependent=ON, name='Schiene-Grob-1', part=schieneG)
    if 'Rad-Starr-1' not in assembly.instances.keys():
        instRF = assembly.Instance(dependent=ON, name='Rad-Fein-1', part=radF)
        if if3D != '3D':
            instRG = assembly.instances['Rad-Grob-1']
        else:
            instRG = assembly.Instance(dependent=ON, name='Rad-Grob-1', part=radG)
        # Rad drehen
        if if3D != '3D': ###################
            model.rootAssembly.rotate(angle=-(ang0 + x0 / rRad) * 180 / pi, axisDirection=(0.0, 0.0, 1.0),
                                      axisPoint=(0.0, rRad, 0.0), instanceList=('Rad-Fein-1', 'Rad-Grob-1'))
            model.rootAssembly.translate(instanceList=('Rad-Fein-1', 'Rad-Grob-1'),
                                         vector=(-bFF / 2 + x0, 0.03, 0.0))
        else:
            assembly.translate(instanceList=('Schiene-Fein-1',), vector=(0.0, 0.0, (bG - bF) / 2))
            assembly.rotate(instanceList=('Schiene-Fein-1', 'Schiene-Grob-1'), axisPoint=(0.0,
                                                                                          0.0, 0.0),
                            axisDirection=(0.0, 1.0, 0.0), angle=-90.0)
            assembly.translate(instanceList=('Schiene-Fein-1', 'Schiene-Grob-1'), vector=(bG / 2, 0, 0))
            assembly.rotate(instanceList=('Rad-Fein-1', 'Rad-Grob-1'), axisPoint=(0, 0, 0),
                            axisDirection=(0, 1, 0), angle=180.0)
            assembly.rotate(instanceList=('Rad-Fein-1', 'Rad-Grob-1'), axisPoint=(0, rRad, 0),
                            axisDirection=(0, 0, 1), angle=((bF + bFF) / 2 - x0) / rRad * 180 / pi)
            assembly.translate(instanceList=('Rad-Fein-1', 'Rad-Grob-1'), vector=(-bFF / 2 + x0, 0, 0))
        #
        rp1 = assembly.ReferencePoint(point=(-bFF / 2 + x0, rRad, 0.0))
        assembly.Set(name='RP-Rad', referencePoints=(assembly.referencePoints[rp1.id],))
        model.Tie(adjust=ON, master=instRG.surfaces['tie'], name='tie-rad',
              positionToleranceMethod=COMPUTED, slave=instRF.surfaces['tie'],
              thickness=ON, tieRotations=ON)
    else:
        instRF = assembly.instances['Rad-Starr-1']
        # Rad bewegen
        if if3D != '3D':
            model.rootAssembly.translate(instanceList=('Rad-Starr-1',),
                                         vector=(-bFF / 2 + x0, 0.005, 0.0))
        else:
            assembly.translate(instanceList=('Schiene-Fein-1',), vector=(0.0, 0.0, (bG - bF) / 2))
            assembly.rotate(instanceList=('Schiene-Fein-1', 'Schiene-Grob-1'), axisPoint=(0.0,
                            0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=-90.0)
            assembly.translate(instanceList=('Schiene-Fein-1', 'Schiene-Grob-1'), vector=(bG / 2, 0, 0))
            #assembly.rotate(instanceList=('Rad-Fein-1',), axisPoint=(0, 0, 0),
            #                axisDirection=(0, 1, 0), angle=180.0)
            assembly.translate(instanceList=('Rad-Starr-1',), vector=(-bFF / 2 + x0, 0, 0))
    #
    model.Tie(adjust=ON, master=instSG.sets['tie'], name='tie-schiene',
              positionToleranceMethod=COMPUTED, slave=instSF.sets['tie']
              , thickness=ON, tieRotations=ON)
    if 'Rad-Starr-1' not in assembly.instances.keys():
        if if3D != '3D':
            model.RigidBody(name='rad-cent', tieRegion=assembly.instances['Rad-Grob-1'].sets['rigid_cent'], refPointRegion=
                            assembly.sets['RP-Rad'])
            """
            model.RigidBody(name='rad-cent', tieRegion=assembly.sets['rigid'], refPointRegion=
            assembly.sets['RP-Rad'])
            """
        else:
            model.RigidBody(name='rad-cent', tieRegion=instRG.sets['rigid'], refPointRegion=
            assembly.sets['RP-Rad'])
            model.ZsymmBC(name='zSym-RF', createStepName='Initial', region=instRF.sets['zSym'])
            model.ZsymmBC(name='zSym-RG', createStepName='Initial', region=instRG.sets['zSym'])
        #
        if if3D == '3D':
            model.ZsymmBC(name='zSym-SF', createStepName='Initial', region=instSF.sets['zSym'])
            model.ZsymmBC(name='zSym-SG', createStepName='Initial', region=instSG.sets['zSym'])
    # Kontaktdefinition
    kontP = model.ContactProperty('Kontakt-Reibung')
    ifPenalty = 1
    if ifPenalty == 1:
        if mu != 0.:
            kontP.TangentialBehavior(formulation=PENALTY, directionality=ISOTROPIC, slipRateDependency=OFF,
                                 pressureDependency=OFF, temperatureDependency=OFF, dependencies=0, table=((mu,),),
                                 shearStressLimit=None, maximumElasticSlip=FRACTION,
                                 fraction=0.0001, elasticSlipStiffness=None)
        else:
            kontP.TangentialBehavior(formulation=FRICTIONLESS)
    else:
        if mu != 0.:
            kontP.TangentialBehavior(dependencies=0, directionality=ISOTROPIC, formulation=LAGRANGE,
                                 pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF,
                                 table=((mu,),), temperatureDependency=OFF)
        else:
            kontP.TangentialBehavior(formulation=FRICTIONLESS)
    kontP.NormalBehavior(allowSeparation=ON, constraintEnforcementMethod=DEFAULT,
                         pressureOverclosure=HARD)
    kontPfl = model.ContactProperty('fricless')
    kontPfl.NormalBehavior(allowSeparation=ON, constraintEnforcementMethod=DEFAULT,
                           pressureOverclosure=HARD)
    kontPfl.TangentialBehavior(formulation=FRICTIONLESS)
    ifNodeCont = 0
    if ifNodeCont == 1:
        model.SurfaceToSurfaceContactStd(adjustMethod=NONE, clearanceRegion=None, createStepName='Initial',
                                         datumAxis=None,
                                         initialClearance=OMIT, interactionProperty='Kontakt-Reibung', master=
                                         instRF.surfaces['contact'], name='kontaktdefinition',
                                         slave=instSF.sets['contact'],
                                         sliding=FINITE, thickness=ON)
    else:
        model.SurfaceToSurfaceContactStd(name='kontaktdefinition', createStepName='Initial',
                                         master=instRF.surfaces['contact'],
                                         slave=instSF.surfaces['contact'], sliding=FINITE, thickness=ON,
                                         interactionProperty=
                                         'Kontakt-Reibung', adjustMethod=NONE, initialClearance=OMIT, datumAxis=None,
                                         clearanceRegion=None)
    # (Ausgeschaltet) make node Sets for applying the press/trac loads
    instSF = assembly.instances['Schiene-Fein-1']
    nodesC = instSF.sets['contact'].nodes
    # Set fuer die Verschiebungs Ausgabe definieren
    assembly.Set(name='edgeNachUnten', edges=instSF.edges.getByBoundingBox(xMin=-TOL, xMax=TOL, zMin=-TOL, zMax=TOL))
    try:
       instRG == 0
    except:
        instRG = []
    return (instSG, instSF, instRG)

def make_load(model, instSG, instRG, input_d, uy00=0.05):
    print('funktion aufgerufen')
    """ Rad rollen: etliche Varianten """
    #[lRoll, f2D, lVar, creep, trac] = load
    lRoll = input_d['Rolllaenge']
    rRad = input_d['Radius Rad']
    f2D = input_d['Normal load'] * 1000 / 2
    lVar = input_d['Belastung'][1]

    creep = input_d['Belastung'][1]
    traction = creep
    creep = -creep
    #
    nCycles = input_d['Number Cycles']
    uy0 = input_d['uy0']
    if_full_out = input_d['ob full Output']
    #
    el_mesh = input_d['Abmessungen']['element length']
    assembly = model.rootAssembly
    #
    model.StaticStep(initialInc=0.5, maxNumInc=1000, name='Kontakt-UY001', nlgeom=ON, previous='Initial')
    print('step erzeugt!!')
    model.StaticStep(initialInc=0.1, maxNumInc=1000, name='Kontakt-F001', nlgeom=ON, previous='Kontakt-UY001')
    if lRoll == 0:
        incSize = 1.
    else:
        incSize = 1 / (lRoll / el_mesh[0]) * 0.7
    print(incSize)
    if lVar == "traction":
        model.StaticStep(initialInc=0.1, maxNumInc=1000, name='Kontakt-Moment001', nlgeom=ON, previous='Kontakt-F001')
        model.StaticStep(initialInc=incSize, maxInc=incSize, minInc=incSize / 1000, noStop=OFF, maxNumInc=5000,
                         name='Rollen001', nlgeom=ON, previous='Kontakt-Moment001')
    else:
        model.StaticStep(initialInc=incSize, maxInc=incSize, minInc=incSize / 1000, noStop=OFF, maxNumInc=5000,
                         name='Rollen001', nlgeom=ON, previous='Kontakt-F001')
    model.StaticStep(initialInc=0.04, maxNumInc=1000, name='Abheben001', nlgeom=ON, previous='Rollen001')
    # Einspannungen
    model.YsymmBC(createStepName='Initial', localCsys=None, name='ySym', region=instSG.sets['unten'])
    model.XsymmBC(createStepName='Initial', localCsys=None, name='xSym-bot', region=instSG.sets['unten'])
    model.XsymmBC(createStepName='Initial', localCsys=None, name='xSym', region=instSG.sets['seiten'])
    if 'zSym' in instSG.sets.keys():
        model.ZsymmBC(createStepName='Initial', localCsys=None, name='zSymG', region=instSG.sets['zSym'])
        model.ZsymmBC(createStepName='Initial', localCsys=None, name='zSymF', region=assembly.instances['Schiene-Fein-1'].sets['zSym'])
    # Rad Bewegen und Belasten
    bcU0Rad = model.DisplacementBC(amplitude=UNSET, createStepName='Kontakt-UY001',
                                   distributionType=UNIFORM, fieldName='', fixed=OFF, localCsys=
                                   None, name='Rad-UY001', region=assembly.sets['RP-Rad'], u1=UNSET, u2=-uy00,# es war -0.05
                                   ur3=UNSET, ur2=0, ur1=0, u3=0)
    bcU0Rad.deactivate('Kontakt-F001')
    bcURad = model.DisplacementBC(amplitude=UNSET, createStepName=
                                  'Initial', distributionType=UNIFORM, fieldName='', localCsys=None, name=
                                  'Rad-UX-ROTZ', region=assembly.sets['RP-Rad'], u1=SET, u2=UNSET, ur3=SET, ur1=0, ur2=0, u3=0)
    if lVar == "traction":
        mom = trac * f2D * rRad
        if mom != 0:
            momentRad = model.Moment(cm3=mom, createStepName='Kontakt-Moment001',
                                     localCsys=None, name='Rad-Moment001', region=assembly.sets['RP-Rad'])
        # momentRad.deactivate('Abheben0')
        bcURad.setValuesInStep(stepName='Kontakt-Moment001', ur3=FREED)
        bcURad.setValuesInStep(stepName='Abheben001', ur3=-lRoll / rRad)
    else:
        if 'Rad-Starr-1' in assembly.instances.keys():
            angMove = 0
        else:
            angMove = lRoll * (2 + creep) / (rRad * (2 - creep))
        #
        bcURad.setValuesInStep(stepName='Rollen001', ur3=-angMove)
    #
    bcURad.setValuesInStep(stepName='Rollen001', u1=lRoll)
    bcURad.setValuesInStep(stepName='Abheben001', u2=0.5)
    # Kraft im Rad
    forceR = model.ConcentratedForce(cf2=-f2D, createStepName='Kontakt-F001', distributionType=UNIFORM,
                                     field='', localCsys=None, name='Kraft-Rad', region=assembly.sets['RP-Rad'])
    model.StaticStep(initialInc=0.25, maxNumInc=1000, name='Rad-Zurueck001', nlgeom=ON, previous='Abheben001')
    bcURad.setValuesInStep(stepName='Rad-Zurueck001', u2=0., u1=0., ur3=0.)
    model.interactions['kontaktdefinition'].setValuesInStep(interactionProperty='fricless', stepName='Abheben001')
    model.interactions['kontaktdefinition'].setValuesInStep(interactionProperty='Kontakt-Reibung',
                                                            stepName='Rad-Zurueck001')
    # Output erstellen
    if if_full_out == 'Yes':
        model.fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'PE', 'PEEQ', 'CNAREA', 'CFORCE',
                                  'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 'CDISP', 'COORD', 'IVOL', 'ALPHAN','ALPHA'), frequency=1)

    elif if_full_out == 'No':
        model.fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'PE', 'PEEQ', 'CNAREA', 'CFORCE',
                                 'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 'CDISP', 'COORD', 'IVOL', 'ALPHAN','ALPHA'), numIntervals=2)
    else:
        #del model.fieldOutputRequests['F-Output-1']
        model.fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'PE', 'PEEQ', 'CNAREA', 'CFORCE',
                                  'LE', 'U', 'CF', 'CSTRESS', 'COORD', 'IVOL', 'ALPHAN','ALPHA'), numIntervals=2)

    #
    if if_full_out in ['Yes', 'No']:
        model.HistoryOutputRequest(name='Referenzpunkt', createStepName='Kontakt-UY001', variables=('U1', 'U2',
                                                                                                  'UR3', 'RF1', 'RF2',
                                                                                                  'RM3', 'COOR1'),
                                   region=assembly.sets['RP-Rad'], sectionPoints=DEFAULT, rebar=EXCLUDE)
        # Output an den ganzen Kontaktknoten
        nCSets = [i[1] for i in assembly.sets.items() if 'nCont-Set-n' in i[0]]
        k = 1
        for i in nCSets:
            model.HistoryOutputRequest(name='hout-' + str(k), createStepName='Kontakt-UY001', variables=('CFT1', 'CFT2'),
                                       region=i, sectionPoints=DEFAULT, rebar=EXCLUDE)
            k += 1
            # mehrere Zyklen rechnen
    if nCycles > 1:
        if lRoll == 0:
            incSize = 1.
        else:
            incSize = 1 / (lRoll / el_mesh[0]) * 0.7
        #
        cycList = range(2, nCycles + 1)
        # jetzt durchgehen
        print(cycList)
        for cyc in cycList:
            print('cycle # '+str(cyc+1))
            model.StaticStep(initialInc=0.5, maxNumInc=1000, name='Kontakt-UY' + str(cyc).zfill(3), nlgeom=ON,
                             previous='Rad-Zurueck' + str(cyc - 1).zfill(3))
            model.StaticStep(initialInc=0.5, maxNumInc=1000, name='Kontakt-F' + str(cyc).zfill(3), nlgeom=ON,
                             previous='Kontakt-UY' + str(cyc).zfill(3))
            bcURad.setValuesInStep(stepName='Kontakt-UY' + str(cyc).zfill(3), u2=FREED)
            bcURad.setValuesInStep(amplitude=FREED, stepName='Kontakt-UY' + str(cyc).zfill(3))
            bcU0Rad = model.DisplacementBC(amplitude=UNSET, createStepName='Kontakt-UY' + str(cyc).zfill(3),
                                           distributionType=UNIFORM,
                                           name='Rad-UY' + str(cyc).zfill(3), region=assembly.sets['RP-Rad'],
                                           u1=UNSET, u2=-uy0, ur3=UNSET)
            bcU0Rad.deactivate('Kontakt-F' + str(cyc).zfill(3))
            if lVar == "traction":
                model.StaticStep(initialInc=0.1, maxNumInc=1000, name='Kontakt-Moment' + str(cyc).zfill(3), nlgeom=ON,
                                 previous='Kontakt-F' + str(cyc).zfill(3))
                model.StaticStep(initialInc=incSize, maxInc=incSize, minInc=incSize / 1000, noStop=OFF, maxNumInc=5000,
                                 name='Rollen' + str(cyc).zfill(3),
                                 nlgeom=ON, previous='Kontakt-Moment' + str(cyc).zfill(3))
            else:
                model.StaticStep(initialInc=incSize, maxInc=incSize, minInc=incSize / 1000, noStop=OFF, maxNumInc=1000,
                                 name='Rollen' + str(cyc).zfill(3), nlgeom=ON, previous='Kontakt-F' + str(cyc).zfill(3))
            model.StaticStep(initialInc=0.04, maxNumInc=1000, name='Abheben' + str(cyc).zfill(3), nlgeom=ON,
                             previous='Rollen' + str(cyc).zfill(3))
            if lVar == "traction":
                mom = trac * f2D * rRad
                if mom != 0:
                    momentRad.setValuesInStep(stepName='Kontakt-Moment'+str(cyc).zfill(3),cm3=mom)
                # momentRad.deactivate('Abheben'+str(cyc))
                bcURad.setValuesInStep(stepName='Kontakt-Moment' + str(cyc).zfill(3), ur3=FREED)
                bcURad.setValuesInStep(stepName='Abheben' + str(cyc).zfill(3), ur3=-lRoll / rRad)
            else:
                angMove = lRoll * (2 + creep) / (rRad * (2 - creep))
                bcURad.setValuesInStep(stepName='Rollen' + str(cyc).zfill(3), ur3=-angMove)
            #
            bcURad.setValuesInStep(stepName='Rollen' + str(cyc).zfill(3), u1=lRoll)
            bcURad.setValuesInStep(stepName='Abheben' + str(cyc).zfill(3), u2=0.5)
            model.StaticStep(initialInc=0.25, maxNumInc=1000, name='Rad-Zurueck' + str(cyc).zfill(3), nlgeom=ON,
                             previous='Abheben' + str(cyc).zfill(3))
            bcURad.setValuesInStep(stepName='Rad-Zurueck' + str(cyc).zfill(3), u2=0.4, u1=0., ur3=0.)
            model.interactions['kontaktdefinition'].setValuesInStep(interactionProperty='fricless',
                                                                    stepName='Abheben' + str(cyc).zfill(3))
            model.interactions['kontaktdefinition'].setValuesInStep(interactionProperty='Kontakt-Reibung',
                                                                    stepName='Rad-Zurueck' + str(cyc).zfill(3))
            if if_full_out not in ['Yes', 'No']:
                model.FieldOutputRequest(name='F-Output-lift'+str(cyc).zfill(3),
                                         createStepName='Abheben' + str(cyc).zfill(3),
                                         variables=('S', 'ALPHAN', 'ALPHA', 'PE', 'PEEQ', 'LE', 'U'),
                                         frequency=LAST_INCREMENT)
                model.fieldOutputRequests['F-Output-lift'+str(cyc).zfill(3)].deactivate('Rad-Zurueck' + str(cyc).zfill(3))
            if cyc%50 == 0:
                np.savetxt('progress_inp_file.dat',np.array([cyc]))
            #, frequency=LAST_INCREMENT
    # Restart Sachen erstellen
    [i[1] for i in model.steps.items() if 'Rad-Zurueck' in i[0]][-1].Restart(numberIntervals=1)
    # Immer am Ende von Rad-Zurueck den vollen Field Output make_rail_2d
    if if_full_out not in ['Yes', 'No']:
        model.fieldOutputRequests['F-Output-1'].deactivate('Kontakt-UY002')
        # for the last 5 Steps:
        model.FieldOutputRequest(name='F-Output-Ende', createStepName='Kontakt-UY'+str(nCycles).zfill(3),
                                 variables=('S', 'PE', 'PEEQ', 'CNAREA', 'CFORCE',
                                 'LE', 'U', 'CF', 'CSTRESS', 'COORD', 'IVOL', 'ALPHAN','ALPHA'), numIntervals=2)
    return

def evaluate_odb(odb_name,b_pfad=150,ob_rad_starr='no'):
    # neu, ueber FieldOutput / Values
    odb = session.openOdb(name=odb_name + '.odb')
    def get_name(inst):
        # Weil bei inst==None: inst.name : Error
        if inst == None:
            return ''
        else:
            return inst.name
    #
    def get_rail_vals(field_out, if_el=0):
        # Liste aus Liste/Skalar
        def lis(x):
            if type(x) == float:
                return [x]
            else:
                return list(x)
        if if_el:
            list_out = [[i.elementLabel] + lis(i.data) for i in field_out.values
                        if 'SCHIENE' in get_name(i.instance)]
        else:
            list_out = [[i.nodeLabel] + lis(i.data) for i in field_out.values
                        if 'SCHIENE' in get_name(i.instance)]
        return np.array(list_out)[:, 1:]
    #
    # get a path for cont. pressure
    def auswerten_pfad(odb,i_step,time_frame,b,str_out='mid'):
        # get data from odb
        vp1 = session.viewports['Viewport: 1']
        vp1.setValues(displayedObject=odb)
        vp1.odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
        #
        st = odb.steps.values()[i_step]
        t_vals = [(abs(fr.frameValue-time_frame),i) for i,fr in enumerate(st.frames)]
        i_frame = sorted(t_vals)[0][1]
        #np.savetxt('test-fram_out.dat',np.array([t_vals]))
        vp1.odbDisplay.setFrame(step=i_step, frame=i_frame)
        # make a path
        pth = session.Path(name='Path-2', type=POINT_LIST, expression=((-b/2,0,0),
                                                                       (b/2,0,0)))
        #
        vp1.odbDisplay.setPrimaryVariable(variableLabel='CPRESS', outputPosition=ELEMENT_NODAL, )
        # get the S22 data at the path
        cp1=session.XYDataFromPath(name='XYData-1', path=pth, includeIntersections=True,
                               projectOntoMesh=False, pathStyle=PATH_POINTS, numIntervals=300,
                               projectionTolerance=0, shape=UNDEFORMED, labelType=X_COORDINATE)
        #
        vp1.odbDisplay.setPrimaryVariable(variableLabel='CSHEAR1', outputPosition=ELEMENT_NODAL, )
        # get the S22 data at the path
        cs1=session.XYDataFromPath(name='XYData-2', path=pth, includeIntersections=True,
                               projectOntoMesh=False, pathStyle=PATH_POINTS, numIntervals=300,
                               projectionTolerance=0, shape=UNDEFORMED, labelType=X_COORDINATE)
        #
        data_list = np.array([[i[0],i[1],j[1]] for i,j in zip(cp1.data,cs1.data)])
        # write to file
        with file(odb.name[:-4]+'_'+str((i_step-2)/5+1)+'_'+str_out+'_cp_res.dat','w') as f:
            f.write(','.join(['x coord [mm]','CPRESS [MPa]','CSHEAR [MPa]'])+'\n')
            np.savetxt(f,data_list, delimiter=',')
        return
    # -------------------------------------------------------------------------------
    # Alle Spannungen und Verschiebungen in Files schreiben
    frame0 = odb.steps.values()[0].frames[0]
    #
    field_coord = frame0.fieldOutputs['COORD']
    ip_array_coord = field_coord.getSubset(position=INTEGRATION_POINT)
    node_array_coord = field_coord.getSubset(position=NODAL)
    #
    coord_n = get_rail_vals(node_array_coord, if_el=0)
    coord_ip = get_rail_vals(ip_array_coord, if_el=1)
    #
    #np.savetxt('test.dat', coord_n)  # [coord_n[:,0].argsort()])
    #np.savetxt('test2.dat', coord_ip)  # [coord_ip[:,0].argsort()])
    # Alle Steps die 'Rad_Zurueck' enthalten
    steps_back = [i for i in odb.steps.keys() if 'Zurueck' in i]
    #
    for i_step, step_name in enumerate(steps_back):
        # jeweiligen Frame
        frameEnd = odb.steps[step_name].frames[-1]
        #
        field_s_ip = frameEnd.fieldOutputs['S'].getSubset(position=INTEGRATION_POINT)
        field_peeq_ip = frameEnd.fieldOutputs['PEEQ'].getSubset(position=INTEGRATION_POINT)
        field_ivol_ip = frameEnd.fieldOutputs['IVOL'].getSubset(position=INTEGRATION_POINT)
        field_u = frameEnd.fieldOutputs['U'].getSubset(position=NODAL)
        # Backstresses
        if 'plastic' not in ob_rad_starr:
            if 'ALPHA1' in frameEnd.fieldOutputs.keys():
                fields_alpha = [j for i, j in frameEnd.fieldOutputs.items() if 'ALPHA' in i][1:]
            else:
                fields_alpha = [j for i, j in frameEnd.fieldOutputs.items() if 'ALPHA' in i]
            ####################### Problem ########################################
            alpha_list = np.hstack((get_rail_vals(i, if_el=1) for i in fields_alpha))
        #
        #np.savetxt('test_alphas.dat', alpha_list)
        #
        s_list = get_rail_vals(field_s_ip, if_el=1)
        ivol_list = get_rail_vals(field_ivol_ip, if_el=1)
        peeq_list = get_rail_vals(field_peeq_ip, if_el=1)
        u_list = get_rail_vals(field_u, if_el=0)
        #
        if len(steps_back) == 1:
            out_str = odb_name
        else:
            out_str = odb_name[:-3] + str(i_step + 1).zfill(3)
        # make cont. output path
        auswerten_pfad(odb,2+i_step*5,0.5,b_pfad,'mid')
        auswerten_pfad(odb,2+i_step*5,1,b_pfad,'end')
        # Ausgabe
        np.savetxt(out_str + '_s_field.dat', np.hstack((coord_ip, s_list, ivol_list)),
                   delimiter=',    ')
        if 'plastic' not in ob_rad_starr:
            np.savetxt(out_str + '_al_field.dat', np.hstack((coord_ip, peeq_list, alpha_list)),
                       delimiter=',    ')
        np.savetxt(out_str + '_u_field.dat', np.hstack((coord_n, u_list)), delimiter=',    ')
        # del_h bei x=0, y=0
        del_h = u_list[(-TOL < coord_n[:, 0])*(coord_n[:, 0] < TOL) * (coord_n[:, 1] > -TOL)][0,1]
    return del_h

# Funktionen beim 2D Rollmodell, ifRoll: ob Symmetrie in x-Richtung ------------
def make_rail_2d(model, input_d):
    """ Schienenparts- und Sets erstellen """
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])/2.
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    TOL = elFF / 10
    rSchiene = 0 #input_d['Radius Schiene']
    elem_type = input_d['Geometrievariante'][3]
    # feiner Part
    sketch0 = model.ConstrainedSketch(name='sketchF', sheetSize=20.0)
    sketch0.rectangle(point1=(-bF, -hF), point2=(bF, 0))
    schieneF = model.Part(dimensionality=TWO_D_PLANAR, name='Schiene-Fein', type=DEFORMABLE_BODY)
    schieneF.BaseShell(sketch=sketch0)
    # Partitionieren
    sketch0c = model.ConstrainedSketch(name='partitionen0', sheetSize=20.0)
    sketch0c.Line(point1=(-bF, -hFF), point2=(bF, -hFF))
    sketch0c.Line(point1=(-bFF, -hF), point2=(-bFF, 0))
    sketch0c.Line(point1=(bFF, -hF), point2=(bFF, 0))
    sketch0c.Line(point1=(0, -hF), point2=(0, 0))# ?
    schieneF.PartitionFaceBySketch(faces=schieneF.faces[:], sketch=sketch0c)
    # grober Part
    sketch1 = model.ConstrainedSketch(name='sketchG', sheetSize=20.0)
    sketch1.Line(point1=(-bG, -hG), point2=(-bG, 0))
    sketch1.Line(point1=(-bG, 0), point2=(-bF, 0))
    sketch1.Line(point1=(-bF, 0), point2=(-bF, -hF))
    sketch1.Line(point1=(-bF, -hF), point2=(bF, -hF))
    sketch1.Line(point1=(bF, -hF), point2=(bF, 0))
    sketch1.Line(point1=(bF, 0), point2=(bG, 0))
    sketch1.Line(point1=(bG, 0), point2=(bG, -hG))
    sketch1.Line(point1=(bG, -hG), point2=(-bG, -hG))
    schieneG = model.Part(dimensionality=TWO_D_PLANAR, name='Schiene-Grob', type=DEFORMABLE_BODY)
    schieneG.BaseShell(sketch=sketch1)
    # Partitionieren
    sketch1c = model.ConstrainedSketch(name='partitionen1', sheetSize=20.0)
    sketch1c.Line(point1=(-bG, -hF), point2=(bG, -hF))
    sketch1c.Line(point1=(-bF, -hG), point2=(-bF, -hF))
    sketch1c.Line(point1=(bF, -hG), point2=(bF, -hF))
    sketch1c.Line(point1=(0, -hG), point2=(0, -hF)) # ?
    schieneG.PartitionFaceBySketch(faces=schieneG.faces[:], sketch=sketch1c)
    # Sets erstellen
    schieneF.Set(faces=schieneF.faces[:], name='ALL')
    schieneG.Set(faces=schieneG.faces[:], name='ALL')
    # Schiene Sets: Listen
    tieSF = selectFull(schieneF.edges, [-bF], [], []) + selectFull(schieneF.edges, [bF], [], []) + \
            selectFull(schieneF.edges, [], [-hF], [])
    tieSG = selectFull(schieneG.edges, [-bF, bF], [-hF, 0], [])
    contS = selectFull(schieneF.edges, [], [0], [])
    contMitte = selectFull(schieneF.edges, [-bFF, bFF], [0], [])
    seitenSG = selectFull(schieneG.edges, [-bG], [], []) + selectFull(schieneG.edges, [bG], [], [])
    untenSG = selectFull(schieneG.edges, [], [-hG], [])
    # Sets und surfaces der Schiene (?)
    schieneF.Surface(name='tie', side1Edges=tieSF)
    schieneF.Set(name='tie', edges=tieSF)
    schieneF.Surface(name='contact', side1Edges=contS)
    schieneF.Set(name='contact', edges=contS)
    schieneF.Set(name='contact-mitte', edges=contMitte)
    # Laenge der Kontaktknoten ermiteln
    lCont = bFF / (len(schieneF.sets['contact-mitte'].nodes) - 1)
    #
    schieneG.Surface(name='tie', side1Edges=tieSG)
    schieneG.Set(name='tie', edges=tieSG)
    schieneG.Set(edges=seitenSG, name='seiten')
    schieneG.Set(edges=untenSG, name='unten')
    # Radius an Schienenoberflaeche
    if rSchiene != 0:
        sketchC = model.ConstrainedSketch(name='sketchCut', sheetSize=20.0)
        sketchC.ArcByCenterEnds(center=(0, -rSchiene), point1=(-rSchiene, -rSchiene),
                                point2=(rSchiene, -rSchiene), direction=CLOCKWISE)
        sketchC.Line(point1=(-rSchiene, -rSchiene), point2=(-rSchiene, hF))
        sketchC.Line(point1=(-rSchiene, hF), point2=(rSchiene, hF))
        sketchC.Line(point1=(rSchiene, hF), point2=(rSchiene, -rSchiene))
        schieneG.Cut(sketch=sketchC)
        schieneF.Cut(sketch=sketchC)
        contS = selectFullC(schieneF.edges, [rSchiene], [], [], [[0, -rSchiene, 0], [0, -rSchiene, 1]])
        schieneF.Surface(name='contact', side1Edges=contS)
    # Vernetzen der Schienenparts
    schieneF.seedPart(size=elFF)
    edgF = selectFull(schieneF.edges, [], [-hF + TOL, -hFF - TOL], [])
    edgF2 = selectFull(schieneF.edges, [-bF + TOL, -bFF - TOL], [], [])
    edgF3 = selectFull(schieneF.edges, [bFF + TOL, bF - TOL], [], [])
    edgeBiasedList(schieneF, edgF, 2, 1, [], elF, elFF)
    edgeBiasedList(schieneF, edgF2, 1, 1, [], elF, elFF)
    edgeBiasedList(schieneF, edgF3, 1, -1, [], elF, elFF)
    if biasS != 1.:
        edgF4 = selectFull(schieneF.edges, [], [-hFF + TOL, -TOL], [])
        edgeBiasedList(schieneF, edgF4, 2, 1, [], elFF, elFF / biasS)
    schieneF.generateMesh()
    # grob
    schieneG.seedPart(size=elF)
    edgG = selectFull(schieneG.edges, [], [-hG + TOL, -hF - TOL], [])
    edgG2 = selectFull(schieneG.edges, [-bG + TOL, -bF - TOL], [], [])
    edgG3 = selectFull(schieneG.edges, [bF + TOL, bG - TOL], [], [])
    edgeBiasedList(schieneG, edgG, 2, 1, [], elG, elF)
    edgeBiasedList(schieneG, edgG2, 1, 1, [], elG, elF)
    edgeBiasedList(schieneG, edgG3, 1, -1, [], elG, elF)
    schieneG.generateMesh()
    # ob plane strain ('PE')
    if elem_type == 'PE':
        for part in [schieneF,schieneG]:
            part.setElementType(elemTypes=(
                mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD, secondOrderAccuracy=OFF,
                hourglassControl=DEFAULT, distortionControl=DEFAULT), mesh.ElemType(
                elemCode=CPE3, elemLibrary=STANDARD)), regions=(part.faces[:],))
    return [schieneF, schieneG, lCont]

def make_rail_map_2d(model, input_d):
    """ Schienenparts- und Sets erstellen """
    #[bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])/2.
    bFF = input_d['Rolllaenge']/2.
    b_out = input_d['Rolllaenge out']
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    el_top = elFF/biasS
    TOL = elFF / 10
    rSchiene = 0 #input_d['Radius Schiene']
    elem_type = input_d['Geometrievariante'][3]
    # feiner Part
    s = model.ConstrainedSketch(name='sketchF', sheetSize=20.0)
    s.Line(point1=(-bFF,0),point2=(bFF+b_out,0))
    s.Line(point1=(-bFF,-hFF),point2=(-bFF,0))
    s.Line(point1=(-bFF,-hFF),point2=(bFF,-hFF))
    s.Line(point1=(bFF,-hFF),point2=(bFF,-el_top))
    s.Line(point1=(bFF,-el_top),point2=(bFF+b_out,-el_top))
    s.Line(point1=(bFF+b_out,-el_top),point2=(bFF+b_out,0))
    schieneF = model.Part(dimensionality=TWO_D_PLANAR, name='Schiene-Fein', type=DEFORMABLE_BODY)
    schieneF.BaseShell(sketch=s)
    # Partitionieren
    sketch0c = model.ConstrainedSketch(name='partitionen0', sheetSize=20.0)
    sketch0c.Line(point1=(-bFF*2, -el_top), point2=(bFF*2, -el_top))
    sketch0c.Line(point1=(bFF, -el_top*2), point2=(bFF, 0))
    schieneF.PartitionFaceBySketch(faces=schieneF.faces[:], sketch=sketch0c)
    # Sets erstellen
    schieneF.Set(faces=schieneF.faces[:], name='ALL')
    # Sets und surfaces der Schiene
    schieneF.Surface(name='CONTACT', side1Edges=schieneF.edges.getByBoundingBox(yMin=-TOL))
    schieneF.Set(name='CONTACT', edges=schieneF.edges.getByBoundingBox(yMin=-TOL))
    schieneF.Set(name='LINKS', edges=schieneF.edges.getByBoundingBox(xMax=-bFF+TOL))
    schieneF.Set(name='RECHTS', edges=schieneF.edges.getByBoundingBox(xMin=bFF-TOL, xMax=bFF+TOL))
    schieneF.Set(name='UNTEN', edges=schieneF.edges.getByBoundingBox(yMax=-hFF+TOL))
    # Vernetzen der Schienenparts
    schieneF.seedPart(size=elFF)
    edgeBiasedList(schieneF, schieneF.sets['LINKS'].edges.getByBoundingBox(yMax=-el_top+TOL), 
                   2, 1, [], elFF, elFF/biasS)
    edgeBiasedList(schieneF, schieneF.sets['RECHTS'].edges.getByBoundingBox(yMax=-el_top+TOL), 
                2, 1, [], elFF, elFF/biasS)
    schieneF.generateMesh()
    # ob plane strain ('PE')
    if elem_type == 'PE':
        for part in [schieneF]:
            part.setElementType(elemTypes=(
                mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD, secondOrderAccuracy=OFF,
                hourglassControl=DEFAULT, distortionControl=DEFAULT), mesh.ElemType(
                elemCode=CPE3, elemLibrary=STANDARD)), regions=(part.faces[:],))
    return [schieneF, elFF]

def make_wheel_2d(model, input_d):
    """ Rad aufbauen und vernetzen """
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])/2.
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    rRad = input_d['Radius Rad']
    wheel_rigid = input_d['ob Rad starr']
    elem_type = input_d['Geometrievariante'][3]
    TOL = elFF / 8

    if wheel_rigid == 'yes':
        # Starres "Rad" aufbauen
        sketchRF = model.ConstrainedSketch(name='radFein', sheetSize=200.0)
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE, point1=(-rRad, rRad), point2=(rRad,rRad))
        # Part erstellen
        radF = model.Part(dimensionality=TWO_D_PLANAR, name='Rad-Starr', type=DISCRETE_RIGID_SURFACE)
        radF.BaseWire(sketch=sketchRF)
        # Sets and reference Point
        radF.Surface(name='contact', side2Edges=radF.edges[:])
        refP = radF.ReferencePoint(point=(0.0, rRad, 0.0))
        radF.Set(name='RP', referencePoints=(radF.referencePoints[refP.id],))
        #
        radF.seedPart(size=elFF/3.)
        radF.generateMesh()
        #
        assembly = model.rootAssembly
        instRF = assembly.Instance(dependent=ON, name='Rad-Starr-1', part=radF)
        assembly.Set(referencePoints=(instRF.referencePoints[refP.id],), name='RP-Rad')
        return [radF, [], 0, 0]
    else:
        def getXY(rGes, phi, y0):
            # Input: RadRadius r, Winkel phi, Radius Kurve: rGes-y0, in Hoehe y0
            # Output: [x,y] Koordinaten des Punktes
            return [(rGes - y0) * sin(phi), (rGes - y0) - cos(phi) * (rGes - y0) + y0]

        # feiner Radteil
        sketchRF = model.ConstrainedSketch(name='radFein', sheetSize=200.0)
        x1 = getXY(rRad, 2. * bF / rRad, 0)
        x2 = getXY(rRad, 2. * bF / rRad, hF)
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(0.0, 0.0), point2=(x1[0], x1[1]))
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(0.0, hF), point2=(x2[0], x2[1]))
        sketchRF.Line(point1=(0.0, 0.), point2=(0.0, hF))
        sketchRF.Line(point1=(x1[0], x1[1]), point2=(x2[0], x2[1]))
        radF = model.Part(dimensionality=TWO_D_PLANAR, name='Rad-Fein', type=DEFORMABLE_BODY)
        radF.BaseShell(sketch=sketchRF)
        # feines Rad- Partitionierung
        sketchRFp = model.ConstrainedSketch(name='radFeinP', sheetSize=200.0)
        x1p = getXY(rRad, (bF / rRad - bFF / rRad), 0)
        x2p = getXY(rRad, (2 * bF / rRad - (bF / rRad - bFF / rRad)), 0)
        sketchRFp.CircleByCenterPerimeter(center=(0.0, rRad), point1=(0, hFF))
        sketchRFp.Line(point1=(0.0, rRad), point2=(x1p[0], x1p[1]))
        sketchRFp.Line(point1=(0.0, rRad), point2=(x2p[0], x2p[1]))
        radF.PartitionFaceBySketch(faces=radF.faces[:], sketch=sketchRFp)
        # Rad Grob- Geometrie
        sketchRG = model.ConstrainedSketch(name='radGrob', sheetSize=200.0)
        angGrob = 2. * bG / rRad
        angFein = 2. * bF / rRad
        # ang1 war falsch?!
        ang0 = -(angGrob / 2. - bF / rRad)
        ang1 = angGrob + ang0#(angGrob / 2 - bF / rRad)
        #print_cmd(ang0)
        #print_cmd(ang1)
        p0rG = getXY(rRad, ang0, 0)
        p1rG = getXY(rRad, ang0, hG)
        pp0rG = getXY(rRad, ang1, 0)
        pp1rG = getXY(rRad, ang1, hG)
        #
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(p1rG[0], p1rG[1]),
                                 point2=(pp1rG[0], pp1rG[1]))
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(p0rG[0], p0rG[1]), point2=(0., 0.))
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(x1[0], x1[1]), point2=(pp1rG[0], pp1rG[1]))
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(tuple(getXY(rRad, 0., hF))),
                                 point2=(tuple(getXY(rRad, angFein, hF))))
        sketchRG.Line(point1=(tuple(getXY(rRad, angFein, hF))), point2=(x1[0], x1[1]))
        sketchRG.Line(point1=(0., 0.), point2=(0, hF))
        sketchRG.Line(point1=(p1rG[0], p1rG[1]), point2=(p0rG[0], p0rG[1]))
        sketchRG.Line(point1=(pp1rG[0], pp1rG[1]), point2=(pp0rG[0], pp0rG[1]))
        radG = model.Part(dimensionality=TWO_D_PLANAR, name='Rad-Grob', type=DEFORMABLE_BODY)
        radG.BaseShell(sketch=sketchRG)
        # Partitionieren vom groben Rad
        sketchRGp = model.ConstrainedSketch(name='radGrobP', sheetSize=200.0)
        sketchRGp.CircleByCenterPerimeter(center=(0.0, rRad), point1=(0, hF))
        sketchRGp.Line(point1=(0.0, rRad), point2=(0., 0.))
        sketchRGp.Line(point1=(0.0, rRad), point2=(x1[0], x1[1]))
        radG.PartitionFaceBySketch(faces=radG.faces[:], sketch=sketchRGp)
        # Sets definieren
        radF.Set(faces=radF.faces[:], name='ALL')
        radG.Set(faces=radG.faces[:], name='ALL')
        axis = [[0, rRad, 0], [0, rRad, 1]]
        contR = selectFullC(radF.edges, [rRad], [], [], axis)
        tieF = (selectFullC(radF.edges, [rRad - hF], [], [], axis) +
                selectFullC(radF.edges, [], [0], [], axis) +
                selectFullC(radF.edges, [], [angFein], [], axis))
        tieG = selectFullC(radG.edges, [rRad - hF, rRad], [0, angFein], [], axis)
        # rigid parts ##########################################################
        #print_cmd(axis)
        #print_cmd(selectFullC(radG.edges, [rRad - hG], [], [], axis))
        #print_cmd(selectFullC(radG.edges, [], [ang0], [], axis))
        #print_cmd(selectFullC(radG.edges, [], [ang1], [], axis,if_print=1))
        #
        #mdb.saveAs(pathName='zwischenversion.cae')
        rigid_rad_g = (selectFullC(radG.edges, [rRad - hG], [], [], axis) +
                       selectFullC(radG.edges, [], [ang0], [], axis) +
                       selectFullC(radG.edges, [], [ang1-0.03,ang1+0.03], [], axis))
        radG.Set(edges=rigid_rad_g, name='rigid_cent')
        ########################################################################
        radG.Surface(name='tie', side1Edges=tieG)
        radF.Surface(name='tie', side1Edges=tieF)
        radF.Surface(name='contact', side1Edges=contR)
        refP = radG.ReferencePoint(point=(0.0, rRad, 0.0))
        radG.Set(name='RP', referencePoints=(radG.referencePoints[refP.id],))
        # Rad vernetzen
        radF.seedPart(size=elFF)
        linesF1 = selectFullC(radF.edges, [rRad - hF + 2 * TOL, rRad - hFF - 2 * TOL], [], [], axis)
        linesF2 = selectFullC(radF.edges, [], [TOL / 20, (bF - bFF) / rRad / 2 - TOL / 20], [], axis)
        linesF3 = selectFullC(radF.edges, [], [(bF + bFF) / rRad + TOL / 20, bF / rRad * 2 - TOL / 20], [], axis)
        edgeBiasedList(radF, linesF1, 1, 1, axis, elF, elFF)
        edgeBiasedList(radF, linesF2, 2, 1, axis, elF, elFF)
        edgeBiasedList(radF, linesF3, 2, -1, axis, elF, elFF)
        radF.generateMesh()
        # grober Teil vom Rad
        radG.seedPart(size=elF)
        linesF1 = selectFullC(radG.edges, [rRad - hG + 2 * TOL, rRad - hF - 2 * TOL], [], [], axis)
        linesF2 = selectFullC(radG.edges, [], [-(bG - bF) / rRad + TOL / 50, -TOL / 50], [], axis)
        linesF3 = selectFullC(radG.edges, [], [(bF * 2) / rRad + TOL / 50, (bG + bF) / rRad - TOL / 50], [], axis)
        edgeBiasedList(radG, linesF1, 1, 1, axis, elG, elF)
        edgeBiasedList(radG, linesF2, 2, 1, axis, elG, elF)
        edgeBiasedList(radG, linesF3, 2, -1, axis, elG, elF)
        radG.generateMesh()
        assembly = model.rootAssembly
        instRG = assembly.Instance(dependent=ON, name='Rad-Grob-1', part=radG)
        # ob plane strain ('PE')
        if elem_type == 'PE':
            for part in [radF,radG]:
                part.setElementType(elemTypes=(
                    mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD, secondOrderAccuracy=OFF,
                    hourglassControl=DEFAULT, distortionControl=DEFAULT), mesh.ElemType(
                    elemCode=CPE3, elemLibrary=STANDARD)), regions=(part.faces[:],))
        return [radF, radG, angFein, angGrob]

def make_wheel_map_2d(model, input_d):
    """ Rad aufbauen und vernetzen """
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])/2.
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    rRad = input_d['Radius Rad']
    wheel_rigid = input_d['ob Rad starr']
    elem_type = input_d['Geometrievariante'][3]
    TOL = elFF / 8

    def getXY(rGes, phi, y0):
        # Input: RadRadius r, Winkel phi, Radius Kurve: rGes-y0, in Hoehe y0
        # Output: [x,y] Koordinaten des Punktes
        return [(rGes - y0) * sin(phi), (rGes - y0) - cos(phi) * (rGes - y0) + y0]

    # feiner Radteil
    sketchRF = model.ConstrainedSketch(name='radFein', sheetSize=200.0)
    x1 = getXY(rRad, 2. * bFF / rRad, 0)
    x2 = getXY(rRad, 2. * bFF / rRad, hFF)
    sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                point1=(0.0, 0.0), point2=(x1[0], x1[1]))
    sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                point1=(0.0, hFF), point2=(x2[0], x2[1]))
    sketchRF.Line(point1=(0.0, 0.), point2=(0.0, hFF))
    sketchRF.Line(point1=(x1[0], x1[1]), point2=(x2[0], x2[1]))
    radF = model.Part(dimensionality=TWO_D_PLANAR, name='Rad-Fein', type=DEFORMABLE_BODY)
    radF.BaseShell(sketch=sketchRF)
    angFein = 2. * bFF / rRad
    # Sets definieren
    radF.Set(faces=radF.faces[:], name='ALL')
    axis = [[0, rRad, 0], [0, rRad, 1]]
    contR = selectFullC(radF.edges, [rRad], [], [], axis)
    tieF = (selectFullC(radF.edges, [rRad - hFF], [], [], axis) +
            selectFullC(radF.edges, [], [0], [], axis) +
            selectFullC(radF.edges, [], [angFein], [], axis))
    #
    radF.Set(name='COUPLING', edges=tieF)
    radF.Surface(name='CONTACT', side1Edges=contR)
    refP = radF.ReferencePoint(point=(0.0, rRad, 0.0))
    radF.Set(name='RP', referencePoints=(radF.referencePoints[refP.id],))
    # Rad vernetzen
    radF.seedPart(size=elFF)
    linesF1 = selectFullC(radF.edges, [rRad - hFF + 2 * TOL, rRad - 2 * TOL], [], [], axis)
    edgeBiasedList(radF, linesF1, 1, 1, axis, elFF, elFF/biasS)
    radF.generateMesh()
    assembly = model.rootAssembly
    instRF = assembly.Instance(dependent=ON, name='Rad-Fein-1', part=radF)
    # ob plane strain ('PE')
    if elem_type == 'PE':
        for part in [radF]:
            part.setElementType(elemTypes=(
                mesh.ElemType(elemCode=CPE4R, elemLibrary=STANDARD, secondOrderAccuracy=OFF,
                hourglassControl=DEFAULT, distortionControl=DEFAULT), mesh.ElemType(
                elemCode=CPE3, elemLibrary=STANDARD)), regions=(part.faces[:],))
    return [radF, angFein]

# Funktionen beim 3D Rollmodell ------------------------------------------------
def make_rail_3d(model, input_d, splineLG=[], splineLF=[]):
    # biasS: Faktor fuer biased seeds in Tiefe
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [tFF, tF, tG] = input_d['Abmessungen']['depth']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    TOL = tFF / 50
    #
    rSchiene = input_d['Radius Schiene']
    elem_type = input_d['Geometrievariante'][3]
    #
    sketchSF = model.ConstrainedSketch(name='sketch-SF', sheetSize=20.0)
    # wenn einfache Rundung mit Radius
    if splineLF == []:
        # Schiene aussen um dh weniger hoch
        dhFein = rSchiene - (rSchiene ** 2 - tF ** 2) ** 0.5
        #
        sketchSF.Line(point1=(0, 0), point2=(0, -hF))
        sketchSF.Line(point1=(0, -hF), point2=(-tF, -hF))
        sketchSF.Line(point1=(-tF, -hF), point2=(-tF, -dhFein))
        sketchSF.ArcByCenterEnds(center=(0, -rSchiene), direction=COUNTERCLOCKWISE,
                                 point1=(0.0, 0.0), point2=(-tF, -dhFein))
    else:
        # Wenn Spline fuer die Oberflaeche
        # splineLF: (x,y)-Werte, sortiert!
        dHges = -splineLF[0][2]
        sketchSF.Line(point1=(0, 0), point2=(0, -hF + dHges))
        sketchSF.Line(point1=(0, -hF + dHges), point2=(-tF, -hF + dHges))
        sketchSF.Line(point1=(-tF, -hF + dHges), point2=(-tF, splineLF[-1][2] + dHges))
        splineList = [[i[3], i[2] + dHges] for i in splineLF[:-1]] + [[-tF, splineLF[-1][2] + dHges]]
        print(splineList)
        sketchSF.Spline(points=tuple(splineList))
    #
    partSF = model.Part(dimensionality=THREE_D, name='Schiene-Fein', type=DEFORMABLE_BODY)
    partSF.BaseSolidExtrude(depth=bF, sketch=sketchSF)
    # Partitionieren
    cut0 = partSF.DatumPlaneByPrincipalPlane(offset=bF / 2, principalPlane=XYPLANE)
    cut1 = partSF.DatumPlaneByPrincipalPlane(offset=bF / 2 + (bFF) / 2, principalPlane=XYPLANE)
    cut2 = partSF.DatumPlaneByPrincipalPlane(offset=bF / 2 - (bFF) / 2, principalPlane=XYPLANE)
    cut3 = partSF.DatumPlaneByPrincipalPlane(offset=-tFF, principalPlane=YZPLANE)
    cut4 = partSF.DatumPlaneByPrincipalPlane(offset=-hFF, principalPlane=XZPLANE)
    #
    partSF.PartitionCellByDatumPlane(cells=partSF.cells[:], datumPlane=partSF.datums[cut0.id])
    partSF.PartitionCellByDatumPlane(cells=partSF.cells[:], datumPlane=partSF.datums[cut1.id])
    partSF.PartitionCellByDatumPlane(cells=partSF.cells[:], datumPlane=partSF.datums[cut2.id])
    partSF.PartitionCellByDatumPlane(cells=partSF.cells[:], datumPlane=partSF.datums[cut3.id])
    partSF.PartitionCellByDatumPlane(cells=partSF.cells[:], datumPlane=partSF.datums[cut4.id])
    # Schiene - grober Part
    # -------------------------------------------------------------
    # Schiene aussen um dh weniger hoch
    dhGrob = rSchiene - (rSchiene ** 2 - tG ** 2) ** 0.5
    #
    sketchSG = model.ConstrainedSketch(name='sketch-SG', sheetSize=20.0)
    # wenn einfache Rundung mit Radius
    if splineLG == []:
        sketchSG.Line(point1=(0, 0), point2=(0, -hG))
        sketchSG.Line(point1=(0, -hG), point2=(-tG, -hG))
        sketchSG.Line(point1=(-tG, -hG), point2=(-tG, -dhGrob))
        sketchSG.ArcByCenterEnds(center=(0, -rSchiene), direction=COUNTERCLOCKWISE,
                                 point1=(0.0, 0.0), point2=(-tG, -dhGrob))
    else:
        # Wenn Spline fuer die Oberflaeche
        # splineLF: (x,y)-Werte, sortiert!
        sketchSG.Line(point1=(0, 0), point2=(0, -hG + dHges))
        sketchSG.Line(point1=(0, -hG + dHges), point2=(-tG, -hG + dHges))
        sketchSG.Line(point1=(-tG, -hG + dHges), point2=(-tG, splineLG[-1][2] + dHges))
        splineList += [[i[3], i[2] + dHges] for i in splineLG[:-1]] + [[-tG, splineLG[-1][2] + dHges]]
        print(splineList)
        sketchSG.Spline(points=tuple(splineList))
    #
    partSG = model.Part(dimensionality=THREE_D, name='Schiene-Grob',
                        type=DEFORMABLE_BODY)
    partSG.BaseSolidExtrude(depth=bG, sketch=sketchSG)
    # Schneiden & Partitionieren
    sketchSGcut = model.ConstrainedSketch(name='cut-SchieneG', sheetSize=0.31, transform=
    partSG.MakeSketchTransform(sketchPlane=partSG.faces.findAt(
        (0.0, -hG / 2, bG / 2), ), sketchPlaneSide=SIDE1, sketchUpEdge=partSG.edges.findAt(
        (0.0, -hG / 2, 0.0), ), sketchOrientation=RIGHT, origin=(0.0, -hG, bG)))
    #
    sketchSGcut.rectangle(point1=((bG - bF) / 2, hG - hF), point2=((bG + bF) / 2, hG * 1.3))
    #
    partSG.CutExtrude(depth=tF, flipExtrudeDirection=OFF, sketch=sketchSGcut,
                      sketchOrientation=RIGHT, sketchPlane=partSG.faces.findAt((0.0, -hG / 2, bG / 2), ),
                      sketchPlaneSide=SIDE1, sketchUpEdge=partSG.edges.findAt((0.0, -hG / 2, 0.0), ))
    #
    cut0 = partSG.DatumPlaneByPrincipalPlane(offset=bG / 2, principalPlane=XYPLANE)
    cut1 = partSG.DatumPlaneByPrincipalPlane(offset=(bG + bF) / 2, principalPlane=XYPLANE)
    cut2 = partSG.DatumPlaneByPrincipalPlane(offset=(bG - bF) / 2, principalPlane=XYPLANE)
    cut3 = partSG.DatumPlaneByPrincipalPlane(offset=-tF, principalPlane=YZPLANE)
    cut4 = partSG.DatumPlaneByPrincipalPlane(offset=-hF, principalPlane=XZPLANE)
    #
    partSG.PartitionCellByDatumPlane(cells=partSG.cells[:], datumPlane=partSG.datums[cut0.id])
    partSG.PartitionCellByDatumPlane(cells=partSG.cells[:], datumPlane=partSG.datums[cut1.id])
    partSG.PartitionCellByDatumPlane(cells=partSG.cells[:], datumPlane=partSG.datums[cut2.id])
    partSG.PartitionCellByDatumPlane(cells=partSG.cells[:], datumPlane=partSG.datums[cut3.id])
    partSG.PartitionCellByDatumPlane(cells=partSG.cells[:], datumPlane=partSG.datums[cut4.id])
    # Sets und surfaces der Schiene
    partSF.Set(cells=partSF.cells[:], name='ALL')
    partSG.Set(cells=partSG.cells[:], name='ALL')
    # SF contact
    fCont = partSF.faces.getByBoundingBox(xMin=-tFF - TOL, xMax=+TOL,
                                          zMin=(bF - bFF) / 2 - TOL, zMax=(bF + bFF) / 2 + TOL, yMin=-hFF / 2 - TOL,
                                          yMax=TOL)
    partSF.Set(name='contact', faces=fCont)
    partSF.Surface(name='contact', side1Faces=fCont)
    lOben = partSF.edges.getByBoundingBox(xMin=-tF - TOL, xMax=+TOL,
                                          zMin=(bF) / 2 - TOL, zMax=(bF) / 2 + TOL, yMin=-hFF / 2 - TOL, yMax=TOL)
    partSF.Set(name='lOben', edges=lOben)
    # combine getBounding Dingse:
    tie1 = partSF.faces.getByBoundingBox(zMin=-TOL, zMax=+TOL, xMin=-bG, xMax=bG)
    tie2 = partSF.faces.getByBoundingBox(zMin=bF - TOL, zMax=bF + TOL, xMin=-bG, xMax=bG)
    tie3 = partSF.faces.getByBoundingBox(xMin=-tF - TOL, xMax=-tF + TOL, yMin=-bG, yMax=bG)
    tie4 = partSF.faces.getByBoundingBox(yMin=-hF - TOL, yMax=-hF + TOL, xMin=-bG, xMax=bG)
    #
    tieG = tie1 + tie2 + tie3 + tie4
    partSF.Set(name='tie', faces=tieG)
    # tie von Schiene-Grob
    partSG.Set(name='tie', faces=partSG.faces.findAt(((-tF / 2, -hF / 2, (bG - bF) / 2),),
                                                     ((-tF / 2, -hF / 2, (bG - bF) / 2 + TOL),),
                                                     ((-tF, -hF / 2, bG / 2 - TOL),),
                                                     ((-tF, -hF / 2, bG / 2 + TOL),), ((-tF / 2, -hF, bG / 2 + TOL),),
                                                     ((-tF / 2, -hF, bG / 2 - TOL),),
                                                     ((-tF / 2, -hF, bG / 2),), ((-tF / 2, -hF / 2, (bG + bF) / 2),), ))
    #
    partSG.Set(edges=partSG.edges.getByBoundingBox(xMin=-tG - TOL, xMax=-tF + TOL,
                                                   zMin=bG / 2 - TOL, zMax=bG / 2 + TOL, yMin=-hF / 2 - TOL, yMax=TOL),
               name='lOben')
    #
    partSG.Set(faces=partSG.faces.getByBoundingBox(yMin=-hG - TOL, yMax=-hG + TOL, xMin=-bG, xMax=bG),
               name='unten')
    partSG.Set(faces=partSG.faces.getByBoundingBox(zMin=-TOL, zMax=+TOL) +
                     partSG.faces.getByBoundingBox(zMin=bG - TOL, zMax=bG + TOL), name='seiten')
    # fuer z-Symmetrie
    partSG.Set(faces=partSG.faces.getByBoundingBox(xMin=-TOL, xMax=+TOL), name='zSym')
    partSF.Set(faces=partSF.faces.getByBoundingBox(xMin=-TOL, xMax=+TOL), name='zSym')
    partSF.seedPart(size=elFF)
    partSG.seedPart(size=elF)
    # feiner Part
    edgF1a = selectFull(partSF.edges, [], [], [+TOL, (bF - bFF) / 2 - TOL])
    edgF1b = selectFull(partSF.edges, [], [], [(bF + bFF) / 2 + TOL, bF - TOL])
    edgF2 = selectFull(partSF.edges, [], [-hF + TOL, -hFF - TOL], [])
    edgF3 = selectFull(partSF.edges, [-tF + TOL, -tFF - TOL], [], [])
    # Zusatz: oben biased
    edgF4 = selectFull(partSF.edges, [], [-hFF * 0.9 + TOL, -hFF * 0.1 - TOL], [])
    edgeBiasedList(partSF, edgF4, 2, 1, [], elFF, elFF / biasS)
    #
    edgeBiasedList(partSF, edgF1a, 3, 1, [], elF, elFF)
    edgeBiasedList(partSF, edgF1b, 3, -1, [], elF, elFF)
    edgeBiasedList(partSF, edgF2, 2, 1, [], elF, elFF)
    edgeBiasedList(partSF, edgF3, 1, 1, [], elF, elFF)
    partSF.generateMesh()
    # grober Schienenpart
    edgF1a = selectFull(partSG.edges, [], [], [+TOL, (bG - bF) / 2 - TOL])
    edgF1b = selectFull(partSG.edges, [], [], [(bG + bF) / 2 + TOL, bG - TOL])
    edgF2 = selectFull(partSG.edges, [], [-hG + TOL, -hF - TOL], [])
    edgF3 = selectFull(partSG.edges, [-tG + TOL, -tF - TOL], [], [])
    edgeBiasedList(partSG, edgF1a, 3, 1, [], elG, elF)
    edgeBiasedList(partSG, edgF1b, 3, -1, [], elG, elF)
    edgeBiasedList(partSG, edgF2, 2, 1, [], elG, elF)
    edgeBiasedList(partSG, edgF3, 1, 1, [], elG, elF)
    partSG.generateMesh()
    return [partSF, partSG]

def make_wheel_3d(model, input_d):
    [bFF, bF, bG] = np.array(input_d['Abmessungen']['length'])
    [hFF, hF, hG] = input_d['Abmessungen']['height']
    [tFF, tF, tG] = input_d['Abmessungen']['depth']
    [elFF, elF, elG, biasS] = input_d['Abmessungen']['element length']
    rRad = input_d['Radius Rad']
    wheel_rigid = input_d['ob Rad starr']
    TOL = elFF / 50.
    #
    if wheel_rigid == 'yes':
        # starres "Rad": Halbkugel an Kegelspitze aufbauen
        x0,y0 = (rRad*sin(pi/4),rRad*(1-sin(pi/4)))
        sketchRF = model.ConstrainedSketch(name='sketch-RF', sheetSize=200.0)
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(0, 0), point2=(x0,y0))
        sketchRF.Line(point1=(x0,y0), point2=(x0+x0*3,y0+x0*3))
        sketchRF.ConstructionLine(point1=(0., 0.), point2=(0., 1.))
        # Part erstellen
        partRF = model.Part(dimensionality=THREE_D, name='Rad-Starr', type=DISCRETE_RIGID_SURFACE)
        partRF.BaseShellRevolve(angle=180.0, flipRevolveDirection=ON, sketch=sketchRF)
        # RP und Surfaces/Sets
        partRF.Surface(name='contact', side2Faces=partRF.faces[:])
        refP = partRF.ReferencePoint(point=(0.0, rRad, 0.0))
        partRF.Set(name='RP', referencePoints=(partRF.referencePoints[refP.id],))
        #
        partRF.seedPart(size=elFF/3.)
        partRF.generateMesh()
        #
        assembly = model.rootAssembly
        instRF = assembly.Instance(dependent=ON, name='Rad-Starr-1', part=partRF)
        assembly.Set(referencePoints=(instRF.referencePoints[refP.id],), name='RP-Rad')
        #
        return [partRF, 0]
    else:
        def getXY(r, phi, y0):
            return [r * sin(phi), r - cos(phi) * r + y0]

        # feines Rad- Geometrie
        sketchRF = model.ConstrainedSketch(name='sketch-RF', sheetSize=200.0)
        #
        x1 = getXY(rRad, bF / (rRad), 0)
        x2 = getXY(rRad - hF, bF / (rRad), hF)
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(0, 0), point2=(x1[0], x1[1]))
        sketchRF.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(0, hF), point2=(x2[0], x2[1]))
        sketchRF.Line(point1=(x1[0], x1[1]), point2=(x2[0], x2[1]))
        sketchRF.Line(point1=(0, 0), point2=(0, hF))
        #
        partRF = model.Part(dimensionality=THREE_D, name='Rad-Fein', type=DEFORMABLE_BODY)
        partRF.BaseSolidExtrude(depth=tF, sketch=sketchRF)
        # feines Rad- Partitionierung
        sketchRFp = model.ConstrainedSketch(name='partFP', sheetSize=200.0)
        sketchRFp.CircleByCenterPerimeter(center=(0.0, rRad), point1=(0, hFF))
        #
        partRF.PartitionFaceBySketch(faces=partRF.faces.findAt(((TOL, hF / 2, 0.0),)),
                                     sketch=sketchRFp, sketchUpEdge=partRF.edges.findAt((0.0, hF / 2, 0.0), ))
        #
        zDir = partRF.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
        # Punkt fuer Auswahl
        pointT = getXY(rRad - hFF, bF / rRad / 4, hFF)
        #
        partRF.PartitionCellByExtrudeEdge(cells=partRF.cells[:], edges=(
            partRF.edges.findAt((pointT[0], pointT[1], 0.0), ),), line=
                                          partRF.datums[zDir.id], sense=FORWARD)
        #
        cut1 = partRF.DatumPlaneByPrincipalPlane(offset=tFF, principalPlane=XYPLANE)
        cut0 = partRF.DatumPlaneByPrincipalPlane(offset=0, principalPlane=YZPLANE)
        #
        rp = partRF.ReferencePoint(point=(0.0, rRad, 0.0))
        #
        axisC = partRF.DatumAxisByParToEdge(edge=partRF.edges.findAt((0.0, 0.0,
                                                                      tF / 2), ), point=partRF.referencePoints[rp.id])
        #
        cut2 = partRF.DatumPlaneByRotation(angle=(bF - bFF) / (2 * rRad * pi) * 180,
                                           axis=partRF.datums[axisC.id], plane=partRF.datums[cut0.id])
        cut3 = partRF.DatumPlaneByRotation(angle=(bF + bFF) / (2 * rRad * pi) * 180,
                                           axis=partRF.datums[axisC.id], plane=partRF.datums[cut0.id])
        #
        partRF.PartitionCellByDatumPlane(cells=partRF.cells[:], datumPlane=partRF.datums[cut1.id])
        partRF.PartitionCellByDatumPlane(cells=partRF.cells[:], datumPlane=partRF.datums[cut2.id])
        partRF.PartitionCellByDatumPlane(cells=partRF.cells[:], datumPlane=partRF.datums[cut3.id])
        # Rad Grob- Geometrie
        # -------------------------------------------------------------------------
        sketchRG = model.ConstrainedSketch(name='sketch-RG', sheetSize=200.0)
        #
        angGrob = bG / rRad
        angFein = bF / rRad
        ang0 = (angGrob - angFein) / 2
        ang1 = (angGrob + angFein) / 2
        #
        p0rG = getXY(rRad, -ang0, 0)
        p1rG = getXY(rRad - hG, -ang0, hG)
        #
        pp0rG = getXY(rRad, ang1, 0)
        pp1rG = getXY(rRad - hG, ang1, hG)
        #
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(p1rG[0], p1rG[1]), point2=(pp1rG[0], pp1rG[1]))
        sketchRG.ArcByCenterEnds(center=(0, rRad), direction=COUNTERCLOCKWISE,
                                 point1=(p0rG[0], p0rG[1]), point2=(pp0rG[0], pp0rG[1]))
        sketchRG.Line(point1=(p0rG[0], p0rG[1]), point2=(p1rG[0], p1rG[1]))
        sketchRG.Line(point1=(pp1rG[0], pp1rG[1]), point2=(pp0rG[0], pp0rG[1]))
        #
        partRG = model.Part(dimensionality=THREE_D, name='Rad-Grob', type=DEFORMABLE_BODY)
        partRG.BaseSolidExtrude(depth=tG, sketch=sketchRG)
        # Partitionieren vom groben Rad
        cut1 = partRG.DatumPlaneByPrincipalPlane(offset=tF, principalPlane=XYPLANE)
        cut0 = partRG.DatumPlaneByPrincipalPlane(offset=0, principalPlane=YZPLANE)
        #
        rpRG = partRG.ReferencePoint(point=(0.0, rRad, 0.0))
        axisC = partRG.DatumAxisByParToEdge(edge=partRG.edges.findAt((p0rG[0], p0rG[1],
                                                                      tG / 2), ), point=partRG.referencePoints[rpRG.id])
        cut2 = partRG.DatumPlaneByRotation(angle=-(angFein / pi) * 180,
                                           axis=partRG.datums[axisC.id], plane=partRG.datums[cut0.id])
        #
        sketchRGp = model.ConstrainedSketch(name='partGP', sheetSize=200.0)
        sketchRGp.CircleByCenterPerimeter(center=(0.0, rRad), point1=(0, hF))
        #
        partRG.PartitionCellByDatumPlane(cells=partRG.cells[:], datumPlane=partRG.datums[cut0.id])
        #
        partRG.PartitionFaceBySketch(faces=partRG.faces.getByBoundingBox(zMin=0, zMax=0, xMin=-bG, xMax=bG)
                                     , sketch=sketchRGp, sketchUpEdge=partRG.edges.findAt((0.0, hG / 2, 0.0), ))
        lP1 = getXY(rRad - hF, -(bG - bF) / rRad / 4, hF)
        lP2 = getXY(rRad - hF, bF / rRad / 2, hF)
        #
        zDir = partRG.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
        partRG.PartitionCellByExtrudeEdge(cells=partRG.cells[:], edges=(
            partRG.edges.findAt((lP1[0], lP1[1], 0.0), ), partRG.edges.findAt((lP2[0], lP2[1], 0.0), ),), line=
                                          partRG.datums[zDir.id], sense=FORWARD)
        #
        partRG.PartitionCellByDatumPlane(cells=partRG.cells[:], datumPlane=partRG.datums[cut1.id])
        partRG.PartitionCellByDatumPlane(cells=partRG.cells[:], datumPlane=partRG.datums[cut2.id])
        # schneiden vom Part
        sketchRGcut = model.ConstrainedSketch(name='cut-Rad-Grob', sheetSize=0.31, transform=
        partRG.MakeSketchTransform(sketchPlane=partRG.faces.findAt(
            (hF / 4, hF / 2, 0.), ), sketchPlaneSide=SIDE1, sketchUpEdge=partRG.edges.findAt(
            (0.0, hF / 2, 0.0), ), sketchOrientation=RIGHT, origin=(0.0, 0., 0)))
        #
        sketchRGcut.ArcByCenterEnds(center=(0, rRad), direction=CLOCKWISE,
                                    point1=(0.0, 0.0), point2=(-x1[0], x1[1]))
        sketchRGcut.ArcByCenterEnds(center=(0, rRad), direction=CLOCKWISE,
                                    point1=(0.0, hF), point2=(-x2[0], x2[1]))
        sketchRGcut.Line(point1=(0.0, 0.), point2=(0.0, hF))
        sketchRGcut.Line(point1=(-x1[0], x1[1]), point2=(-x2[0], x2[1]))
        #
        partRG.CutExtrude(depth=tF, flipExtrudeDirection=OFF, sketch=sketchRGcut,
                          sketchOrientation=RIGHT, sketchPlane=partRG.faces.findAt((hF / 4, hF / 2, 0.), ),
                          sketchPlaneSide=SIDE1, sketchUpEdge=partRG.edges.findAt((0.0, hF / 2, 0.0), ))
        # Sets fuer die Rad-Parts
        partRF.Set(cells=partRF.cells[:], name='ALL')
        partRG.Set(cells=partRG.cells[:], name='ALL')
        #
        # Alle Sets erstellen mit den Funktionen
        axis = [[0, rRad, 0], [0, -1, 0]]
        # feiner Radpart
        contactF = selectFullC(partRF.faces, [rRad - TOL, rRad + TOL],
                               [(bF - bFF) / 2. / rRad + TOL / rRad, (bF + bFF) / 2. / rRad - TOL / rRad], [TOL, tF - TOL],
                               axis)
        partRF.Surface(name='contact', side1Faces=contactF)
        tieF = selectFullC(partRF.faces, [], [], [tF - TOL, tF + TOL], axis) + selectFullC(partRF.faces, [],
                                                                                           [-TOL / rRad, TOL / rRad], [],
                                                                                           axis) + \
               selectFullC(partRF.faces, [], [bF / rRad - TOL / rRad, bF / rRad + TOL / rRad], [], axis) + selectFullC(
            partRF.faces, [rRad - hF - TOL, rRad - hF + TOL], [], [], axis)
        partRF.Surface(name='tie', side1Faces=tieF)
        # grober Radpart
        tieG = selectFullC(partRG.faces, [rRad - hF - TOL, rRad + TOL], [-TOL / rRad, bF / rRad + TOL / rRad],
                           [TOL, tF + TOL], axis)
        partRG.Surface(name='tie', side1Faces=tieG)
        rigidG = selectFullC(partRG.faces, [rRad - hG - TOL, rRad - hG + TOL], [], [], axis) + \
                 selectFullC(partRG.faces, [], [-(bG - bF) / 2 / rRad - TOL / rRad, -(bG - bF) / 2 / rRad + TOL / rRad], [],
                             axis) + \
                 selectFullC(partRG.faces, [], [(bG + bF) / 2 / rRad - TOL / rRad, (bG + bF) / 2 / rRad + TOL / rRad], [],
                             axis)
        partRG.Set(name='rigid', faces=rigidG)
        partRG.Set(name='RP-Rad', referencePoints=(partRG.referencePoints[rpRG.id],))
        partRG.Set(faces=partRG.faces.getByBoundingBox(zMin=-TOL, zMax=+TOL), name='zSym')
        partRF.Set(faces=partRF.faces.getByBoundingBox(zMin=-TOL, zMax=+TOL), name='zSym')
        # Vernetzen der Radparts
        axis = [[0, rRad, 0], [0, -1, 0]]
        partRF.seedPart(size=elFF)
        partRG.seedPart(size=elF)
        seedBF0 = selectFull(partRF.edges, [], [], [tFF + TOL, tF - TOL])
        seedBF1 = selectFullC(partRF.edges, [(rRad - hF) + TOL, (rRad - hFF) - TOL], [], [], axis)
        seedBF2a = selectFullC(partRF.edges, [], [TOL / rRad, (bF - bFF) / 2 / rRad - TOL / rRad], [], axis)
        seedBF2b = selectFullC(partRF.edges, [], [(bFF + bF) / rRad / 2 + TOL / rRad, bF / rRad - TOL / rRad], [], axis)
        edgeBiasedList(partRF, seedBF1, 1, 1, axis, elF, elFF)
        edgeBiasedList(partRF, seedBF2b, 2, -1, axis, elF, elFF)
        edgeBiasedList(partRF, seedBF2a, 2, 1, axis, elF, elFF)
        edgeBiasedList(partRF, seedBF0, 3, -1, [], elF, elFF)
        partRF.generateMesh()
        seedBF0 = selectFull(partRG.edges, [], [], [tF + TOL, tG - TOL])
        seedBF1 = selectFullC(partRG.edges, [(rRad - hG) + TOL, (rRad - hF) - TOL], [], [], axis)
        seedBF2a = selectFullC(partRG.edges, [], [-(bG - bF) / rRad / 2 + TOL / rRad, -TOL / rRad], [], axis)
        seedBF2b = selectFullC(partRG.edges, [], [bF / rRad + TOL / rRad, (bG + bF) / rRad / 2 - TOL / rRad], [], axis)
        edgeBiasedList(partRG, seedBF1, 1, 1, axis, elG, elF)
        edgeBiasedList(partRG, seedBF2b, 2, -1, axis, elG, elF)
        edgeBiasedList(partRG, seedBF2a, 2, 1, axis, elG, elF)
        edgeBiasedList(partRG, seedBF0, 3, -1, [], elG, elF)
        partRG.generateMesh()
        return [partRF, partRG]

# one function for creating rolling model ----------------------------------
def make_rolling_model(calc_dir, model_name='roll-test', uy00=0.05):
    #
    dir0 = make_dir(calc_dir, if_change=1)
    Mdb()
    #
    input_d = Pickler.load('input_model.dat')
    # Modell erstellen
    # x0 in Geometrie hinein!!!
    #x0 = (b[0] - load[0])/2.
    model = reset_model(model_name)
    if '2D' in input_d['Geometrievariante'][0]:
        # lCont: Laenge der Flaeche der Knoten
        if input_d['Geometrievariante'][0] == '2D':
            [schieneF, schieneG, lCont] = make_rail_2d(model, input_d)
            mdb.saveAs(pathName=model_name + '.cae')
            [radF, radG, angFein, angGrob] = make_wheel_2d(model, input_d)
            mdb.saveAs(pathName=model_name + '.cae')
        else:
            [schieneF, lCont] = make_rail_map_2d(model, input_d)
            mdb.saveAs(pathName=model_name + '.cae')
            [radF, angFein] = make_wheel_map_2d(model, input_d)
            mdb.saveAs(pathName=model_name + '.cae')
            schieneG, radG = None,None
    else:
        [schieneF, schieneG] = make_rail_3d(model,input_d)
        mdb.saveAs(pathName=model_name + '.cae')
        [radF, radG] = make_wheel_3d(model, input_d)
        mdb.saveAs(pathName=model_name + '.cae')
    # for fast model: load and evaluate function separate!
    make_mat_sec(model, input_d)
    mdb.saveAs(pathName=model_name + '.cae')
    raise ValueError('soweit gut?')
    (instSG, instSF, instRG) = make_assembly(model, [schieneF, schieneG, radF, radG], input_d)
    #
    make_load(model, instSG, instRG, input_d, uy00=uy00)
    run_model(model, model_name, int(input_d['Anzahl Prozessoren']), 1)
    #
    del_h = evaluate_odb(model_name,ob_rad_starr=input_d['ob Rad starr'])
    os.chdir(DIR0)
    remove_files(DIR0)
    return

calc_dir = str(sys.argv[-1])
# run in directory calc_dir
make_rolling_model(calc_dir)
#
