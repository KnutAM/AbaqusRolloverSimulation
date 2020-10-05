from __future__ import print_function
import numpy as np

from abaqus import *
from abaqusConstants import *
import regionToolset, mesh


def getFaceType(theElement, faceNodes):
    # Find which face of the element that belongs to the face. 
    # Input
    # element       The element object that should be investigated
    # faceNodes     List of nodes that belong to the face
    # 
    # Output
    # faceSide      Integer describing which elementFace that belongs to the face
    
    faceSide = None
    
    elemNodes = theElement.getNodes()
    elemFaceNodes = []
    
    for i, node in enumerate(elemNodes):
        if node in faceNodes:
            elemFaceNodes.append(i+1)
    
    def isSide(sideInds):
        return all([i in elemFaceNodes for i in sideInds])
    
    if any([code in str(theElement.type) for code in ['C3D10', 'C3D4']]):
        if isSide([1, 2, 3]):
            faceSide = 1
        elif isSide([1, 4, 2]):
            faceSide = 2
        elif isSide([2, 4, 3]):
            faceSide = 3
        elif isSide([3, 4, 1]):
            faceSide = 4
    else:
        raise NotImplementedError('Element type ' + theElement.type + ' is not supported')
            
    if not faceSide:
        raise Exception('Could not identify side for element:' + str(theElement))
    
    return faceSide
    

def getFaceTypeElements(faceElements, faceNodes, elemByFaceType = [[] for i in range(6)]):
    # Sort faceElements in bins according to which elementFace that belong to the face, described by 
    # faceNodes
    # Input:
    # faceElements      List of elements belonging to the face
    # faceNodes         List of nodes belonging to the face
    # elemByFaceType    List of 6 lists representing elementFace FACE1, FACE2, ..., FACE6. Each list 
    #                   contain elements for which the elementFace of that type is on the face. 
    #                   Having this as optional argument the function can be called for different 
    #                   parts of a face (e.g. partitions), reducing the computational time
    #
    # Output:
    # elemByFaceType    See input description
    # 
    
    for i, e in enumerate(faceElements):
        faceType = getFaceType(e, faceNodes)
        elemByFaceType[faceType-1].append(e)
    
    return elemByFaceType
    
    
def getFaceMeshRegion(faceElements, faceNodes):
    # Return a "surface-like" region (see Abaqus manual on Region command) for the mesh surface
    # containing elements faceElements and nodes faceNodes
    # Input
    # faceElements      Iterable containing elements that belong to the face
    # faceNodes         Iterable containing nodes that belong to the face
    # 
    # Output
    # region            A regionToolset region object of type "surface-like"
    #
    
    elemByFaceType = getFaceTypeElements(faceElements, faceNodes)
    elems = {}
    for i, e in enumerate(elemByFaceType):
        if len(e)>0:
            elems['face' + str(i+1) + 'Elements'] = mesh.MeshElementArray(elements=e)
        
    region = regionToolset.Region(**elems)
    
    return region


def getOffsetVector(shadowRefNodes, someCoordOnFace):
    # Given 3 nodes on the offsetted mesh and a point on the original surface, calculate the normal
    # vector with which the offsetted mesh is offset.
    # Input
    # shadowRefNodes    List of 3 nodes on the offsetted mesh
    # someCoordOnFace   Iterable containing the 3 coordinates of a point on the original surface
    
    coords = [np.array(n.coordinates) for n in shadowRefNodes]
    sVecs = [c-coords[0] for c in coords[1:]]
    nVec = np.cross(sVecs[0], sVecs[1])
    nVec = nVec/np.linalg.norm(nVec)    # Normalize
    
    dVec = coords[0] - np.array(someCoordOnFace)
    
    nVec = nVec * np.dot(nVec, dVec)
    
    return nVec
    

def getFacePointCoordinates(shadowRefNodes, someCoordOnFaces):
    facePointCoordinates = []
    for coords in someCoordOnFaces:
        offsetVector = getOffsetVector(shadowRefNodes, coords)
        facePointCoordinates.append(tuple([tuple(np.array(n.coordinates) - offsetVector) 
                                           for n in shadowRefNodes]))
    
    return facePointCoordinates
    

def generateSymmetricMesh(thePart, sourceFaceSet, targetFaceSet):
    # Given an already meshed part, apply the mesh on the face described by sourceFaceSet to the 
    # face given by targetFaceSet. Note that the mesh on the remaining part is removed. Only the 2 
    # faces will have meshes. 
    # Input
    # thePart           Abaqus part object
    # sourceFaceSet     Geometric set containing the face with the mesh to be used
    # targetFaceSet     Geometric set containing on which the source mesh should be applied
    #
    # Output
    # None
    # 
    
    shadowMeshOffset = 20.0
    someCoordOnFaces = [s.nodes[0].coordinates for s in [sourceFaceSet, targetFaceSet]]
    sourceRegion = getFaceMeshRegion(sourceFaceSet.elements, sourceFaceSet.nodes)
    thePart.generateMeshByOffset(region=sourceRegion, initialOffset=shadowMeshOffset,
                                 meshType=SHELL, distanceBetweenLayers=0.0, numLayers=1)
    
    thePart.deleteMesh()
    
    shadowNodesBoundingBox = thePart.nodes.getBoundingBox()
    bbInput = {x + side: shadowNodesBoundingBox[lh][i] for i, x in enumerate(['x', 'y', 'z']) 
               for side, lh in zip(['Min', 'Max'], ['low', 'high'])}
    shadowRefNodes = thePart.nodes[:3]
    
    
    facePointCoordinates = getFacePointCoordinates(shadowRefNodes, someCoordOnFaces)
    
    shadowRegion = regionToolset.Region(elementFaces=thePart.elements)
    thePart.copyMeshPattern(elemFaces=shadowRegion, targetFace=sourceFaceSet.faces[0],
                            nodes=shadowRefNodes,
                            coordinates=facePointCoordinates[0])
    
    thePart.copyMeshPattern(elemFaces=shadowRegion, targetFace=targetFaceSet.faces[0],
                            nodes=shadowRefNodes,
                            coordinates=facePointCoordinates[1])
    
    thePart.deleteNode(nodes=thePart.nodes.getByBoundingBox(**bbInput))
    
    
if __name__ == '__main__':
    m = mdb.models[mdb.models.keys()[0]]
    thePart = m.parts[m.parts.keys()[0]]
    sourceFaceSet = thePart.sets['sourceSet']
    targetFaceSet = thePart.sets['targetSet']
    generateSymmetricMesh(thePart, sourceFaceSet, targetFaceSet)
    thePart.generateMesh()
