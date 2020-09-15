from __future__ import print_function
import numpy as np

def get_stiffness_from_substructure_mtx_file(filename):
    with open(filename + '.mtx', 'r') as mtx:
        mtx_str = mtx.read()

    mat_str = mtx_str.split('*MATRIX,TYPE=STIFFNESS')[-1].strip(',').strip('\n')
    mat_vec = []
    for entry in mat_str.split():
        ent = entry.strip(',').strip('\n')
        try:
            mat_vec.append(float(ent))
        except ValueError:
            pass

    mat_vec = np.array(mat_vec)
    ndof = -0.5+np.sqrt(0.25+mat_vec.size*2)
    if np.abs(ndof-int(ndof)) < 1.e-10:
        ndof = int(ndof)
    else:
        print('Error reading matrix from ' + filename + '.mtx')
        return None
    
    kmat = np.zeros((ndof,ndof))
    k = 0
    for i in range(ndof):
        for j in range(i+1):
            kmat[i,j] = mat_vec[k]
            kmat[j,i] = kmat[i,j]
            k = k + 1
    
    # Reorder matrix (this is a bit risky, as we don't check with the input file)
    # A check with the input file could be made later in combination with reading the 
    # ELEMENT NODES part of the <filename>.mtx file.
    re_order = [ndof-3,ndof-2,ndof-1]
    for i in range(ndof-3):
        re_order.append(i)
    
    re_order = np.array(re_order, dtype=np.int)
    kmat = kmat[np.ix_(re_order, re_order)]
    coords = np.load('uel_coords_tmp.npy')
    
    print('Checking stiffness matrix:')
    check_stiffness_matrix(kmat, coords)
    
    return kmat, coords


