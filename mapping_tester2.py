# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 13:58:11 2020

@author: prehr
"""

from step_parse_5_6 import StepParse, AssemblyManager
import networkx as nx


file1 = 'Torch Assembly.STEP'
file2 = 'Torch (with all four bulbs).STEP'

manager = AssemblyManager()

def print_all():
    print('\nNodes:')
    for node, dict in manager._lattice.nodes.items():
        print(node, dict)
    print('\nEdges:')
    for edge, dict in manager._lattice.edges.items():
        print(edge, dict)

_id1, _a1 = manager.new_assembly()
_a1.load_step(file1)
manager.AddToLattice(_id1)

_id2, _a2 = manager.new_assembly()
_a2.load_step(file2)
manager.AddToLattice(_id2, _dominant = 1)

_id3, _a3 = manager.new_assembly()
_a3.load_step(file1)
manager.AddToLattice(_id3, _dominant = 1)

# # _to_remove = nx.descendants(_a3,8)
# # for node in _to_remove:
# #     _a3.remove_node(node)
# # _a3.remove_node(8)
# manager.AddToLattice(_id3, _dominant = 1)


# n, nm = manager.add_node_in_lattice(_id1)
# manager.remove_node_in_lattice(_id1,n)
# manager.move_node_in_lattice(_id1,10,5)

print_all()
# manager.flatten_in_lattice(_id1,5)
# manager.flatten_in_lattice(_id2,1)


