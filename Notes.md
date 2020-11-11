## Contact using substructure/uel:

### Primary/secondary
* The stiffest surface should be the primary
* The most densely meshed should be the secondary

### 2D
Add truss element with very small stiffness on separate part, tie to substructure nodes. Use the same mesh discretization to ensure same node positions.
Ensure that normal is pointing towards contact, otherwise no contact will be detected. This is dependent on using side1Edges or side2Edges in .Surface()

### 3D
**Surface normal**: Currently, we just assume that the surface normal direction will be correct. As the shadow elements are created in the same way from a solid surface this will likely work, but if not it is good to keep this note to know where to search for problems.

**Section thickness**: Using keywords, a surface can be defined without thickness. But this is not possible using CAE, and it would require modification of the input file. Currently, the surfaces have a thickness, but set to 1.e-9. This seem to work, but modifying the input file for the rail shadow surfaces might be good to avoid this issue completely (note that only one of two surfaces involved in contact can have zero thickness). ***Note***: Seems that this might only be an option in Abaqus explicit...