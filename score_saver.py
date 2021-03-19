# -*- coding: utf-8 -*-
"""
Created on Mon Mar 15 16:30:23 2021

@author: prehr
"""

import os

def save_to_txt(data, file = None):
    if not file:
        file = os.path.join(os.getcwd(), 'data.txt')
    with open(file, 'w+') as f:
        f.write(str(data))

def load_from_txt(file):
    with open(file, 'r') as f:
        for line in f.readlines():
            data = line
    return eval(data)


