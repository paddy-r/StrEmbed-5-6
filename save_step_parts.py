# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 16:03:16 2021

@author: prehr
"""

''' HR Feb 21
    To save individual STEP files for each shape/part in assembly file
    Also calculates bounding box + aspect ratios and saves images '''

from step_parse_5_6 import StepParse
from OCC.Extend import DataExchange
import os

# input_file = 'Torch Assembly.STEP'
# input_file = 'Torch (with all four bulbs).STEP'
# input_file = '5 parts_{3,1},1.STEP'
# input_file = 'PARKING_TROLLEY.STEP'
input_file = 'cakestep.stp'
# input_file = 'Steam Engine STEP.STEP'

g = StepParse()
g.load_step(input_file)
g.OCC_read_file(input_file)

cwd = os.getcwd()

part_dir = os.path.join(cwd, '__cakebox_parts')
if not os.path.exists(part_dir):
    print('Creating folder...')
    os.makedirs(part_dir)
else:
    print('Folder already exists...')

for k,v in g.OCC_dict.items():
    print('Saving STEP file for part ID: ', k)
    filename = g.part_dict[g.step_dict[k]]
    fullpath = os.path.join(cwd, '__cakebox_parts', filename + '.STEP')
    print(fullpath)
    DataExchange.write_step_file(v, fullpath)




