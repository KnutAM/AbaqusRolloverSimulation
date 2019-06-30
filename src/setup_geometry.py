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
    
    rail_geometry = {'length': 100.0, 'height': 30.0, 'max_contact_zone': 25.}
    rail_mesh = {'fine': 1.0, 'coarse': 5.0}
    
    wheel_geometry = {'diameter': 400.0, 'id': 50.0}
    wheel_mesh = {'fine': 1.0, 'coarse': 100.0, 'refine_thickness': 1.0}
    process_geometry_and_mesh(rail_geometry, rail_mesh, wheel_geometry, wheel_mesh)
    
    # Material and sections
    rollover_model.Material(name='ElasticSteel')
    rollover_model.materials['ElasticSteel'].Elastic(table=((210000.0, 0.3), ))
    rollover_model.Material(name='ShadowMaterial')
    rollover_model.materials['ShadowMaterial'].Elastic(table=((1.e-6, 0.3), ))
    rollover_model.HomogeneousSolidSection(name='WheelSection', material='ElasticSteel', thickness=None)
    rollover_model.HomogeneousSolidSection(name='RailSection', material='ElasticSteel', thickness=None)
    rollover_model.HomogeneousSolidSection(name='ShadowSection', material='ShadowMaterial', thickness=None)
    
    rollover_model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    
    rail = setup_rail(rollover_model, rail_geometry, rail_mesh, 'RailSection', 'ShadowSection')
    wheel = setup_wheel(rollover_model, wheel_geometry, wheel_mesh, 'WheelSection')
    assy = assemble(rollover_model, rail, wheel)
    
    setup_contact(rollover_model, assy, 'Step-1', rail_geometry)
    
    connect_nodes(rollover_model, assy, rail, rail_geometry, rail_mesh)
    
    bc = loading(rollover_model, assy, rail_geometry, wheel_geometry, 'Step-1')
    
    # assy.translate(instanceList=('WHEEL', ), vector=(-60.0, 0.0, 0.0))
    
def process_geometry_and_mesh(rail_geometry, rail_mesh, wheel_geometry, wheel_mesh):
    # Determine length of shadow mesh line
    number_of_top_elements = int(rail_geometry['length']/rail_mesh['fine'])
    true_fine_element_length = rail_geometry['length']/number_of_top_elements
    number_of_shadow_elements = int(rail_geometry['max_contact_zone']/rail_mesh['fine'])
    rail_geometry['number_of_top_elements'] = number_of_top_elements
    rail_geometry['shadow_line_length'] = true_fine_element_length*number_of_shadow_elements
    rail_geometry['number_of_shadow_elements'] = number_of_shadow_elements
    
    # Determine mesh refinement angle for wheel
    wheel_geometry['rolling_angle'] = 1.5*rail_geometry['length']/(wheel_geometry['diameter']/2.0)
    
    
