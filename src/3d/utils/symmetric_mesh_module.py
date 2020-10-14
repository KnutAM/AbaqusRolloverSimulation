from __future__ import print_function
import numpy as np
import sys

from abaqus import *
from abaqusConstants import *
import regionToolset, mesh, part
import textRepr


def make_periodic_meshes(the_part, source_sets, target_sets):
    # Given an already meshed part, the_part: For each set source_set and target_set in source_sets and 
    # target_sets, apply the mesh on the faces described by source_set to the faces described by 
    # target_set. The mesh on the remaining of the part is removed and only the faces described by 
    # the sets in source_sets and target_sets will have meshes. 
    # Input
    # the_part          Abaqus part object
    # source_sets       List of geometric sets, each containing the faces with mesh to be copied
    # source_sets       List of geometric sets, each containing the faces with mesh to be pasted
    #
    # Output
    # None
    # 
    shadow_regions_s = []
    ref_points_ss = []
    for source_set in source_sets:
        shadow_regions, ref_points_s = create_shadow_mesh(the_part, source_set)
        shadow_regions_s.append(shadow_regions)
        ref_points_ss.append(ref_points_s)
    
    target_face_orders_s = order_target_sets_faces(source_sets, target_sets)
    
    the_part.deleteMesh()
    
    for s_set, t_set, tf_orders, sh_regions, ref_pts_s in zip(source_sets, target_sets, 
                                                              target_face_orders_s, 
                                                              shadow_regions_s, ref_points_ss):
        add_mesh_to_faces(the_part, s_set, sh_regions, ref_pts_s)
        add_mesh_to_faces(the_part, t_set, sh_regions, ref_pts_s, tf_orders)
        for sh_region in sh_regions:
            the_part.deleteElement(elements=sh_region.elements)
        

# Start of create_shadow_mesh related functions
def create_shadow_mesh(the_part, source_set):
    shadow_regions = []
    ref_points_s = []
    for source_face in source_set.faces:
        source_region = get_source_region(source_face)
        
        # Create an offsetted mesh
        shadow_elems, offset_vector = create_offset_mesh(the_part, source_face, source_region)
        # shadow_regions.append(regionToolset.Region(elements=shadow_elems))
        shadow_regions.append(the_part.Set(name='shFace' + str(source_face.index).zfill(3), 
                              elements=shadow_elems))
                             
        ref_points_s.append(getref_points(the_part, source_face, offset_vector))
        
    return shadow_regions, ref_points_s


def getref_points(the_part, source_face, offset_vector):
    # Given a meshed source Face, determine 3 node positions to be used for copying the mesh to face
    # later. These nodes will be located on the edges of the source_face
    
    e = the_part.edges[source_face.getEdges()[0]]
    nodes = e.getNodes()[:3]
    
    return [np.array(n.coordinates) + offset_vector for n in nodes]


def getsource_region(source_face):
    # Create a "surface-like" region, source_region, of elements on source_face
    # Input
    # source_face    Face object 
    f_elems = source_face.getElementFaces()
    elem_by_face_type = [[] for i in range(6)]
    for f_elem in f_elems:
        face_type_ind = int(str(f_elem.face)[4:]) - 1
        elem_by_face_type[face_type_ind].append(f_elem.getElements()[0])
    
    elems = {}
    for i, e in enumerate(elem_by_face_type):
        if len(e)>0:
            elems['face' + str(i+1) + 'Elements'] = mesh.MeshElementArray(elements=e)
            
    source_region = regionToolset.Region(**elems)
    
    return source_region


def create_offset_mesh(the_part, source_face, source_region, offset_distance=20.0):
    # Determine bounding box for offsetted mesh
    bounding_box = source_face.getNodes().getBoundingBox()
    offset_vector = offset_distance*np.array(source_face.getNormal())
    for key in bounding_box:
        bounding_box[key] = np.array(bounding_box[key]) + offset_vector
    
    # Convert bounding box to arguments understood by getByBoundingBox
    bb_to_get_by = convert_bounding_box(bounding_box)
    
    # Get mesh currently in that bounding box (e.g. from other faces in the set)
    old_elems = the_part.elements.getByBoundingBox(**bb_to_get_by)
    
    # Create the offsetted mesh
    the_part.generateMeshByOffset(region=source_region, initialOffset=offset_distance,
                                 meshType=SHELL, distanceBetweenLayers=0.0, numLayers=1)
    
    # Get all mesh that exist in the bounding box
    new_elems = the_part.elements.getByBoundingBox(**bb_to_get_by)
    
    # Extract only the parts of the mesh that is new with the offsetted mesh
    shadow_elems = mesh.MeshElementArray(elements=[e for e in new_elems if e not in old_elems])
    
    return shadow_elems, offset_vector

# End of create_shadow_mesh related functions        

# Start of face ordering functions
def order_target_sets_faces(source_sets, target_sets):
    face_order = []
    for src_set, tar_set in zip(source_sets, target_sets):
        face_order.append(order_target_set_faces(src_set, tar_set))
    
    return face_order
    
