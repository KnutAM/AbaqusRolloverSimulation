from __future__ import print_function
import numpy as np
import sys

from abaqus import *
from abaqusConstants import *
import regionToolset, mesh, part

import mesh_tools as mt


def make_periodic_meshes(the_part, source_sets, target_sets):
    """Ensure that meshes are the same on the paired face sets on the_part. 
    Given an already meshed part, the_part: For each set source_set and target_set in source_sets and 
    target_sets, apply the mesh on the faces described by source_set to the faces described by 
    target_set. The mesh on the remaining of the part is removed and only the faces described by 
    the sets in source_sets and target_sets will have meshes. 
    
    :param the_part: The part to be meshed
    :type the_part: Part (Abaqus object)
    
    :param source_sets: Sets containing faces from which meshes will be copied to target_sets
    :type source_sets: list(Set (Abaqus object))
    
    :param target_sets: Sets containing faces to which meshes from source_sets will be copied
    :type target_sets: list(Set (Abaqus object))
        
    :returns: None
    :rtype: None

    """
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
            delete_set_keys = []
            the_part.deleteNode(nodes=sh_region.nodes)
            
            for set_key in the_part.sets.keys():
                if sh_region == the_part.sets[set_key]:
                    delete_set_keys.append(set_key)
            for delete_set_key in delete_set_keys:
                del the_part.sets[delete_set_key]
        

# Start of create_shadow_mesh related functions
def create_shadow_mesh(the_part, source_set):
    """Create an offsetted 2d-planar mesh for each face in source_set
    
    :param the_part: The part to be meshed
    :type the_part: Part (Abaqus object)
    
    :param source_set: Set containing faces from which a copy of the meshes will be offsetted
    :type source_sets: Set (Abaqus object)
    
    :returns: (shadow_regions, ref_points_s)
    
        - shadow_regions: List of sets containing the offsetted mesh corresponding to each face in 
          source_set.faces
        - ref_points_s: List of lists containing 3 points on edges of the offsetted face. The 
          coordinates are described by numpy arrays with x, y, z coordinates. 
    :rtype: tuple(list(Set (Abaqus object)), list(list(np.array)))

    """
    shadow_regions = []
    ref_points_s = []
    for source_face in source_set.faces:
        source_region = mt.get_source_region(source_face)
        
        # Create an offsetted mesh
        shadow_elems, offset_vector = mt.create_offset_mesh(the_part, source_face, source_region)
        # shadow_regions.append(regionToolset.Region(elements=shadow_elems))
        shadow_regions.append(the_part.Set(name='shFace' + str(source_face.index).zfill(3), 
                              elements=shadow_elems))
                             
        ref_points_s.append(getref_points(the_part, source_face, offset_vector))
        
    return shadow_regions, ref_points_s


def getref_points(the_part, source_face, offset_vector):
    """Get reference points on the mesh on source_face offsetted by offset_vector
    
    The points are located on the edges of source_face.
    
    :param the_part: The part to be meshed
    :type the_part: Part (Abaqus object)
    
    :param source_face: A meshed face
    :type source_face: Face (Abaqus object)
    
    :returns: List of three reference points described by numpy arrays with x, y, z coordinates
        
    :rtype: list(np.array)

    """
    # Given a meshed source Face, determine 3 node positions to be used for copying the mesh to face
    # later. These nodes will be located on the edges of the source_face
    
    e = the_part.edges[source_face.getEdges()[0]]
    nodes = e.getNodes()[:3]
    
    return [np.array(n.coordinates) + offset_vector for n in nodes]

# End of create_shadow_mesh related functions        

# Start of face ordering functions
def order_target_sets_faces(source_sets, target_sets):
    """Determine the order of faces in each set in target_sets corresponding 
    to the face order in each set in the corresponding set in source_sets. See also 
    order_target_set_faces for description of how each set is handled. 
    
    :param source_sets: A list of sets that contain faces
    :type source_sets: list(Set (Abaqus object))
    
    :param target_sets: A list of sets (containing faces) that corresponds to the sets in 
                        source_sets. The faces must have equal geometry as those in the sets in 
                        source_sets and be translated only in the face's normal directions. 
    :type target_sets: list(Set (Abaqus object))
    
    :returns: A list of lists containing the order of faces in target_sets corresponding to 
              source_sets. 
    :rtype: list(list(int))

    """
    face_order = []
    for src_set, tar_set in zip(source_sets, target_sets):
        face_order.append(order_target_set_faces(src_set, tar_set))
    
    return face_order
    
