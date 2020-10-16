"""Sketch from an input geometry file

.. codeauthor:: Knut Andreas Meyer
"""
import numpy as np

from abaqusConstants import *
import sketch



def get_circle_center_from_3_points(p1, p2, p3):
    """Get the center point a circle described by three points. Solution based on Keith Randall
    (https://codegolf.stackexchange.com/a/2396)
    
    :param iterable p1: An iterable of 2 floats the first point
    :param iterable p2: An iterable of 2 floats the second point
    :param iterable p3: An iterable of 2 floats the third point
    
    :returns: The 2d coordinates of the circle center.
    :rtype: np.array

    """
    x,y,z = [complex(p[0], p[1]) for p in [p1,p2,p3]]
    w = z - x
    w /= y - x
    c = (x-y)*(w-abs(w)**2)/2j/w.imag-x
    
    return np.array([c.real, c.imag])
    


def get_arc_center(end_point, arc_curve):
    """Get the center point of the arc described by the ConstrainedSketchGeometry object arc_curve
    
    Find two more points on the curve, located 1/3 and 2/3 from end_point along the arc. Calculate 
    the center based on these points. The reason for not using end points is to avoid numerical 
    issues in case the arc is (almost) closed. 

    :param iterable end_point: An iterable of 2 floats giving an end point of the curve.
    :param ConstrainedSketchGeometry arc_curve: ConstrainedSketchGeometry of curveType=ARC.
    
    :returns: The 2d coordinates of the arc center.
    :rtype: np.array

    """
    if arc_curve.curveType is not ARC:
        raise ValueError('The arc_curve input must be a ConstrainedSketchGeometry of curveType=ARC')
        
    p1 = np.array(end_point)
    try:
        # Get the point p2, 1/3 into the arc
        p2 = arc_curve.getPointAtDistance(point=p1, distance=0.33, percentage=True)
    except AbaqusException as e:
        print('Probably the end_point is not at the start or end of the arc_curve. ' + 
              'Abaqus returns an error:')
        print(str(e))
        raise ValueError('Check end_point input')
    
    # Get another point, p3, 2/3 into the arc. 
    p3 = np.array(arc_curve.getPointAtDistance(point=p1, distance=0.67, percentage=True))
    
    # Return center point
    return get_circle_center_from_3_points(p1, p2, p3)


def get_tangent(end_point, sketch_geometry):
    """Get the tangent direction exiting sketch_geometry at end_point.

    :param iterable end_point: An iterable of 2 floats giving an end point of the geometry_object.
    :param ConstrainedSketchGeometry sketch_geometry: The sketch geometry object for which the tangent should be obtained for.
    
    :returns: The 2d tangent vector exiting the sketch_geometry object at end_point.
    :rtype: np.array

    """
    
    # Check which curve type sketch_geometry is, possible values are ARC, CIRCLE, ELLIPSE, LINE, and 
    # SPLINE. CIRCLE and ELLIPSE are closed curves and not supported
    if sketch_geometry.curveType == LINE:
        p0 = np.array(sketch_geometry.getPointAtDistance(point=end_point, distance=1.0, 
                                                         percentage=True))
        tangent = np.array(end_point) - p0
    elif sketch_geometry.curveType == ARC:
        center_point = get_arc_center(end_point, sketch_geometry)
        radius_vector = np.array(end_point) - center_point
        tangent_vector = np.array([radius_vector[1], -radius_vector[0]])
        # Create a test point close to the end point on the arc
        test_point = np.array(sketch_geometry.getPointAtDistance(point=end_point, distance=0.1, 
                                                                 percentage=True))
        # Ensure correct direction of tangent
        if np.dot(tangent_vector, np.array(end_point) - test_point) < 0:
            tangent_vector = -tangent_vector
    elif sketch_geometry.curveType == SPLINE:
        # For this case the tangent is numerically approximated. 
        # Potential improvement: Use get_circle_center_from_3_points to evaluate the curvature to
        # such that an pertubation size can be optimized. 
        
        # Not sure what precision is used internally for splines, so assume single precision.
        pertubation = np.linalg.norm(end_point)*1.e-4
        p0 = np.array(sketch_geometry.getPointAtDistance(point=end_point, distance=pertubation, 
                                                         percentage=False))
        tangent = np.array(end_point) - p0
    else:
        raise ValueError('sketch_geometry.curveType must be LINE, ARC or SPLINE')
        
    return tangent/np.linalg.norm(tangent)  # Return normalized tangent
    