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
    
    # Rail
    rail_name = 'RAIL'
    rail_length = 100.0
    rail_height = 30.0
    rail_sketch = rollover_model.ConstrainedSketch(name='__rail_profile__', sheetSize=200.0)
    rail_sketch.setPrimaryObject(option=STANDALONE)
    rail_sketch.rectangle(point1=(-rail_length/2.0, -rail_height), point2=(rail_length/2.0, 0.0))
    rail_part = rollover_model.Part(name=rail_name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    rail_part.BaseShell(sketch=rail_sketch)
    rail_sketch.unsetPrimaryObject()
    
    # Wheel
    wheel_diameter = 400.0
    wheel_refine_thickness = 2.0
    wheel_sketch = rollover_model.ConstrainedSketch(name='__wheel_profile__', sheetSize=200.0)
    wheel_sketch.setPrimaryObject(option=STANDALONE)
    wheel_sketch.CircleByCenterPerimeter(center=(0.0, wheel_diameter/2.0), point1=(0.0, 0.0))
    wheel_part = rollover_model.Part(name='Wheel', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    wheel_part.BaseShell(sketch=wheel_sketch)
    
    wheel_partition_sketch = rollover_model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    wheel_partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    rotation_angle = 1.5*rail_length/wheel_diameter
    dx = np.array([wheel_diameter, wheel_diameter - 2*wheel_refine_thickness])*np.sin(rotation_angle)/2.0
    dy = np.array([wheel_diameter, wheel_diameter - 2*wheel_refine_thickness])*(1.0 - np.cos(rotation_angle))/2.0
    wheel_partition_sketch.ArcByCenterEnds(center=(0.0, wheel_diameter/2.0), point1=(dx[1], dy[1]), point2=(-dx[1], dy[1]), direction=CLOCKWISE)
    wheel_partition_sketch.Line(point1=(-dx[0], dy[0]), point2=(-dx[1], dy[1]))
    wheel_partition_sketch.Line(point1=(dx[0], dy[0]), point2=(dx[1], dy[1]))
    wheel_part.PartitionFaceBySketch(faces=wheel_part.faces.findAt(((0.0, wheel_diameter/2.0, 0.0),)), sketch=wheel_partition_sketch)
    
    
    # Mesh wheel
    wheel_part.seedEdgeBySize(edges=wheel_part.edges.findAt(((0.0, 0.0, 0.0),)), size=1.0, deviationFactor=0.1, constraint=FINER)
    wheel_part.seedEdgeByBias(biasMethod=DOUBLE, endEdges=wheel_part.edges.findAt(((0.0, wheel_diameter, 0.0),)), minSize=1.0, maxSize=100.0, constraint=FINER)
    wheel_part.generateMesh()
    
    
    # Rail mesh
    rail_part.seedEdgeByBias(biasMethod=SINGLE, 
                     end2Edges=rail_part.edges.findAt(((-rail_length/2.0, -rail_height/2.0, 0.0),)),
                     end1Edges=rail_part.edges.findAt(((+rail_length/2.0, -rail_height/2.0, 0.0),)), 
                     minSize=1.0, maxSize=5.0, constraint=FINER)
    rail_part.generateMesh()
    
    # Material
    rollover_model.Material(name='ElasticSteel')
    rollover_model.materials['ElasticSteel'].Elastic(table=((210000.0, 0.3), 
        ))


RolloverSetup()