def setup_rail(model, geometry, mesh, section_name, shadow_section):
    # Rail
    name = 'RAIL'
    length = geometry['length']
    height = geometry['height']
    shadow_line_length = geometry['shadow_line_length']
    number_of_shadow_elements = geometry['number_of_shadow_elements']
    number_of_top_elements = geometry['number_of_top_elements']
    
    sketch = model.ConstrainedSketch(name='__rail_profile__', sheetSize=200.0)
    sketch.setPrimaryObject(option=STANDALONE)
    
    dx = length/2.0
    dy = height
    dxs = -(dx + shadow_line_length)
    dys = -mesh['fine']
    sketch.Line(point1=( dx,  0.), point2=( dx, -dy))
    sketch.Line(point1=( dx, -dy), point2=(-dx, -dy))
    sketch.Line(point1=(-dx, -dy), point2=(-dx, dys))
    sketch.Line(point1=(-dx, dys), point2=(dxs, dys))
    sketch.Line(point1=(dxs, dys), point2=(dxs,  0.))
    sketch.Line(point1=(dxs,  0.), point2=( dx, 0.))
    
    part = model.Part(name=name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    part.BaseShell(sketch=sketch)
    sketch.unsetPrimaryObject()
    
    # Partitioning
    partition_sketch = model.ConstrainedSketch(name='__wheel_partition__', sheetSize=200.0)
    partition_sketch.setPrimaryObject(option=SUPERIMPOSE)
    partition_sketch.Line(point1=(-length/2.0-shadow_line_length-1., -mesh['fine']), point2=(length/2.0+1., -mesh['fine']))
    partition_sketch.Line(point1=(-length/2.0, 0.), point2=(-length/2.0, -mesh['fine']))
    part.PartitionFaceBySketch(faces=part.faces.findAt(((0.0, -1.0, 0.0),)), sketch=partition_sketch)
    
    # Rail mesh
    part.seedEdgeByNumber(edges=part.edges.findAt(((0.0, 0.0, 0.0),)), 
                          number=number_of_top_elements, constraint=FIXED)
    part.seedEdgeByNumber(edges=part.edges.findAt(((-length/2.0-shadow_line_length/2.0, 0.0, 0.0),)), 
                          number=number_of_shadow_elements, constraint=FIXED)
    part.seedEdgeByBias(biasMethod=SINGLE, 
                     end2Edges=part.edges.findAt(((-length/2.0, -height/2.0, 0.0),)),
                     end1Edges=part.edges.findAt(((+length/2.0, -height/2.0, 0.0),)), 
                     minSize=mesh['fine'], maxSize=mesh['coarse'], constraint=FIXED) # Need FIXED to ensure compatible meshes
    part.generateMesh()
    
    # Assign sections
    faces = part.faces.findAt(((0., -mesh['fine']/2.0, 0.),),((0., -1.5*mesh['fine'], 0.),))
    region = part.Set(faces=faces, name='rail')
    part.SectionAssignment(region=region, sectionName=section_name, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
        
    shadow_face = part.faces.findAt(((-length/2.0-shadow_line_length/2.0, -mesh['fine']/2.0, 0.),))
    shadow_region = part.Set(faces=shadow_face, name='shadow_rail')
    part.SectionAssignment(region=shadow_region, sectionName=shadow_section, offset=0.0, 
        offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
    
    
    return part
    
def setup_wheel(model, geometry, mesh, section_name):
    name='WHEEL'
    # Geometry
    diameter = geometry['diameter']
    inner_diameter = geometry['id']
    refine_thickness = mesh['refine_thickness']
    rolling_angle = geometry['rolling_angle']/2.0
    
    part = model.Part(name=name, dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
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
    
    
def setup_contact(model, assy, create_step_name, rail_geometry):
    model.ContactProperty('Contact')
    model.interactionProperties['Contact'].NormalBehavior(pressureOverclosure=LINEAR, contactStiffness=1.e6)
    model.interactionProperties['Contact'].TangentialBehavior(formulation=FRICTIONLESS)
    
    rail_inst = assy.instances['RAIL']
    wheel_inst = assy.instances['WHEEL']

    rail_contact_surface = assy.Surface(side1Edges=rail_inst.edges.findAt(((0.,0.,0.),), 
        (((-rail_geometry['length']-rail_geometry['shadow_line_length'])/2.0, 0.0, 0.0),)), 
        name='railhead')
    wheel_contact_surface = assy.Surface(side1Edges=wheel_inst.edges.findAt(((-1.0e-3, 0., 0.),),((1.0e-3, 0., 0.),)), name='wheel_contact')

    model.SurfaceToSurfaceContactStd(name='Contact', 
        createStepName=create_step_name, master=rail_contact_surface, slave=wheel_contact_surface, sliding=FINITE, 
        thickness=ON, interactionProperty='Contact', adjustMethod=NONE, 
        initialClearance=OMIT, datumAxis=None, clearanceRegion=None)
        
def find_rail_node_pairs_left_right(rail, geometry, mesh):
    edges = rail.edges.findAt(((-geometry['length']/2.0, -(geometry['height']-mesh['fine'])/2.0, 0.0),),
                              (( geometry['length']/2.0, -(geometry['height']-mesh['fine'])/2.0, 0.0),))
    vertices = rail.vertices.findAt(((-geometry['length']/2.0, 0.0, 0.0),),
                                    (( geometry['length']/2.0, 0.0, 0.0),))
    # Find nodes that are within a tolerance from each other in y-z coordinates
    yzcoords = []
    nodes = []
    for e in edges:
        nodes.append(e.getNodes())
        coordmat = np.zeros((len(nodes[-1]), 2))
        ind = 0
        for n in nodes[-1]:
            coord = n.coordinates
            coordmat[ind, :] = np.array([coord[1], coord[2]])
            ind = ind + 1
            
        yzcoords.append(coordmat)
    
    node_pairs = [[vertices[0].getNodes()[0], vertices[1].getNodes()[0]]]
    indl = 0
    crs = yzcoords[1]
    for cl in yzcoords[0]:
        dist = (crs[:,0]-cl[0])**2 + (crs[:,1]-cl[1])**2
        indr = np.argmin(dist)
        node_pairs.append([nodes[0][indl], nodes[1][indr]])
        indl = indl + 1
    
    return node_pairs
    
def append_shadow_nodes(rail, geometry, mesh, node_pairs):
    node_connect_tolerance = 1.e-6
    length = geometry['length']
    # First identify the two nodes already linked, these should not be included
    vertices = rail.vertices.findAt(((-geometry['length']/2.0, 0.0, 0.0),),
                                    ((-geometry['length']/2.0, -mesh['fine'], 0.0),))
    # No connect nodes
    nc_nodes = [vertices[0].getNodes()[0], vertices[1].getNodes()[0]]
    
    # Find the coordinates of the nodes to connect
    shadow_x_center = -(geometry['length']+geometry['shadow_line_length'])/2.0
    shadow_edges = rail.edges.findAt(((shadow_x_center, 0.0, 0.0),),
                                     ((shadow_x_center, -mesh['fine'], 0.0),))
    true_edges = rail.edges.findAt(((0.0, 0.0, 0.0),),
                                   ((0.0, -mesh['fine'], 0.0),))
    
    yzcoords = []
    nodes = []
    for edges in [shadow_edges, true_edges]:
        tmp_coords = []
        nodes.append([])
        for e in edges:
            edge_nodes = e.getNodes()            
            for n in edge_nodes:
                nodes[-1].append(n)
                coord = n.coordinates
                tmp_coords.append(n.coordinates)
        yzcoords.append(np.array(tmp_coords))
        
    # Determine matching nodes
    for sn, sc in zip(nodes[0], yzcoords[0]):  # Shadow nodes, shadow coordinates
        if sn != nc_nodes[0] and sn != nc_nodes[1]:
            dist = (yzcoords[1][:,0]-length-sc[0])**2 + (yzcoords[1][:,1]-sc[1])**2 + (yzcoords[1][:,2]-sc[2])**2
            ind = np.argmin(dist)
            if dist[ind] < node_connect_tolerance**2:
                node_pairs.append([sn, nodes[1][ind]])
            else:
                print("WARNING: No matching nodes found, minimum distance = " + str(np.sqrt(dist[ind])))
        else:
            print('Found node that has already been used, this is expected to occur twice')
    return node_pairs
    
def connect_nodes(model, assy, rail, geometry, mesh):
    node_pairs = find_rail_node_pairs_left_right(rail, geometry, mesh)
    node_pairs = append_shadow_nodes(rail, geometry, mesh, node_pairs)
    set_nr = 1
    for np in node_pairs:
        names = ['NodeConnectSet' + side + '-' + str(set_nr) for side in ['Left', 'Right']]
        node_seq_left = rail.nodes.sequenceFromLabels((np[0].label,))
        node_seq_right = rail.nodes.sequenceFromLabels((np[1].label,))
        rail.Set(nodes=node_seq_left, name=names[0])
        rail.Set(nodes=node_seq_right, name=names[1])
        set_nr = set_nr + 1
    
    assy.regenerate()
    for set_nr in range(len(node_pairs)):
        names = ['NodeConnectSet' + side + '-' + str(set_nr+1) for side in ['Left', 'Right']]
        # Link x-degree of freedom
        model.Equation(name='NodeConnectConstraintX-'+str(set_nr), terms=((1.0, 
        'RAIL.'+names[0], 1), (-1.0, 'RAIL.'+names[1], 1)))
        # Link y-degree of freedom
        model.Equation(name='NodeConnectConstraintY-'+str(set_nr), terms=((1.0, 
        'RAIL.'+names[0], 2), (-1.0, 'RAIL.'+names[1], 2)))
        # For 3D link also z-degree of freedom (not implemented)
        
def setup_control_point_wheel(model, wheel, assy, geometry):
    wheel_inst = assy.instances['WHEEL']
    rp = wheel.ReferencePoint(
        point=wheel.InterestingPoint(edge=wheel.edges.findAt(((0.,0.,0.),))[0], rule=CENTER))
    rp_key = wheel.referencePoints.keys()[0]
    assy.regenerate()
    
    inner_circle = wheel_inst.edges.findAt(((0.0, (geometry['diameter']-geometry['id'])/2.0, 0.),))
    wheel_center=assy.Set(edges=inner_circle, name='WheelCenter')
    
    rp_region=regionToolset.Region(referencePoints=(wheel_inst.referencePoints[rp_key],))
    
    model.RigidBody(name='Center', refPointRegion=rp_region, tieRegion=wheel_center)
    
    
def loading(model, assy, rail_geom, wheel_geom, step_name):
    
    # Fix bottom of rail
    bottom_edge = assy.instances['RAIL'].edges.findAt(((0., -rail_geom['height'], 0.),))
    bottom_region = assy.Set(edges=bottom_edge, name='RailBottom')
    model.DisplacementBC(name='BC-1', createStepName='Initial', 
        region=bottom_region, u1=SET, u2=SET, ur3=UNSET, amplitude=UNSET, 
        distributionType=UNIFORM, fieldName='', localCsys=None)
    
    # BC for wheel
    ## Setup reference point in center
    id = wheel_geom['id']
    od = wheel_geom['diameter']
    
    wheel_inst = assy.instances['WHEEL']
    wheel = model.parts['WHEEL']
    rp = wheel.ReferencePoint(
        point=wheel.InterestingPoint(edge=wheel.edges.findAt(((0.,0.,0.),))[0], rule=CENTER))
    rp_key = wheel.referencePoints.keys()[0]
    assy.regenerate()
    
    ## Tie using rigid body reference point to inner diameter of wheel
    inner_circle = wheel_inst.edges.findAt(((0.0, (od-id)/2.0, 0.),))
    wheel_center=assy.Set(edges=inner_circle, name='WheelCenter')
    rp_region=regionToolset.Region(referencePoints=(wheel_inst.referencePoints[rp_key],))
    model.RigidBody(name='Center', refPointRegion=rp_region, tieRegion=wheel_center)
    
    ## Assign boundary conditions to reference point
    wheel_control = model.DisplacementBC(name='BC-2', createStepName=step_name, 
        region=rp_region, u1=0.0, u2=-1.0, ur3=0.0, amplitude=UNSET, fixed=OFF, 
        distributionType=UNIFORM, fieldName='', localCsys=None)