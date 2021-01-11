# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 10:32:48 2020

@author: prehr
"""

from step_parse_5_6 import StepParse, AssemblyManager
# from StrEmbed_5_6 import MyParse
import networkx as nx

# a1 = StepParse(100)
# a2 = StepParse(200)
# a1 = MyParse(100)
# a2 = MyParse(200)

# file1 = 'cakestep.stp'

# file1 = 'PARKING_TROLLEY.STEP'
# file2 = 'PARKING_TROLLEY.STEP'

file1 = 'Torch Assembly.STEP'
# file2 = 'Torch Assembly.STEP'
file2 = 'Torch (with all four bulbs).STEP'



master = AssemblyManager()
a1 = master.new_assembly()
a2 = master.new_assembly()
lattice = master._lattice



a1.load_step(file1)
a2.load_step(file2)

a1.create_tree()
a2.create_tree()

# a1.OCC_read_file(file1)
# a2.OCC_read_file(file2)

# a1.remove_node(12)
# a1.add_node(1000, label = 'what', text = 'what')
# a1.add_edge(15,1000)

# a2.add_node(2000, label = 'hello', text = 'hello')
# a2.add_node(3000, label = 'why', text = 'how')
# a2.add_edge(6,2000)
# a2.add_edge(6,3000)

# a1.remove_redundants()
# a2.remove_redundants()

results = StepParse.map_nodes(a1,a2)
_node_map = results[0]
_edge_map = {}

_id1 = a1.assembly_id
_id2 = a2.assembly_id
# assembly_manager = {_id1: a1, _id2: a2}
# asses = [el for el in assembly_manager]

master_node_map = {}
master_edge_map = {}





def get_master_item(_map, ass, item):
    for k,v in _map.items():
        for _k,_v in v.items():
            if _k == ass and _v == item:
                return k



''' Add mapped nodes '''
for k,v in _node_map.items():
    _id = lattice.new_node_id
    lattice.add_node(_id)
    lattice.nodes[_id].update({_id1:k, _id2:v})
    # lattice.nodes[_id][_id1] = k
    # lattice.nodes[_id][_id2] = v
    master_node_map[_id] = {_id1:k, _id2:v}

''' Add unmapped nodes from a1 and a2 '''
_u1,_u2 = results[1]

for n1 in _u1:
    _id = lattice.new_node_id
    lattice.add_node(_id)
    lattice.nodes[_id][_id1] = n1
    master_node_map[_id] = {_id1:n1}

for n2 in _u2:
    _id = lattice.new_node_id
    lattice.add_node(_id)
    lattice.nodes[_id][_id2] = n2
    master_node_map[_id] = {_id2:n2}



_parts_dict = {}
_subs_dict = {}

for k,v in master_node_map.items():
    for _a,_n in v.items():
        _ass = master._mgr[_a]
        if _n in _ass.leaves:
            _parts_dict[k] = v
        else:
            _subs_dict[k] = v

for e1 in a1.edges:
    ''' Will throw key error if not in _node_map '''
    try:
        e2 = (_node_map[e1[0]],_node_map[e1[1]])
        if e2 in a2.edges:
            _edge_map[e1] = e2
    except:
        pass

for edge in _edge_map:
    _map= master_node_map
    u = get_master_item(_map, _id1, edge[0])
    v = get_master_item(_map, _id1, edge[1])
    master_edge = (u,v)
    master_edge_map[master_edge] = {_id1:edge, _id2:_edge_map[edge]}



''' Get remaining edges not common to both assemblies and add to master edge map '''
for ass in master._mgr:
    for e in master._mgr[ass].edges:
        if e not in _edge_map.keys():
            _map = master_node_map
            u = get_master_item(_map, ass, e[0])
            v = get_master_item(_map, ass, e[1])
            master_edge = (u,v)
            ''' Add to (or create) dict entry '''
            try:
                master_edge_map[master_edge].update({ass:e})
            except:
                master_edge_map[master_edge] = {ass:e}



''' Finally, create edges in master graph '''
for edge in master_edge_map:
    lattice.add_edge(edge[0], edge[1])



''' Nice plots, coloured according to whether common to a1, a2 or not '''

ass_col_dict = {a1.assembly_id: 'blue', a2.assembly_id: 'red'}
default_colour = 'black'

node_col_map = []
edge_col_map = []

for node in lattice.nodes:
    _map = master_node_map[node]
    if len(_map) == 1:
        ass = list(_map.keys())[0]
        colour = ass_col_dict[ass]
        node_col_map.append(colour)
    else:
        node_col_map.append(default_colour)

for edge in lattice.edges:
    _map = master_edge_map[edge]
    if len(_map) == 1:
        ass = list(_map.keys())[0]
        colour = ass_col_dict[ass]
        edge_col_map.append(colour)
    else:
        edge_col_map.append(default_colour)

nx.draw(lattice, node_color = node_col_map, edge_color = edge_col_map, with_labels = True)


# return lattice, master_node_map, master_edge_map, _node_map, _edge_map, _parts_dict, _subs_dict