def order_target_set_faces(source_set, target_set):
    # Calculate offset vector from source to target faces
    normal_vector = np.array(source_set.faces[0].getNormal())
    inbetween_vector = np.array(target_set.faces[0].pointOn[0]) - np.array(source_set.faces[0].pointOn[0])
    offset_vector = normal_vector * np.dot(normal_vector, inbetween_vector)
    
    tar_face_inds = []
    for src_face in source_set.faces:
        tar_face_inds.append(find_matching_face(the_face=src_face, search_faces=target_set.faces, 
                                              offset_vector=offset_vector))
        
    return tar_face_inds
    
def find_matching_face(the_face, search_faces, offset_vector):
    GEOM_TOL = 1.e-6
    MESH_TOL = 1.e-3
    # Search for a face in search_faces that matches the size, centroid and bounding box
    the_size = the_face.getSize(printResults=False)
    the_centroid = np.array(the_face.getCentroid()) + offset_vector
    the_bounding_box = the_face.getNodes().getBoundingBox()
    the_bounding_box = {key: np.array(the_bounding_box[key]) + offset_vector for key in the_bounding_box}
    
    matching_ind = None
    num_matching = 0
    for f_ind, s_face in enumerate(search_faces):
        # Check that the following parts matches:
        # size, centroid, bounding box (coarse tolerance as it is mesh-based)
        size_check = np.abs(s_face.getSize(printResults=False) - the_size)/the_size
        centroid_check = np.linalg.norm(s_face.getCentroid() - the_centroid) / \
                        (np.sqrt(the_size) + np.linalg.norm(the_centroid))
        
        if all([check < GEOM_TOL for check in [size_check, centroid_check]]):
            s_bounding_box = s_face.getNodes().getBoundingBox()
            bb_error = 0.0
            for key in the_bounding_box:
                bb_error = bb_error + np.linalg.norm(np.array(s_bounding_box[key])-the_bounding_box[key])
            
            if (bb_error/np.linalg.norm(offset_vector)) < MESH_TOL:
                matching_ind = f_ind
                num_matching = num_matching + 1
    
    if matching_ind is None:
        raise Exception('Could not find a matching face on the other side')
    
    if num_matching > 1:
        print('Warning: Found multiple matching faces on the other side')
        
    return matching_ind

# End of face ordering functions    

# Start of add_mesh_to_faces functions
def add_mesh_to_faces(the_part, face_set, add_regions, ref_points_s, face_order=None):
    if face_order is not None:
        to_faces = [face_set.faces[i] for i in face_order]
    else:
        to_faces = face_set.faces
        
    for to_face, add_region, ref_points in zip(to_faces, add_regions, ref_points_s):
        add_mesh_to_face(the_part, to_face, add_region, ref_points)
    
    
def add_mesh_to_face(the_part, to_face, add_region, ref_points):
    add_ref_nodes, face_point_coords = get_copy_nodes_and_coord(to_face, add_region, ref_points)
        
    the_part.copyMeshPattern(elemFaces=add_region, targetFace=to_face, 
                            nodes=add_ref_nodes, coordinates=face_point_coords)
    
    
def get_copy_nodes_and_coord(to_face, add_region, ref_points):
    offset_vector = get_offset_vector(to_face, add_region)
    
    add_ref_nodes = get_ref_nodes(add_region, ref_points)
    
    # Calculate the 3 points on the receiving face corresponding to the 3 add_ref_nodes
    face_point_coords = tuple([tuple(np.array(n.coordinates) + offset_vector) for n in add_ref_nodes])
    
    return add_ref_nodes, face_point_coords
   
   
def get_offset_vector(to_face, add_region):
    normal_vector = np.array(to_face.getNormal())
    inbetween_vector = np.array(to_face.pointOn[0]) - np.array(add_region.nodes[0].coordinates)
    offset_vector = normal_vector * np.dot(normal_vector, inbetween_vector)
    return offset_vector


def get_ref_nodes(add_region, ref_points):
    nodes = []
    pos_tol = 1.e-6
    
    for ref_point in ref_points:
        for node in add_region.nodes:
            if np.linalg.norm(np.array(node.coordinates)-ref_point) < pos_tol:
                nodes.append(node)
                break
    if len(nodes) != len(ref_points):
        print('Could not find nodes corresponding to reference points')
        raise ValueError
        
    return nodes
    
# End of add_mesh_to_faces functions
    
# Utility functions
def convert_bounding_box(bb_from_get):
    # The method getBoundingBox returns dictionary with items 'low' and 'high'
    # The method getByBoundingBox require input xMin, xMax, yMin, ..., zMax
    # The present function returns a dictionary, bb_to_get_by, that can be used as input as 
    # getByBoundingBox(**bb_to_get_by), i.e. using kwargs
    bb_to_get_by = {x + side: bb_from_get[lh][i] for i, x in enumerate(['x', 'y', 'z']) 
                 for side, lh in zip(['Min', 'Max'], ['low', 'high'])}
    return bb_to_get_by


if __name__ == '__main__':
    print('STARTING SYMMETRIC MESH GENERATION')
    m = mdb.models[mdb.models.keys()[0]]
    the_part = m.parts[m.parts.keys()[0]]
    the_part.deleteMesh()
    the_part.deleteNode(nodes=the_part.nodes)
    the_part.generateMesh()
    source_face_set = the_part.sets['source_set']
    target_face_set = the_part.sets['target_set']
    make_periodic_meshes(the_part, [source_face_set], [target_face_set])
    the_part.generateMesh()
