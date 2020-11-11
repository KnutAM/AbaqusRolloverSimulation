Other notes
Contact using substructure:

Primary/secondary
* The stiffest surface should be the primary
* The most densily meshed should be the secondary


2D
Add truss element with very small stiffness on separate part, tie to substructure nodes. Use the same mesh discretization to ensure same node positions.
Ensure that normal is pointing towards contact, otherwise no contact will be detected. This is dependent on using side1Edges or side2Edges in .Surface()

3D
Section thickness
Using keywords, a surface can be defined without thickness. But this is not possible using CAE,
and it would require modification of the input file.