def create_stiffness_matrix(outer_node_coord, outer_node_RF, rp_node_RF):
    # Create the stiffness matrix based on the reaction forces given
    # Input
    # outer_node_coord  [(x,y,z), node_nr]              Coordinates for outer nodes
    # outer_node_RF     [stpnr, (RF1, RF2), node_nr]    Reaction forces for outer nodes
    # rp_node_RF        [stpnr, (RF1, RF2, RM3)]        Reaction forces/moments for rp node
    # Note: outer_nodes should be sorted counter-clockwise starting at (x,y)=(r,0)
    # 
    # The steps should have the following loadings
    # stepnr=0  node @ (r, 0, 0) displaced 1 in x-direction
    # stepnr=1  node @ (r, 0, 0) displaced 1 in y-direction
    # stepnr=2  rp_node (0,0,0) displaced 1 in x-direction
    # stepnr=3  rp_node (0,0,0) rotated 1 around z-axis
    # 
    # The dof number is 1, 2, and 3 are x-disp, y-disp, z-rot for rp_node
    # Then every other x-disp and y-disp for outer nodes, counter-clockwise starting at (r,0,0)
    # I.e. dof=4 is x-disp at (r,0,0), dof=5 is y-disp at (r,0,0) etc. 
    # Output
    # stiffness_matrix  [ndof,ndof]
    
    num_outer_nodes = outer_node_coord.shape[1]
    ndof = 3 + 2*num_outer_nodes
    stiffness_matrix = np.zeros((ndof,ndof))
    
    # Add contributions from outer_nodes on outer_nodes
    RFx_ux = outer_node_RF[0, 0, :]
    RFx_uy = outer_node_RF[1, 0, :]
    RFy_ux = outer_node_RF[0, 1, :]
    RFy_uy = outer_node_RF[1, 1, :]
    angles = np.arctan2(outer_node_coord[1, :], outer_node_coord[0, :])
    ftmp_x = np.zeros((num_outer_nodes))
    ftmp_y = np.zeros((num_outer_nodes))
    
    for i, ang in zip(range(num_outer_nodes), angles):
        # Calculate reaction forces due to inclined unit loading
        # Contribution due x-displacements
        Fx_x = RFx_ux*np.cos(ang) - RFx_uy*np.sin(ang)
        Fy_x = RFy_ux*np.cos(ang) - RFy_uy*np.sin(ang)
        # Contribution due y-displacements
        Fx_y = RFx_uy*np.cos(ang) + RFx_ux*np.sin(ang)
        Fy_y = RFy_uy*np.cos(ang) + RFy_ux*np.sin(ang)
        
        for Fx, Fy, j in zip([Fx_x, Fx_y], [Fy_x, Fy_y], [0, 1]):            
            # Rotate reaction forces to align with the direction at the correct node
            Fxp = Fx*np.cos(ang) - Fy*np.sin(ang)
            Fyp = Fx*np.sin(ang) + Fy*np.cos(ang)
            
            # Shift the numbering to match the correct nodes
            for ftmp, Fp in zip([ftmp_x, ftmp_y], [Fxp, Fyp]):
                ftmp[i:] = Fp[0:(num_outer_nodes-i)]
                ftmp[0:i] = Fp[(num_outer_nodes-i):]
            
            # Add the forces corresponding to unit deflection in stiffness matrix
            stiffness_matrix[3::2, 3 + 2*i + j] = ftmp_x
            stiffness_matrix[4::2, 3 + 2*i + j] = ftmp_y
            
    # Add contributions from rp on outer_nodes
    # ux at rp
    RFx_ux_rp = outer_node_RF[2, 0, :]
    RFy_ux_rp = outer_node_RF[2, 1, :]
    stiffness_matrix[3::2, 0] = RFx_ux_rp  # ux on rp to x-dofs
    stiffness_matrix[4::2, 0] = RFy_ux_rp  # ux on rp to y-dofs
    # uy at rp not simulated, but due to symmetry we can calculate the correct forces
    RFx_uy_rp = np.zeros(RFx_ux_rp.shape)
    RFy_uy_rp = np.zeros(RFy_ux_rp.shape)
    n1 = int(1*num_outer_nodes/4)
    n3 = int(3*num_outer_nodes/4)
    RFy_uy_rp[n1:] = RFx_ux_rp[:n3]
    RFy_uy_rp[:n1] = RFx_ux_rp[n3:]
    RFx_uy_rp[n1:] = -RFy_ux_rp[:n3]
    RFx_uy_rp[:n1] = -RFy_ux_rp[n3:]
    stiffness_matrix[3::2, 1] = RFx_uy_rp  # ux on rp to x-dofs
    stiffness_matrix[4::2, 1] = RFy_uy_rp  # ux on rp to y-dofs
    
    # ur3 at rp
    RFx_ur3_rp = outer_node_RF[3, 0, :]
    RFy_ur3_rp = outer_node_RF[3, 1, :]
    stiffness_matrix[3::2, 2] = RFx_ur3_rp  # ur3 on rp to x-dofs
    stiffness_matrix[4::2, 2] = RFy_ur3_rp  # ur3 on rp to y-dofs
    
    # Add contributions from outer_nodes to rp
    # Utilize that stiffness_matrix is symmetric
    stiffness_matrix[0:3, 3:] = np.transpose(stiffness_matrix[3:, 0:3])
    
    # Add contributions from rp to rp
    stiffness_matrix[0,:3] = rp_node_RF[2,:]                                                #dF/dux
    stiffness_matrix[1,:3] = np.array([-rp_node_RF[2,1], rp_node_RF[2,0], rp_node_RF[2,2]]) #dF/duy
    stiffness_matrix[2,:3] = rp_node_RF[3,:]                                                #dF/dur3
    
    # print 'Checking full matrix'
    # check_stiffness_matrix(stiffness_matrix)
    
    return stiffness_matrix
    
    
