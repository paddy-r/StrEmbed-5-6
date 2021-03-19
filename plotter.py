# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 16:13:24 2021

@author: prehr
"""

import os
import copy

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.patches as patches

from score_saver import load_from_txt



''' HR 18/03/21
    To load Excel file of case study data that Alison created '''
def read_excel():
    folder = "C:\_Work\_DCS project\__ALL CODE\_Repos\StrEmbed-5-6\StrEmbed-5-6 for git"
    file = "Copy of data-from-Hugh - AMcK Copy.xlsx"

    a = pd.read_excel(os.path.join(folder, file), sheet_name = "Meta Information")

    cols = [el for el in a]
    yeses = [k for k,v in a[cols[5]].items() if v == 'y']
    part_names = [a[cols[1]][index] for index in yeses]
    print(part_names)

    categories = {}
    pairs = []
    for item in yeses:
        name, category = (a[cols[1]][item], a[cols[6]][item])
        pairs.append((name, category))
        if category in categories:
            categories[category].append(name)
        else:
            categories[category] = [name]

    return part_names, categories



def plot(step_folder = None, parts = None, categories = None):
    ''' Must find way to transfer this between saver and loader '''
    default_value = -1

    if not step_folder:
        # step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\Torch Assembly"
        step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\cakestep"
        # step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\assorted"
        # step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\77170325_1"

    ''' Dicts of similarity scores, from file '''
    bb_dict = load_from_txt(os.path.join(step_folder, 'scores_bb.txt'))
    ml_dict = load_from_txt(os.path.join(step_folder, 'scores.txt'))
    gr_dict = load_from_txt(os.path.join(step_folder, 'scores_graphlet.txt'))

    # if parts:
    #     for part in parts:
    #         if not part.endswith(('.step', '.stp', '.STEP', '.STP')):
    #             part = part + '.STEP'
    #             print(part)
    parts = sorted([el + '.STEP' for el in parts if not el.endswith('.STEP')])
    # if not parts:
    #     ''' Get parts from folder '''
    #     parts = [file for file in os.listdir(step_folder) if file.endswith('STEP')]
    #     ''' Get parts from data dict instead of from folder '''
    #     # parts = set()
    #     # for el in bb_dict:
    #     #     for part in el:
    #     #         parts.add(part)

    parts_list = list(parts)
    n = len(parts)

    ''' Create square matrices for plotting '''
    bb_mat = np.full((n,n), default_value).tolist()
    ml_mat = np.full((n,n), default_value).tolist()
    gr_mat = np.full((n,n), default_value).tolist()

    prod_mat = np.full((n,n), default_value).tolist()
    diff_mat = np.full((n,n), default_value).tolist()

    # for i,el in enumerate(parts_list):
    #     bb_mat[i][0:i-1] = [default_value]*(i-1)
    #     bb_mat[i][i:] = sim[el]
    #     ss_mat[i][0:i-1] = [default_value]*(i-1)
    #     ss_mat[i][i:] = ss[el]

    for i,el in enumerate(parts_list):
        for j,em in enumerate(parts_list):
            pair = (el,em)
            if pair in bb_dict:
                bb_mat[i][j] = bb_dict[pair]
            if pair in ml_dict:
                ml_mat[i][j] = ml_dict[pair]
            if pair in gr_dict:
                gr_mat[i][j] = gr_dict[pair]
                if pair in ml_dict:
                    if (gr_dict[pair] != default_value) and (ml_dict[pair] != default_value):
                        prod_mat[i][j] = gr_dict[pair]*ml_dict[pair]
                        diff_mat[i][j] = abs(gr_dict[pair] - ml_dict[pair])

    nrows = 1
    ncols = 3
    size = 14

    fig, ax = plt.subplots(nrows = nrows, ncols = ncols)
    ax[0].title.set_text('$S_{\\rm AR}$')
    ax[0].title.set_size(size)
    ax[1].title.set_text('$S_{\\rm ML}$')
    ax[1].title.set_size(size)
    ax[2].title.set_text('$S_{\\rm GR}$')
    ax[2].title.set_size(size)

    ax[0].tick_params(axis = 'both', which = 'major', labelsize = size)
    ax[1].tick_params(axis = 'both', which = 'major', labelsize = size)
    ax[2].tick_params(axis = 'both', which = 'major', labelsize = size)

    ax[1].set_xlabel('Similarity score (with part numbers)', size = size)

    ''' Colour map options
        Setting vmin means any data falling below are coloured out
        "gray_r" colour map is reversed grey (hence _r)
        so that lower half (unfilled) is light rather than dark '''
    cmap = copy.copy(cm.get_cmap("gray_r"))
    vmin = -0.001
    cmap.set_under(color = 'white')

    ax[0].imshow(bb_mat, cmap = cmap, vmin = vmin)
    ax[1].imshow(ml_mat, cmap = cmap, vmin = vmin)
    ax[2].imshow(gr_mat, cmap = cmap, vmin = vmin)

    fig.tight_layout()



    if categories:
        cat_list = list(categories)
        colours = plt.cm.get_cmap('hsv', len(cat_list))
        cat_col = {}
        for i,el in enumerate(cat_list):
            cat_col[el] = colours(i+1)
        cmap2 = []
        cmap2_edge = []
    else:
        cmap2 = 'black'

    bb_list = []
    ml_list = []
    gr_list = []
    for k,v in bb_dict.items():
        # if (v != default_value) and (ml_dict[k] != default_value) and (gr_dict[k] != default_value):
        if (ml_dict[k] != default_value) and (gr_dict[k] != default_value):
            if k[0] in parts_list and k[1] in parts_list:
                bb_list.append(v)
                ml_list.append(ml_dict[k])
                gr_list.append(gr_dict[k])
                ''' Map colours to part category membership '''
                if categories:
                    print(k[0], k[1])
                    category1 = [_k for _k,_v in categories.items() if k[0] in _v][0]
                    print(category1)
                    category2 = [_k for _k,_v in categories.items() if k[1] in _v][0]
                    c1 = cat_col[category1]
                    c2 = cat_col[category2]
                    cmap2.append(c1)
                    cmap2_edge.append(c2)

    fig2, ax2 = plt.subplots(1,1)
    ax2.scatter(ml_list, gr_list, s = 50, c = cmap2, edgecolors = cmap2_edge)
    # ax2.set_xlabel('Machine learning score')
    # ax2.set_ylabel('Graphlets score')
    ax2.set_xlabel('$S_{\\rm ML}$', size = size)
    ax2.set_ylabel('$S_{\\rm GR}$', size = size)

    ax2.tick_params(axis = 'both', which = 'major', labelsize = size)
    leg_el = [patches.Patch(facecolor = value, label = key) for key, value in cat_col.items()]
    ax2.legend(handles = leg_el, loc = 'lower right')    # x1,x2 = 0.65, 1.01
    # y1,y2 = 0.3, 1.01

    # # rect = patches.Rectangle((x1,y1), x2-x1, y2-y1, linewidth=1, edgecolor='r', facecolor='none')
    # rect = patches.Rectangle((x1,y1), x2-x1, y2-y1, linewidth=1, edgecolor = 'black', linestyle = 'dashed', facecolor = 'none')
    # ax2.add_patch(rect)
    manager = plt.get_current_fig_manager()
    ''' For wxAgg backend '''
    # manager.frame.Maximize(True)
    ''' For Qt4Agg backend '''
    manager.window.showMaximized()
    fig2.tight_layout()

    fig3, ax3 = plt.subplots(1,1)
    # ax3.imshow(prod_mat, cmap = cmap, vmin = vmin)
    # ax3.title.set_text('$S_{\\rm ML} \\circ S_{\\rm GR}$')
    pic = ax3.imshow(diff_mat, cmap = cmap, vmin = vmin)
    ax3.title.set_text('$|S_{\\rm ML} - S_{\\rm GR}|$')

    ax3.title.set_size(size)
    ax3.tick_params(axis = 'both', which = 'major', labelsize = size)
    fig3.colorbar(pic, ax = ax3)

    return cat_col, ml_list, gr_list, diff_mat



def proportion(ml_list, gr_list):
    x1,x2 = 0,0.001
    y1,y2 = 0,1

    y_list = []
    counter = 0
    for i,el in enumerate(ml_list):
        if el>x1 and el<x2 and gr_list[i]>y1 and gr_list[i]<y2:
            counter += 1
            y_list.append
    print('Data within region: ', counter)
    print('Proportion of total: ', counter/len(gr_list))
