import sys


from rollover.utils import naming_mod as names
from rollover.three_d.utils import symmetric_mesh_module as sm

def main():
    the_model = mdb.models[names.rail_model]
    rail_part = the_model.parts[names.rail_part]
    
    sm.make_periodic_meshes(rail_part, 
                            source_sets=[rail_part.sets[names.rail_side_sets[0]]], 
                            target_sets=[rail_part.sets[names.rail_side_sets[1]]])
    
    rail_part.generateMesh()
	
	
	
if __name__ == '__main__':
	main()
