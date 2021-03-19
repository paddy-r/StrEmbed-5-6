# -*- coding: utf-8 -*-
"""
Created on Sun Mar 14 15:02:13 2021

@author: prehr
"""

''' HR 14/03/21
    To load arbitrary STEP files from folder
    and compute bounding boxes and ML similiarity scores '''

import os
from OCC.Extend import DataExchange as dex
import numpy as np
from score_saver import load_from_txt, save_to_txt
from step_parse_5_6 import StepParse

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
# from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

def networkx_to_dgl(A_nx):
    # need to convert it into something dgl can work with
    node_dict = {} # to convert from A_nx nodes to dgl nodes
    part_count = 0
    assembly_count = 0
    face_count = 0

    face_str = []
    face_dst = []
    link_str = []
    link_dst = []
    assembly1_str = []
    assembly1_dst = []
    assembly2_str = []
    assembly2_dst = []

    #print("edges",A_nx.edges(data=True,keys=True))

    for node_str, node_dst, key, data in A_nx.edges(data=True,keys=True):
      t = data['type']
      # get nodes in dict
      tn_str = A_nx.nodes[node_str]['type']
      if node_str not in node_dict:
        if tn_str == 'part':
          node_dict[node_str] = part_count
          part_count += 1
        elif tn_str == "assembly":
          node_dict[node_str] = assembly_count
          assembly_count += 1
        elif tn_str == "face":
          node_dict[node_str] = face_count
          face_count += 1

      tn_dst = A_nx.nodes[node_dst]['type']
      if node_dst not in node_dict:
        if tn_dst == 'part':
          node_dict[node_dst] = part_count
          part_count += 1
        elif tn_dst == "assembly":
          node_dict[node_dst] = assembly_count
          assembly_count += 1
        elif tn_dst == "face":
          node_dict[node_dst] = face_count
          face_count += 1
      # there are three edge types so sort which ever one we are dealing with into that one

      if t == "face":
        assert tn_str == "face"
        assert tn_dst == "face"
        face_str.append(node_dict[node_str])
        face_dst.append(node_dict[node_dst])
      elif t == "link":
        # print("node_str, node_dst, key, data")
        # print(node_str, node_dst, key, data)
        # print("tn_str: ",tn_str)
        # print("tn_dst: ",tn_dst)
        assert tn_str == "face"
        assert tn_dst == "part"
        link_str.append(node_dict[node_str])
        link_dst.append(node_dict[node_dst])
      elif t == "assembly":
        assert tn_str == "assembly"
        assert tn_dst in ["assembly","part"]
        if tn_dst == "assembly":
          assembly1_str.append(node_dict[node_str])
          assembly1_dst.append(node_dict[node_dst])
        elif tn_dst == "part":
          assembly2_str.append(node_dict[node_str])
          assembly2_dst.append(node_dict[node_dst])

    # make heterograph
    A_dgl = dgl.heterograph({
      ('face','face','face') : ( face_str, face_dst ),
      ('face','link','part') : ( link_str, link_dst ), # part -> face
      ('assembly','assembly','part') : ( assembly2_str, assembly2_dst ), # these may be swapped around at some point
      ('assembly','assembly','assembly') : ( assembly1_str, assembly1_dst ),
      ('assembly','layer','part') : ([],[]),
      ('part','layer','part') : ([],[]),
      ('assembly','layer','assembly') : ([],[]),
      ('part','layer','assembly') : ([],[])
    })
    return A_dgl



''' Adapted from TH's "partfind_search_gui_hr" and "step_to_graph"
    Minimal code to get graphs of parts '''
def load_from_step(step_file):
    s_load = StepToGraph(step_file)
    g_load = networkx_to_dgl(s_load.H)
    face_g = g_load.node_type_subgraph(['face'])
    g_out = dgl.to_homogeneous(face_g)
    return g_out



def geo_abs(a,b):
    if a<b:
        return a/b
    else:
        return b/a



def get_aspect_ratios(shape, tol = 1e-6, use_mesh = True):

    bbox = Bnd_Box()
    bbox.SetGap(tol)
    if use_mesh:
        mesh = BRepMesh_IncrementalMesh()
        mesh.SetParallelDefault(True)
        mesh.SetShape(shape)
        mesh.Perform()
        if not mesh.IsDone():
            raise AssertionError("Mesh not done.")
    brepbndlib_Add(shape, bbox, use_mesh)

    xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
    dx,dy,dz = xmax-xmin, ymax-ymin, zmax-zmin

    ar = sorted((dx/dy, dy/dz, dz/dx))
    return ar



def get_bb_score(ar1, ar2):

    r1 = geo_abs(ar1[0], ar2[0])
    r2 = geo_abs(ar1[1], ar2[1])
    r3 = geo_abs(ar1[2], ar2[2])
    score = (r1+r2+r3)/3
    print('Score: ', score)
    return score



