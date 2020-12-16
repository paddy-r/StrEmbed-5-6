# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 13:58:11 2020

@author: prehr
"""

from step_parse_5_6 import AssemblyManager

manager = AssemblyManager()

_id1, _a1 = manager.new_assembly()
_a1.load_step('Torch Assembly.STEP')
_a1.create_tree()
manager.AddToLattice(_id1)

_id2, _a2 = manager.new_assembly()
_a2.load_step('Torch (with all four bulbs).STEP')
_a2.create_tree()