def reduce_stiffness_matrix(Kfull, outer_node_coord, angle_to_keep):
    # Given the stiffness for the wheel's full circumference, use static condensation to remove 
    # unused degrees of freedom on the boundary. Return a list of nodes and the reduced stiffness 
    # matrix
    # Input
    # Kfull             [ndof, ndof]            Stiffness matrix for the full circumference
    # outer_node_coord  [(x,y,z), node_nr]      Coordinates for outer nodes
    # angle_to_keep                             How many radians to keep on the wheel.
    #                                           Will be symmetric about yz-plane (node at (0,-r))
    # Output
    # Kred              [ndof_red, ndof_red]    Reduced stiffness matrix for only rp and segment of 
    #                                           the circumference
    # coords            [(x,y,z), node_nr]      Coordinates for the kept outer nodes 
    # 
    # Note: The degrees of freedom are numbered such that the first 3 are u1, u2 and ur3 at rp.
    #       Then, the fourth is x-dof for the first entry in coords, fifth the y-dof for first entry 
    #       in coords, sixth the x-dof for the second entry in coords, and so on.
    # ----------------------------------------------------------------------------------------------
    
    # Calculate angle to the -y axis:
    angle = np.arctan2(-outer_node_coord[0,:], -outer_node_coord[1,:])
    
    keep_mask = np.abs(angle) < angle_to_keep/2.0
    remove_mask = np.invert(keep_mask)
    
    coords = outer_node_coord[:, keep_mask]
    
    # Find dofs numbers that should be kept
    ndofs = Kfull.shape[0]
    xdofs = np.arange(3,ndofs,2, dtype=np.int)
    ydofs = xdofs + 1
    kdofs = np.zeros((3+2*np.sum(keep_mask)), dtype=np.int)
    kdofs[:3] = np.array([0,1,2], dtype=np.int)
    kdofs[3::2] = xdofs[keep_mask]
    kdofs[4::2] = ydofs[keep_mask]
    
    rdofs = np.zeros((2*np.sum(remove_mask)), dtype=np.int)
    rdofs[::2] = xdofs[remove_mask]
    rdofs[1::2] = ydofs[remove_mask]
    
    # Calculate reduced stiffness matrix
    Kkk = Kfull[np.ix_(kdofs,kdofs)]
    Kkr = Kfull[np.ix_(kdofs,rdofs)]
    Krr = Kfull[np.ix_(rdofs,rdofs)]
    # Theory
    # fk = Kkk*ak + Kkr*ar
    # fr = Krk*ak + Krr*ar = 0
    # ar = -inv(Krr)*Krk*ak
    # fk = Kkk*ak - Kkr*inv(Krr)*Krk*ak
    # fk = (Kkk - Kkr*inv(Krr)*Krk)*ak = Kred*ak
    # Calculation:
    Kred = Kkk - Kkr.dot(np.linalg.inv(Krr)).dot(np.transpose(Kkr))
    
    
    # Remove rbm twice (iterative procedure), unknown how much this affects the overall stiffness?
    # But the fact that this is needed indicates that something is wrong when creating the stiffness matrix
    # Should try first to create the super element directly from Abaqus stiffness matrix, and compare
    # If the problem dissappears, then compare with my built matrices to identify potential errors
    # If the problem remains, then discuss with a senior how this can be and if the removal of rbm is reasonable?
    #Kred = remove_rbm(Kred, coords)
    #Kred = remove_rbm(Kred, coords)
    print('Checking reduced matrix')
    check_stiffness_matrix(Kred, coords)
    print('Checking reduced symmetrized matrix')
    check_stiffness_matrix(0.5*(Kred+np.transpose(Kred)), coords)
    
    return Kred, coords
    
