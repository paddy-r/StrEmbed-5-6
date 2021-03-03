# -*- coding: utf-8 -*-
"""
Created on Wed Mar  3 15:23:17 2021

@author: prehr
"""

input_file = 'Torch Assembly.STEP'

from step_parse_5_6 import StepParse
g = StepParse()

g.load_step(input_file)
g.OCC_read_file(input_file)