partfind_folder = "C:\_Work\_DCS project\__ALL CODE\_Repos\partfind\partfind for git"

''' -------------------------------------------------------------- '''
''' Import all partfind stuff from TH
    For now, just sets/resets cwd and grabs code from scripts '''
cwd_old = os.getcwd()
os.chdir(partfind_folder)

# from partfind_search_gui_hr import networkx_to_dgl
from step_to_graph import StepToGraph
from partgnn import PartGNN
from main import parameter_parser
import dgl

args = parameter_parser()
model = PartGNN(args)
model.load_model()

from utils import graphlet_pair_compare

''' Restore previous cwd '''
''' -------------------------------------------------------------- '''
os.chdir(cwd_old)

# step_folder = "C:\_Work\_DCS project\__ALL CODE\_Repos\StrEmbed-5-6\StrEmbed-5-6 for git\gears"
# step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\StrEmbed-5-6\\StrEmbed-5-6 for git\\assorted"
# step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\Torch Assembly"
# step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\cakestep"
step_folder = "C:\\_Work\\_DCS project\\__ALL CODE\\_Repos\\StrEmbed-5-6\\StrEmbed-5-6 for git\\77170325_1"
files = [file for file in os.listdir(step_folder) if file.endswith('STEP')]



''' Populate file dicts '''
shape_dict = {file:list(dex.read_step_file_with_names_colors(os.path.join(step_folder, file)))[0] for file in files}

graph_dict = {}
for file in files:
    try:
        graph_dict[file] = load_from_step(os.path.join(step_folder, file))
    except:
        graph_dict[file] = None

ar_dict = {}
for file in files:
    ar_dict[file] = get_aspect_ratios(shape_dict[file])



try:
    scores_loaded = load_from_txt(os.path.join(step_folder, 'scores.txt'))
except:
    scores_loaded = {}

try:
    scores_graphlet_loaded = load_from_txt(os.path.join(step_folder, 'scores_graphlet.txt'))
except:
    scores_graphlet_loaded ={}

try:
    scores_bb_loaded = load_from_txt(os.path.join(step_folder, 'scores_bb.txt'))
except:
    scores_bb_loaded = {}



default_value = -1
buffer_size = 10

done = []
scores = {}
scores_graphlet = {}
scores_bb = {}



count = 0

for file in files:
    try:
        # g1 = load_from_step(os.path.join(step_folder, file))
        g1 = graph_dict[file]
    except:
        g1 = None

    ''' Get OCC shape 1 '''
    # sh1 = dex.read_step_file_with_names_colors(os.path.join(step_folder, file))
    # sh1 = list(sh1)[0]
    sh1 = shape_dict[file]
    ar1 = ar_dict[file]

    to_do = [el for el in files if el not in done]
    for file2 in to_do:
        try:
            # g2 = load_from_step(os.path.join(step_folder, file2))
            g2 = graph_dict[file2]
        except:
            g2 = None

        ''' Get OCC shape 2 '''
        # sh2 = dex.read_step_file_with_names_colors(os.path.join(step_folder, file2))
        # sh2 = list(sh2)[0]
        sh2 = shape_dict[file2]
        ar2 = ar_dict[file2]

        if (file,file2) in scores_loaded:
            print('Score ML found')
            scores[(file,file2)] = scores_loaded[(file,file2)]
        else:
            print('Score ML not found; calculating...')
            try:
                scores[(file,file2)] = model.test_pair(g1,g2)
            except:
                scores[(file,file2)] = default_value

        if (file,file2) in scores_graphlet_loaded:
            print('Score GR found')
            scores_graphlet[(file,file2)] = scores_graphlet_loaded[(file,file2)]
        else:
            print('Score GR not found; calculating...')
            try:
                scores_graphlet[(file,file2)] = graphlet_pair_compare(g1,g2)
            except:
                scores_graphlet[(file,file2)] = default_value

        if (file,file2) in scores_bb_loaded:
            print('Score BB found')
            scores_bb[(file,file2)] = scores_bb_loaded[(file,file2)]
        else:
            print('Score BB not found; calculating...')
            try:
                scores_bb[(file,file2)] = get_bb_score(ar1,ar2)
            except:
                scores_bb[(file,file2)] = default_value

        count += 1
        print('Count = ', count)
        ''' Save if buffer limit reached '''
        if (count % buffer_size == 0) or (file2 == to_do[-1]):
            print('Saving buffer...')
            save_to_txt(scores, os.path.join(step_folder, 'scores.txt'))
            save_to_txt(scores_graphlet, os.path.join(step_folder, 'scores_graphlet.txt'))
            save_to_txt(scores_bb, os.path.join(step_folder, 'scores_bb.txt'))


    done.append(file)


