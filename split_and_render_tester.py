# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 15:23:17 2021

@author: prehr
"""
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Solid, TopoDS_Compound, TopoDS_Shell, TopoDS_Face, TopoDS_Vertex, TopoDS_Edge, TopoDS_Wire, TopoDS_CompSolid
from step_parse_5_6 import StepParse

# input_file = 'COMPOUND_13.STEP'
# input_file = 'Torch Assembly.STEP'
# input_file = 'cakestep.stp'
input_file = 'PARKING_TROLLEY.STEP'
# input_file = 'Steam Engine STEP.STEP'
# input_file = 'COMPOUND.STEP'
# input_file = 'Part6.STEP.STEP'
# input_file = 'MAIN FRAME_Default_As Machined_.STEP.STEP'
# input_file = '.STEP'
# input_file = 'COMPOUND.STEP'
# input_file = '9711-9350_SSTB2080-999_1.STEP'

g = StepParse()
g.load_step(input_file)

a,b = 'occ_name', 'screen_name'
for node in g.nodes:
    d = g.nodes[node]
    if d[a] != d[b]:
        print(node, d)

# g.split_and_render(path = "C:\_Work\_DCS project\__ALL CODE\_Repos\StrEmbed-5-6\StrEmbed-5-6 for git\dumptester")

