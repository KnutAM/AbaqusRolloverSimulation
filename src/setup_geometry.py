# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import step
import interaction
import load
import mesh
import optimization
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior
import __main__

import numpy as np

def RolloverSetup():
    rollover_model = mdb.models.values()[0]
    
    rail_geometry = {'length': 100.0, 'height': 30.0}
    rail_mesh = {'fine': 1.0, 'coarse': 5.0}
    
    wheel_geometry = {'diameter': 400.0, 'rolling_angle': 1.5*100.0/(400.0/2.0), 'id': 50.0}
    wheel_mesh = {'fine': 1.0, 'coarse': 100.0, 'refine_thickness': 1.0}
    
    
    # Material and sections
    rollover_model.Material(name='ElasticSteel')
    rollover_model.materials['ElasticSteel'].Elastic(table=((210000.0, 0.3), ))
    rollover_model.HomogeneousSolidSection(name='WheelSection', material='ElasticSteel', thickness=None)
    rollover_model.HomogeneousSolidSection(name='RailSection', material='ElasticSteel', thickness=None)
    
    rollover_model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    
    rail = setup_rail(rollover_model, rail_geometry, rail_mesh, 'RailSection')
    wheel = setup_wheel(rollover_model, wheel_geometry, wheel_mesh, 'WheelSection')
    assy = assemble(rollover_model, rail, wheel)
    
    setup_contact(rollover_model, assy, 'Step-1')
    
    
def setup_rail(model, geometry, mesh, section_name):
    # Rail
    name = 'RAIL'
    length = geometry['length']
    height = geometry['height']
    sketch = model.ConstrainedSketch(name='__rail_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    sketch.rectangle(point1=(-length/2.0, -height), point2=(length/2.0, 0.0))
    part = model.Part(name=name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    part.BaseShell(sketch=sketch)
    sketch.unsetPrimaryObject()
    
    # Rail mesh
    part.seedEdgeByBias(biasMethod=SINGLE, 
                     end2Edges=part.edges.findAt(((-length/2.0, -height/2.0, 0.0),)),
                     end1Edges=part.edges.findAt(((+length/2.0, -height/2.0, 0.0),)), 
                     minSize=mesh['fine'], maxSize=mesh['coarse'], constraint=FINER)
    part.generateMesh()
    
    # Assign section
    f = part.faces
    faces = f.getSequenceFromMask(mask=('[#1 ]', ), )
    region = part.Set(faces=f, name='rail')
    part.SectionAssignment(region=region, sectionName=section_name, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    return part
    
def setup_wheel(model, geometry, mesh, section_name):
    # Geometry
    diameter = geometry['diameter']
    inner_diameter = geometry['id']
    refine_thickness = mesh['refine_thickness']
    rolling_angle = geometry['rolling_angle']/2.0
    
    part = model.Part(name='Wheel', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    sketch = model.ConstrainedSketch(name='__wheel_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    sketch.CircleByCenterPerimeter(center=(0.0, diameter/2.0), point1=(0.0, 0.0))
    sketch.CircleByCenterPerimeter(center=(0.0, diameter/2.0), point1=(0.0, diameter/2.0 - inner_diameter/2.0))
    part.BaseShell(sketch=sketch)
    
    # Partitioning
    partition_sketch = model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    dias = np.array([diameter, diameter - 2*refine_thickness])
    dx = dias*np.sin(rolling_angle)/2.0
    dy = dias*(1.0 - np.cos(rolling_angle))/2.0
    dy[1] = dy[1] + refine_thickness
    partition_sketch.ArcByCenterEnds(center=(0.0, diameter/2.0), point1=(dx[1], dy[1]), point2=(-dx[1], dy[1]), direction=CLOCKWISE)
    partition_sketch.Line(point1=(-dx[0], dy[0]), point2=(-dx[1], dy[1]))
    partition_sketch.Line(point1=(dx[0], dy[0]), point2=(dx[1], dy[1]))
    part.PartitionFaceBySketch(faces=part.faces.findAt(((0.0, 1.0, 0.0),)), sketch=partition_sketch)
    
    
    # Mesh wheel
    part.seedEdgeBySize(edges=part.edges.findAt(((0.0, 0.0, 0.0),)), size=mesh['fine'], deviationFactor=0.1, constraint=FINER)
    part.seedEdgeByBias(biasMethod=DOUBLE, endEdges=part.edges.findAt(((0.0, diameter, 0.0),)), minSize=mesh['fine'], maxSize=mesh['coarse'], constraint=FINER)
    part.generateMesh()
    
    # Section assignment
    f = part.faces
    faces = f.getSequenceFromMask(mask=('[#3 ]', ), )
    region = part.Set(faces=faces, name='wheel')
    part.SectionAssignment(region=region, sectionName=section_name, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', 
        thicknessAssignment=FROM_SECTION)
    
    return part
    
    
def assemble(model, rail, wheel):
    assy = model.rootAssembly
    assy.DatumCsysByDefault(CARTESIAN)
    assy.Instance(name='RAIL', part=rail, dependent=ON)
    assy.Instance(name='WHEEL', part=wheel, dependent=ON)
    
    return assy
    
    
def setup_contact(model, assy, create_step_name):
    model.ContactProperty('Contact')
    model.interactionProperties['Contact'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=ON, constraintEnforcementMethod=DEFAULT)
    model.interactionProperties['Contact'].TangentialBehavior(formulation=FRICTIONLESS)
    
    rail_inst = assy.instances['RAIL']
    wheel_inst = assy.instances['WHEEL']

    rail_contact_surface = assy.Surface(side1Edges=rail_inst.edges.findAt(((0.,0.,0.),)), name='railhead')
    wheel_contact_surface = assy.Surface(side1Edges=wheel_inst.edges.findAt(((-1.0e-3, 0., 0.),),((1.0e-3, 0., 0.),)), name='wheel_contact')

    model.SurfaceToSurfaceContactStd(name='Contact', 
        createStepName=create_step_name, master=rail_contact_surface, slave=wheel_contact_surface, sliding=FINITE, 
        thickness=ON, interactionProperty='Contact', adjustMethod=NONE, 
        initialClearance=OMIT, datumAxis=None, clearanceRegion=None)