def order_target_set_faces(source_set, target_set):
    """Determine the order of faces in target_set corresponding to the face order source_set. See 
    find_matching_face for how a matching face is determined. 
    
    :param source_set: A set containing faces
    :type source_sets: Set (Abaqus object)
    
    :param target_set: A set containing faces that corresponds to the faces in source_set. The faces 
                       must have equal geometry to the faces in source_set and be translated only in 
                       the face's normal directions. See find_matching_face for details on how a 
                       corresponding face is determined. 
    :type target_sets: list(Set (Abaqus object))
    
    :returns: A list containing the order of faces in target_set corresponding to source_set.
    :rtype: list(list(int))

    """
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
    """Determine the face in search_faces that is equal to the_face but offset by offset_vector. A 
    matching face is determined by having the same
    
    - Area (Relative tolerance 1e-6)
    - Centroid (norm(Error)/(sqrt(Area)+norm(centroid)) < 1e-6)
    - Bounding_box (norm(Error)/(norm(offset_vector)) < 1e-3). This is calculated from the 
      nodes, hence the larger tolerance
    
    :param the_face: The face that we want to find a match for in search_faces. The face must be 
                     meshed.
    :type the_face: Face (Abaqus object)
    
    :param search_faces: A list of faces from which we seek a match to the_face. The faces must be 
                         meshed.
    :type search_faces: list(Face (Abaqus object))
    
    :param offset_vector: The with which the search_faces are offset from the_face
    :type offset_vector: np.array 
    
    :returns: A list containing the order of faces in target_set corresponding to source_set.
    :rtype: list(list(int))

    """
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
    """Add offsetted orphan meshes specified by add_regions to the faces in face_set
    
    :param the_part: The part
    :type the_part: Part (Abaqus object)
    
    :param face_set: The set containing faces that we want to add the orphan meshes to
    :type face_set: Set (Abaqus object)
    
    :param add_regions: list of sets containing the orphan meshes to be added
    :type add_regions: list(Set (Abaqus object))
    
    :param ref_points_s: List of lists containing 3 points on edges of the faces containing the 
                         offsetted orphan mesh. The points are described by numpy arrays with x, y, 
                         and z coordinates. 
    :type ref_points_s: list(list(np.array))
    
    :param face_order: List of indices of faces in face_set such that the order corresponds to the 
                       order in add_regions. If none, the order is unaltered., defaults to None
    :type face_order: list(int)
    
    :returns: None
    :rtype: None

    """
    if face_order is not None:
        to_faces = [face_set.faces[i] for i in face_order]
    else:
        to_faces = face_set.faces
        
    for to_face, add_region, ref_points in zip(to_faces, add_regions, ref_points_s):
        add_mesh_to_face(the_part, to_face, add_region, ref_points)
    
    
def add_mesh_to_face(the_part, to_face, add_region, ref_points):
    """Add an offsetted orphan mesh specified by add_region to the face to_face in face_set
    
    :param the_part: The part
    :type the_part: Part (Abaqus object)
    
    :param to_face: The face that we want to add the orphan mesh to
    :type face_set: Face (Abaqus object)
    
    :param add_region: Set containing the orphan mesh to be added
    :type add_region: Set (Abaqus object)
    
    :param ref_points: List containing 3 points on edges of the face with the offsetted orphan mesh.
                       The points are described by numpy arrays with x, y, and z coordinates. 
    :type ref_points: list(np.array)
    
    :returns: None
    :rtype: None

    """
    # Delete all seeds on face edges
    for eind in to_face.getEdges():
        the_part.deleteSeeds(regions=part.EdgeArray(edges=[the_part.edges[eind]]))
    
    add_ref_nodes, face_point_coords = get_copy_nodes_and_coord(to_face, add_region, ref_points)
        
    the_part.copyMeshPattern(elemFaces=add_region, targetFace=to_face, 
                            nodes=add_ref_nodes, coordinates=face_point_coords)
    
    
def get_copy_nodes_and_coord(to_face, add_region, ref_points):
    """Find the nodes in the orphan mesh described by add_region corresponding to the coordinates in
    ref_points. Also return the coordinates of the corresponding points on the face to_face. 
    
    :param to_face: The face on which we want the coordinates
    :type face_set: Face (Abaqus object)
    
    :param add_region: Set containing the orphan mesh whose node corresponding to ref_points should
                       be found.
    :type add_region: Set (Abaqus object)
    
    :param ref_points: List containing 3 points on edges of the face with the offsetted orphan mesh.
                       The points are described by numpy arrays with x, y, and z coordinates. 
    :type ref_points: list(np.array)
    
    :returns: (add_ref_nodes, face_point_coords)
        
        - add_ref_nodes: list of nodes at the coordinates specified by ref_points
        - face_point_coords: list of points on to_face corresponding to the nodes in 
          add_ref_nodes
    :rtype: tuple(list(Node (Abaqus object)), list(np.array))

    """
    offset_vector = get_offset_vector(to_face, add_region)
    
    add_ref_nodes = get_ref_nodes(add_region, ref_points)
    
    # Calculate the 3 points on the receiving face corresponding to the 3 add_ref_nodes
    face_point_coords = tuple([tuple(np.array(n.coordinates) + offset_vector) for n in add_ref_nodes])
    
    return add_ref_nodes, face_point_coords
   
   
def get_offset_vector(to_face, add_region):
    """Find the vector from add_region to to_face which is normal to to_face
    
    :param to_face: A face
    :type face_set: Face (Abaqus object)
    
    :param add_region: Set describing a face containing an orphan mesh
    :type add_region: Set (Abaqus object)
    
    :returns: A vector from add_region to to_face which is normal to to_face.               
    :rtype: np.array

    """
    normal_vector = np.array(to_face.getNormal())
    inbetween_vector = np.array(to_face.pointOn[0]) - np.array(add_region.nodes[0].coordinates)
    offset_vector = normal_vector * np.dot(normal_vector, inbetween_vector)
    return offset_vector


def get_ref_nodes(add_region, ref_points):
    """Find the nodes in add_region corresponding to ref_points. 
    
    :param add_region: Set describing a face containing an orphan mesh (or any other object 
                       containing list of Node (Abaqus object) accessible via add_region.nodes
    :type add_region: Set (Abaqus object)
    
    :param ref_points: List of points where we shall locate nodes.
    :type ref_points: list(np.array)
    
    :returns: A list of nodes with coordinates corresponding to ref_points
    :rtype: list(Node (Abaqus object))

    """
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
