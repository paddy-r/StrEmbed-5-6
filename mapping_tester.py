step# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 10:32:48 2020

@author: prehr
"""

from step_parse_5_5 import StepParse
from StrEmbed_5_5 import MyParse
# import networkx as nx

# a1 = StepParse()
# a2 = StepParse()
a1 = MyParse(100)
a2 = MyParse(200)

# file1 = 'cakestep.stp'

# file1 = 'PARKING_TROLLEY.STEP'
# file2 = 'PARKING_TROLLEY.STEP'

file1 = 'Torch Assembly.STEP'
file2 = 'Torch (with all four bulbs).STEP'



print('Loading files...\n\n')
a1.load_step(file1)
a2.load_step(file2)

a1.create_tree()
a2.create_tree()

print('Loaded files!\n\n')



# a1.remove_node(12)
# a1.add_node(1000, label = 'what', text = 'what')
# a1.add_edge(15,1000)

# a2.add_node(2000, label = 'hello', text = 'hello')
# a2.add_node(3000, label = 'why', text = 'how')
# a2.add_edge(6,2000)
# a2.add_edge(6,3000)

a1.remove_redundants()
a2.remove_redundants()

results = StepParse.map_nodes(a1,a2)
_map = results[0]

_id1 = a1._id
_id2 = a2._id
assembly_manager = {_id1: a1, _id2: a2}

master_node_map = {}
lattice = StepParse()



''' Add mapped nodes '''
for k,v in _map.items():
    _id = lattice.new_id
    lattice.add_node(_id, None, None)
    master_node_map[_id] = {_id1:k, _id2:v}



''' Add unmapped nodes '''
_u1 = results[1][0]
for n1 in _u1:
    _id = lattice.new_id
    lattice.add_node(_id, None, None)
    master_node_map[_id] = {_id1:n1}

_u2 = results[1][1]
for n2 in _u2:
    _id = lattice.new_id
    lattice.add_node(_id, None, None)
    master_node_map[_id] = {_id2:n2}
    


_parts_dict = {}
_subs_dict = {}

for k,v in master_node_map.items():
    _contains_leaf = False
    for _a,_n in v.items():
        _ass = assembly_manager[_a]
        if _n in _ass.leaves:
            print('Found leaf in assembly', _a, ': ', _n)
            _parts_dict[k] = v
        else:
            print('Not a leaf in assembly', _a, ':', _n)
            _subs_dict[k] = v