def remove_rbm(Kred, coords):
    ndof = Kred.shape[0]
    unit_ux = np.zeros((ndof))
    unit_uy = np.zeros((ndof))
    unit_ur = np.zeros((ndof))
    unit_ux[0] = 1
    unit_ux[3::2] = 1
    unit_uy[1] = 1
    unit_uy[4::2] = 1
    unit_ur[2] = 1
    rx = coords[0, :]
    ry = coords[1, :]
    unit_ur[3::2] = -ry # x-displacement for pure (unit) rotation
    unit_ur[4::2] = rx  # y-displacement for pure (unit) rotation
    
    Kcomp = np.copy(Kred)
    # Compensate for cross effects, is symmetry maintained?
    Kcomp[0,1] = Kred[0,1] - np.dot(Kred[0,:], unit_uy)
    Kcomp[1,0] = Kred[1,0] - np.dot(Kred[1,:], unit_ux)
    # Rotation compensation
    Kcomp[2,0] = Kred[2,0] - np.dot(Kred[2,:], unit_ux)
    Kcomp[0,2] = Kred[0,2] - np.dot(Kred[0,:], unit_ur)
    Kcomp[2,1] = Kred[2,1] - np.dot(Kred[2,:], unit_uy)
    Kcomp[1,2] = Kred[1,2] - np.dot(Kred[1,:], unit_ur)
    
    for i in range((ndof-3)/2):
        ix = 3+2*i
        iy = 4+2*i
        Kcomp[ix,iy] = Kred[ix,iy] - np.dot(Kred[ix,:], unit_uy)
        Kcomp[iy,ix] = Kred[iy,ix] - np.dot(Kred[iy,:], unit_ux)
        # Will need to compensate for rotation as well!
        Kcomp[ix,2] = Kred[ix,2] - np.dot(Kred[ix, :], unit_ur)
        Kcomp[iy,2] = Kred[iy,2] - np.dot(Kred[iy, :], unit_ur)
    
    Kred = np.copy(Kcomp)
    
    Kcomp[0,0] = Kred[0,0] - np.dot(Kred[0,:], unit_ux)
    Kcomp[1,1] = Kred[1,1] - np.dot(Kred[1,:], unit_uy)
    Kcomp[2,2] = Kred[2,2] - np.dot(Kred[2,:], unit_ur)
    
    for i in range((ndof-3)/2):
        ix = 3+2*i
        iy = 4+2*i
        Kcomp[ix,ix] = Kred[ix,ix] - np.dot(Kred[ix,:], unit_ux)
        Kcomp[iy,iy] = Kred[iy,iy] - np.dot(Kred[iy,:], unit_uy)
        
    return Kcomp
    
    
def check_stiffness_matrix(kmat, coords):
    kcheck = kmat[3:,3:]
    check_rbm_x = np.abs(kmat[:, 0] + np.sum(kmat[:, 3::2], axis=1))
    check_rbm_y = np.abs(kmat[:, 1] + np.sum(kmat[:, 4::2], axis=1))
    ndof = kmat.shape[0]
    unit_ur = np.zeros((ndof))
    unit_ur[2] = 1.0
    rx = coords[0, :]
    ry = coords[1, :]
    unit_ur[3::2] = -ry # x-displacement for pure (unit) rotation
    unit_ur[4::2] = rx  # y-displacement for pure (unit) rotation
    check_rbm_rot = np.dot(kmat, unit_ur)
    cond = np.linalg.cond(kcheck)
    symnorm = np.linalg.norm(np.transpose(kmat)-kmat)/np.linalg.norm(kmat)
    stiffness_ok = (cond < 1.e4)    # Nodal output typically single precision
    if cond > 1.e12:
        print('stiffness NOT OK, check for errors')
    elif cond > 1.e4:
        print('stiffness matrix badly conditioned, consider double precision for nodal output')
    
    # Put check to a non-conservative level (1e-4) to avoid output. But this seems rather high.
    # However, in the fortran uel code, the forces are calculated by considering displacements
    # relative the central node, hence the rbm are small and should not pose a numerical problem. 
    if any(np.array([np.max(check_rbm_x), np.max(check_rbm_y), np.max(check_rbm_rot)]) > 1.e-3):
        print('stiffness matrix sensitive to rbm')
        for n, v in enumerate(check_rbm_x):
            print('K*u [' + str(n) + '] for ux=1: %10.3e' % v)
        for n, v in enumerate(check_rbm_y):
            print('K*u [' + str(n) + '] for uy=1: %10.3e' % v)
        for n, v in enumerate(check_rbm_rot):
            print('K*u [' + str(n) + '] for ur=1: %10.3e' % v)
        
    print('determinant  = %10.3e' % np.linalg.det(kcheck))
    print('condition nr = %10.3e' % cond)
    print('|K-K^T|/|K|  = %10.3e' % symnorm)
    print('max rbm x effect = %10.3e' % np.max(check_rbm_x))
    print('max rbm y effect = %10.3e' % np.max(check_rbm_y))
    print('max rbm rot effect = %10.3e' % np.max(check_rbm_rot))