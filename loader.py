# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 16:13:24 2021

@author: prehr
"""

from step_parse_5_6 import StepParse
import os
import numpy as np
import matplotlib.pyplot as plt



def geo_abs(a,b):
    if a<b:
        return a/b
    else:
        return b/a


# input_file = 'C:\_Work\_DCS project\__ALL CODE\_Repos\StrEmbed-5-6\StrEmbed-5-6 for git\Torch Assembly\data.xlsx'
input_file = 'C:\_Work\_DCS project\__ALL CODE\_Repos\StrEmbed-5-6\StrEmbed-5-6 for git\cakestep\data.xlsx'

folder = os.getcwd()

g = StepParse()
bb,ss = g.load_bb_ss_data(input_file)
n = len(bb)
refs = [el for el in bb]

ar = {}
sim = {}

for k,v in bb.items():

    ''' Absolute sizes '''
    dx,dy,dz = v[-3:]

    ''' Aspect ratios, sorted '''
    ar[k] = sorted((dx/dy, dy/dz, dz/dx))

to_do = [el for el in refs]
for ref in refs:
    sim[ref] = []
    for ref2 in to_do:
        r1 = geo_abs(ar[ref][0], ar[ref2][0])
        r2 = geo_abs(ar[ref][1], ar[ref2][1])
        r3 = geo_abs(ar[ref][2], ar[ref2][2])
        s = (r1+r2+r3)/3
        # sim[(ref,ref2)] = s
        sim[ref].append(s)
    to_do.remove(ref)

''' Create square matrices for plotting '''
bb_mat = np.zeros((n,n)).tolist()
ss_mat = np.zeros((n,n)).tolist()

for i,el in enumerate(refs):
    bb_mat[i][i:] = sim[el]
    ss_mat[i][i:] = ss[el]

fig, ax = plt.subplots(nrows = 1, ncols = 2)
# ax[0, 0].plot(range(10), 'r') #row=0, col=0
# ax[0, 1].plot(range(10), 'g') #row=0, col=1
ax[0].imshow(bb_mat)
ax[1].imshow(ss_mat)

