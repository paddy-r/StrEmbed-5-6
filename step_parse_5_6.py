# HR 19/08/2019 to 10/12/2019
# Added all extra code I've done up to this point

# TH: I am using this to turn the script into a module file to make it useable else where
# We can add functionally as new things are made.

# HR July 2019
# To parse STEP file

### ---
# HR 12/12/2019 onwards
# Version 5.2
### ---

### ---
# HR 23/03/2020 onwards
# Version 5.3
### ---
# Removed treelib entirely, now using networkx for all operations
# A lot of old functionality replaced with simpler networkx methods

'''HR 11/08/20 onwards
Version 5.5'''

'''HR 02/12/20 onwards
Version 5.6 '''

# # Regular expression module
# import re

# Natural Language Toolkit module, for Levenshtein distance
import nltk

import numpy as np
from scipy.special import binom
# from math import log
# import pandas as pd

# # For powerset construction
# from itertools import chain, combinations

# def powerset(iterable):
#     "e.g. powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
#     s = list(iterable)
#     return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

# Import networkx for plotting lattice
import networkx as nx

''' MPL for default viewer if run outside GUI '''
import matplotlib as mpl

#TH: useful for working with files
import os

# ''' For data exchange export '''
# import xlsxwriter

# HR 10/7/20 All python-occ imports for 3D viewer
# from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Solid, TopoDS_Compound, TopoDS_Shell, TopoDS_Face, TopoDS_Vertex, TopoDS_Edge, TopoDS_Wire, TopoDS_CompSolid
# from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
# from OCC.Core.StlAPI import stlapi_Read, StlAPI_Writer
# from OCC.Core.BRep import BRep_Builder
# from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Pnt2d
# from OCC.Core.Bnd import Bnd_Box2d
# from OCC.Core.TopoDS import TopoDS_Compound
# from OCC.Core.IGESControl import IGESControl_Reader, IGESControl_Writer
# from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer, STEPControl_AsIs
# from OCC.Core.Interface import Interface_Static_SetCVal
from OCC.Core.IFSelect import IFSelect_RetDone
# from OCC.Core.IFSelect import IFSelect_ItemsByEntity
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.XCAFDoc import (XCAFDoc_DocumentTool_ShapeTool,
                              XCAFDoc_DocumentTool_ColorTool)
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
from OCC.Core.TDF import TDF_LabelSequence, TDF_Label
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.TopLoc import TopLoc_Location
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform

# from OCC.Extend.TopologyUtils import (discretize_edge, get_sorted_hlr_edges,
                                      # list_of_shapes_to_compound)

from OCC.Display import OCCViewer
from OCC.Core.Quantity import (Quantity_Color, Quantity_NOC_WHITE, Quantity_TOC_RGB)
from OCC.Extend import DataExchange
from OCC.Core.Graphic3d import Graphic3d_BufferType

from OCC.Core.Bnd import Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib_Add
# from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh



def remove_suffixes(_str, suffixes = ('.stp', '.step', '.STP', '.STEP')):
    ''' endswith accept tuple '''
    while _str.endswith(suffixes):
        _str = os.path.splitext(_str)[0]
    return _str



''' HR 26/04/21
    To get lines (e.g. in STEP file) with certain keywords present or not
    Adapted from earlier script
    Keep here for now but not best place for it '''
def step_search(file, keywords = None, exclusions = None, any_mode = True):

    if not file:
        print('File not found; aborting')
        return

    if not keywords:
        keywords = ['NEXT_']
        # keywords = ['MANIFOLD', 'PRODUCT ', 'CLOSED', 'ADVANCED']

    if not exclusions:
        exclusions = ['kevinphilipsbong']

    results = []

    # with open(file) as f:
    #     for i,line in enumerate(f):
    #         if any(word in line for word in keywords) and not any(_word in line for _word in exclusions):
    #             results.append(line)

    ''' HR 4/5/21 updated to account for lines running over '''
    with open(file) as f:
        ''' Create empty running line to append text to '''
        full_line = ''
        for i,line in enumerate(f):
            ''' Append to running line, removing trailing newline chars '''
            full_line += line.replace('\n', '')
            ''' If ending line, do actual search... '''
            if line.endswith(';\n'):
                if any_mode:
                    if any(word in full_line for word in keywords) and not any(_word in full_line for _word in exclusions):
                        results.append(full_line)
                else:
                    if all(word in full_line for word in keywords) and not any(_word in full_line for _word in exclusions):
                        results.append(full_line)
                ''' ...and make new empty running line '''
                full_line = ''

    keyword_dict = {}
    for keyword in keywords:
        keyword_dict[keyword] = []
        for line in results:
            if keyword in line:
                keyword_dict[keyword].append(line)

    return results, keyword_dict



"""
HR 26/08/2020
ShapeRenderer adapted from pythonocc script "wxDisplay"
https://github.com/tpaviot/pythonocc-core
"""
class ShapeRenderer(OCCViewer.Viewer3d):
    '''
    HR 17/7/20
    Adapted/simplified from OffScreenRenderer in OCCViewer <- OCC.Display
    Dumps render of shape to jpeg file
    '''
    def __init__(self, screen_size = (1000,1000)):
        super().__init__()
        self.Create()
        self.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_WHITE))
        self.SetSize(screen_size[0], screen_size[1])
        # self.DisableAntiAliasing()
        self.SetModeShaded()
        # self.display_triedron()
        self.SetRaytracingMode(depth = 5)
        self._rendered = False





''' To contain lattice structure that manages/contains all assemblies '''
class AssemblyManager():

    def __init__(self, viewer = None, axes = None, ic = None, dc = None, sc = None, lc = None, lattice_plot_mode = True, *args, **kwargs):
        self._mgr = {}
        self._lattice = StepParse('lattice')

        # self.new_assembly_text = 'Unnamed item'
        # self.new_part_text     = 'Unnamed item'

        self.ENFORCE_BINARY_DEFAULT = True
        self.DO_ALL_LATTICE_LINES = True

        '''
            Set up lattice plot viewer
            Default is MPL viewer
        '''
        if viewer:
            self.viewer = viewer
        else:
            self.viewer = mpl.pyplot.figure()
        if axes:
            self.axes = axes
        else:
            self.axes = self.viewer.add_subplot(111)

        ''' Turn off all axis lines and ticks '''
        self.axes.axis('off')
        self.axes.axes.get_xaxis().set_ticks([])
        self.axes.axes.get_yaxis().set_ticks([])

        self._lattice.origin = (0,0)

        self.lattice_plot_mode = lattice_plot_mode

        ''' Set up colouring '''
        self.INACTIVE_COLOUR_DEFAULT = 'darkgray'
        self.DEFAULT_COLOUR_DEFAULT = 'red'
        self.SELECTED_COLOUR_DEFAULT = 'blue'
        self.LINE_COLOUR_DEFAULT = 'lightgray'

        if not ic:
            self.ic = self.INACTIVE_COLOUR_DEFAULT
        else:
            self.ic = ic
        if not dc:
            self.dc = self.DEFAULT_COLOUR_DEFAULT
        else:
            self.dc = dc
        if not sc:
            self.sc = self.SELECTED_COLOUR_DEFAULT
        else:
            self.sc = sc
        if not lc:
            self.lc = self.LINE_COLOUR_DEFAULT
        else:
            self.lc = lc



    @property
    def new_assembly_id(self):
        if not hasattr(self, "assembly_id_counter"):
            self.assembly_id_counter = 0
        self.assembly_id_counter += 1
        return self.assembly_id_counter



    def new_assembly(self, _dominant = None):
        _assembly_id = self.new_assembly_id
        _assembly = StepParse(_assembly_id)
        self._mgr.update({_assembly_id:_assembly})
        print('Created new assembly with ID: ', _assembly_id)

        _assembly.enforce_binary = self.ENFORCE_BINARY_DEFAULT

        return _assembly_id, _assembly



    def remove_assembly(self, _id):
        if _id in self._mgr:
            print('Assembly ', _id, 'found in and removed from manager')
            ''' Try and remove from lattice '''
            self.RemoveFromLattice(_id)
            self._mgr.pop(_id)
            return True
        else:
            print('Assembly ', _id, 'not found in manager; could not be removed')
            return False



    ''' Get lattice node corresponding to node in given assembly
        Return lattice node if present, otherwise None '''
    def get_master_node(self, _assembly_id, _item):
        for node in self._lattice.nodes:
            for k,v in self._lattice.nodes[node].items():
                if k == _assembly_id and v == _item:
                    return node
        return None





    ''' ----------------------------------------------------------------------
        ----------------------------------------------------------------------
        HR JAN 2021 ASSEMBLY OPERATIONS TO BE REFERRED TO IN GUI
        Plan:
        - Copy existing methods from GUI and check they're working
        - Goal is to remove any reference to individual assemblies in GUI,
            all interactions in GUI should be with assembly manager here
        - COMPLETE FEB 2021! I am a neat guy!
    '''



    def add_edge_in_lattice(self, _id, u, v):

        '''
        Assembly-specific operations
        '''
        _ass = self._mgr[_id]
        _ass.add_edge(u, v)

        '''
        Lattice operations
        '''
        _um = self.get_master_node(_id, u)
        _vm = self.get_master_node(_id, v)

        if (_um,_vm) in self._lattice.edges:
            print('Edge already exists; adding entry')
        else:
            print('Edge does not exist in lattice; creating new edge and entry')
            self._lattice.add_edge(_um,_vm)
        self._lattice.edges[(_um,_vm)].update({_id:(u,v)})




    def remove_edge_in_lattice(self, _id, u, v):

        '''
        Assembly-specific operations
        '''
        _ass = self._mgr[_id]
        _ass.remove_edge(u, v)

        '''
        Lattice operations
        '''
        _um = self.get_master_node(_id, u)
        _vm = self.get_master_node(_id, v)

        _len = len(self._lattice.edges[(_um,_vm)])
        if _len == 1:
            print('Edge dict has len = 1; removing whole edge')
            self._lattice.remove_edge(_um,_vm)
        else:
            print('Edge dict has len > 1; removing edge dict entry for assembly')
            self._lattice.edges[(_um,_vm)].pop(_id)



    def add_node_in_lattice(self, _id, _parent, _disaggregate = False, **attr):

        _ass = self._mgr[_id]
        leaves = _ass.leaves

        ''' Allow node to be added to leaf if "disaggregate" flag is true '''
        if _parent not in leaves:
            print('ID of node to add node to: ', _parent)
        else:
            if not _disaggregate:
                print('Cannot add node: item is a leaf node/irreducible part')
                print('To add node, disaggregate part first')
                return

        _node = _ass.new_node_id

        '''
        Assembly-specific operations
        '''
        _ass.add_node(_node, **attr)

        '''
        Lattice operations
        '''
        _nodem = self._lattice.new_node_id
        self._lattice.add_node(_nodem)
        self._lattice.nodes[_nodem].update({_id:_node})

        self.add_edge_in_lattice(_id, _parent, _node)

        return _node, _nodem



    def enforce_binary(self, _id, _node):

        _ass = self._mgr[_id]

        ''' Abort if not enforced '''
        if not _ass.enforce_binary:
            print('Not enforcing binary relations; disallowed for assembly ', _id)
            return

        _parent = _ass.get_parent(_node)
        _children = [el for el in _ass.successors(_node)]

        ''' Abort if more than one child '''
        if not len(_children) == 1:
            return

        print('Single child; removing and linking past node')
        print('Assembly ', _id, '; node ', _node)

        ''' Reparent orphans-to-be '''
        for _child in _children:
            self.move_node_in_lattice(_id, _child, _parent)

        ''' Finally, remove redundant node '''
        self.remove_node_in_lattice(_id, _node)



    def remove_node_in_lattice(self, _id, _node):

        _ass = self._mgr[_id]
        _nm = self.get_master_node(_id, _node)

        _parent = _ass.get_parent(_node)
        _leaves = _ass.leaves

        '''
        NOTES
        - Order of operations is unusual here, to avoid missing edges
        1. Reparent (move) children, if node is sub-assembly,
            with veto of binary enforcement (as not necessary if sub-ass)
        2. Other redundant edges are then removed in lattice first
        3. Then node/edges removed in assembly
        4. Then remaining node/edge references removed in lattice dicts
        5. Last, binary relations enforced if necessary
        '''

        ''' Reparent orphans to node parent if node is sub-assembly '''
        if _node not in _leaves:
            orphans = [el for el in _ass.successors(_node)]
            for orphan in orphans:
                self.move_node_in_lattice(_id, orphan, _parent, veto_binary = True)

        _ins = list(_ass.in_edges(_node))
        _outs = list(_ass.out_edges(_node))

        ''' Remove now-redundant edges (lattice) '''
        _edges = _ins + _outs
        for _edge in _edges:
            print('Removing edge: ', _edge[0], _edge[1])
            self.remove_edge_in_lattice(_id, _edge[0], _edge[1])

        ''' Remove node and edges (assembly) '''
        _ass.remove_node(_node)

        ''' Remove node (dicts in lattice) '''
        _len = len(self._lattice.nodes[_nm])
        if _len == 1:
            print('Node dict has len = 1; removing whole node')
            self._lattice.remove_node(_nm)
        else:
            print('Node dict has len > 1; removing node dict entry for assembly')
            self._lattice.nodes[_nm].pop(_id)

        ''' If original node is leaf, enforce binary relations if necessary '''
        if _node in _leaves:
            self.enforce_binary(_id, _parent)



    def move_node_in_lattice(self, _id, _node, _parent, veto_binary = False):

        _ass = self._mgr[_id]
        _old_parent = _ass.get_parent(_node)

        if _old_parent == _parent:
            return

        ''' Check if is root, i.e. has no parent '''
        if (_old_parent is None):
            print('Root node cannot be moved; not proceeding')
            return False

        ''' Remove old edge '''
        self.remove_edge_in_lattice(_id, _old_parent, _node)

        ''' Create new edge '''
        self.add_edge_in_lattice(_id, _parent, _node)

        ''' Enforce binary relations if necessary '''
        if not veto_binary:
            self.enforce_binary(_id, _old_parent)

        return True



    def assemble_in_lattice(self, _id, _nodes, **attr):

        _ass = self._mgr[_id]

        ''' Check root is not present in nodes '''
        _root = _ass.get_root()
        if _root in _nodes:
            _nodes.remove(_root)
            print('Removed root from items to assemble')

        '''
        MAIN "ASSEMBLE" ALGORITHM
        '''

        ''' Get selected item that is highest up tree (i.e. lowest depth) '''
        depths = {}
        for _node in _nodes:
            depths[_node] = _ass.node_depth(_node)
            print('ID = ', _node, '; parent depth = ', depths[_node])
        highest_node = min(depths, key = depths.get)
        new_parent = _ass.get_parent(highest_node)
        print('New parent = ', new_parent)

        ''' Get valid ID for new node then create '''
        new_sub, _ = self.add_node_in_lattice(_id, new_parent, **attr)

        ''' Move all selected items to be children of new node '''
        for _node in _nodes:
            self.move_node_in_lattice(_id, _node, new_sub)

        return new_sub



    def flatten_in_lattice(self, _id, _node):

        _ass = self._mgr[_id]
        leaves = _ass.leaves
        print('Leaves: ', leaves)

        if _node not in leaves:
            print('ID of item to flatten = ', _node)
        else:
            print('Cannot flatten: item is a leaf node/irreducible part\n')
            return

        '''
        MAIN "FLATTEN" ALGORITHM
        '''

        ''' Get all children of item '''
        ch = nx.descendants(_ass, _node)
        ch_parts = [el for el in ch if el in leaves]
        print('Children parts = ', ch_parts)
        ch_ass = [el for el in ch if not el in leaves]
        print('Children assemblies = ', ch_ass)

        ''' Move all children that are indivisible parts '''
        for child in ch_parts:
            self.move_node_in_lattice(_id, child, _node)

        ''' Delete all children that are assemblies '''
        for child in ch_ass:
            self.remove_node_in_lattice(_id, child)

        return True



    def disaggregate_in_lattice(self, _id, _node, num_disagg = 2, **attr):

        _ass = self._mgr[_id]
        leaves = _ass.leaves

        if _node in leaves:
            print('ID of item to disaggregate = ', _node)
        else:
            print('Cannot disaggregate: item is not a leaf node/irreducible part\n')
            return

        '''
        MAIN "DISAGGREGATE" ALGORITHM
        '''

        ''' Get valid ID for new node then create '''
        _new_nodes = []
        for i in range(num_disagg):
            new_node, _ = self.add_node_in_lattice(_id, _node, _disaggregate = True, **attr)
            _new_nodes.append(new_node)

        return _new_nodes



    def aggregate_in_lattice(self, _id, _node):

        _ass = self._mgr[_id]
        leaves = _ass.leaves

        if not _node in leaves:
            print('ID of item to aggregate = ', _node)
        else:
            print('Cannot aggregate: item is a leaf node/irreducible part\n')
            return

        '''
        MAIN "AGGREGATE" ALGORITHM
        '''

        ''' Get children of node and remove '''
        _removed_nodes = []
        ch = nx.descendants(_ass, _node)
        print('Children aggregated: ', ch)
        for child in ch:
            try:
                self.remove_node_in_lattice(_id, child)
                print('Removed node ', child)
                _removed_nodes.append(child)
            except:
                print('Could not delete node')

        return _removed_nodes



    ''' ----------------------------------------------------------------------
        ADD TO/REMOVE FROM LATTICE
        ----------------------------------------------------------------------
    '''



    def AddToLattice(self, _id, _dominant = None):

        if not self._mgr:
            print('Cannot add assembly to lattice: no assembly in manager')
            return False

        if _id not in self._mgr:
            print('ID: ', _id)
            print('Assembly not in manager; not proceeding')
            return False

        ''' If first assembly being added, just map nodes and edges directly
            No need to do any similarity calculations '''
        if len(self._mgr) == 1:

            print('Adding first assembly to lattice')
            _a1 = self._mgr[_id]

            for node in _a1.nodes:
                new_node = self._lattice.new_node_id
                self._lattice.add_node(new_node)
                self._lattice.nodes[new_node].update({_id:node})

            ''' Nodes must exist as edges require "get_master_node" '''
            for n1,n2 in _a1.edges:
                u = self.get_master_node(_id, n1)
                v = self.get_master_node(_id, n2)
                self._lattice.add_edge(u,v)
                self._lattice.edges[(u,v)].update({_id:(n1,n2)})

            return True



        ''' If no dominant assembly specified/not found
            get the one with lowest ID '''
        if (not _dominant) or (_dominant not in self._mgr):
            print('Dominant assembly not specified or not found in manager; defaulting to assembly with lowest ID')
            _idlist = sorted([el for el in self._mgr])
            _idlist.remove(_id)
            _dominant = _idlist[0]



        ''' Assemblies to be compared established by this point '''
        print('ID of dominant assembly in manager: ', _dominant)
        print('ID of assembly to be added:         ', _id)

        _id1 = _dominant
        _id2 = _id

        _a1 = self._mgr[_id1]
        _a2 = self._mgr[_id2]
        print('a1 nodes: ', _a1.nodes)
        print('a2 nodes: ', _a2.nodes)



        '''
        MAIN SECTION:
            1. DO NODE COMPARISON AND COMPUTE PAIR-WISE SIMILARITIES
            2. GET NODE MAP BETWEEN DOMINANT AND NEW ASSEMBLIES
            3. ADD NEW ASSEMBLY TO LATTICE GRAPH
        '''
        results = self.map_nodes(_a1, _a2)

        ''' Get node map (n1:n2) and lists of unmapped nodes in a1 and a2 '''
        _map = results[0]
        _u1, _u2 = results[1]

        ''' Show results '''
        print('Mapping results: ')
        f = 'screen_name'
        for k,v in results[0].items():
            print('a1 node: ', _a1.nodes[k][f], 'a2 node: ', _a2.nodes[v][f])

        '''
            NODES
        '''

        ''' Append to existing master node dict if already present... '''
        for n1,n2 in _map.items():
            ''' Returns None if not present... '''
            _master_node = self.get_master_node(_id1, n1)
            ''' ...but if already present, add... '''
            if _master_node:
                self._lattice.nodes[_master_node].update({_id2:n2})

        ''' ...else create new master node entry '''
        for n2 in _u2:
            _node = self._lattice.new_node_id
            self._lattice.add_node(_node)
            self._lattice.nodes[_node].update({_id2:n2})


        '''
            EDGES
        '''

        for n1,n2 in _a2.edges:
            m1 = self.get_master_node(_id2, n1)
            m2 = self.get_master_node(_id2, n2)
            if m1 and m2:
                ''' Create master edge if not present '''
                if (m1,m2) not in self._lattice.edges:
                    self._lattice.add_edge(m1,m2)
                ''' Lastly, create new entry '''
                self._lattice.edges[(m1,m2)].update({_id2:(n1,n2)})

        return True



    def RemoveFromLattice(self, _id):

        if not self._mgr:
            print('Cannot remove assembly from lattice: no assembly in manager')
            return False

        if _id not in self._mgr:
            print('ID: ', _id)
            print('Assembly not in manager; not proceeding')
            return False

        ''' CASE 1: Lattice only contains single assembly '''
        if len(self._mgr) == 1:
            nodes = [node for node in self._lattice.nodes]
            ''' Edges will be removed automatically when their nodes are removed '''
            for node in nodes:
                self._lattice.remove_node(node)
            return True

        ''' CASE 2: Lattice has more than one assembly in it '''
        _nodes = list(self._lattice.nodes)
        _edges = list(self._lattice.edges)

        for _edge in _edges:
            _dict = self._lattice.edges[_edge]
            if _id in _dict:
                ''' Remove entry for assembly in lattice dict... '''
                _dict.pop(_id)
                if not any(ass in _dict for ass in self._mgr):
                    ''' ...and remove entirely if no other assemblies in dict '''
                    self._lattice.remove_edge(_edge[0],_edge[1])

        for _node in _nodes:
            _dict = self._lattice.nodes[_node]
            if _id in _dict:
                ''' Remove entry for assembly in lattice dict... '''
                _dict.pop(_id)
                if not any(ass in _dict for ass in self._mgr):
                    ''' ...and remove entirely if no other assemblies in dict '''
                    self._lattice.remove_node(_node)

        return True



    ''' ----------------------------------------------------------------------
        HR June 21: All similarity/assembly matching methods here,
            refactored from StepParse class methods
        ----------------------------------------------------------------------
    '''



    '''
    HR June 21 Must refactor this, moved from StepParse class method
    NOT TESTED
    '''
    # ''' ---------------
    # TREE RECONCILIATION
    # HR 3/6/20
    # Based on Networkx "optimal_edit_paths" method

    # a1 and a2 are assemblies 1 and 2
    # Call as "paths, cost = StepParse.Reconcile(a1, a2)"
    # ----------------'''

    def Reconcile(self, id1, id2, lev_tol = 0.1):

        ''' -------------------------------------------
        STAGE 1: MAP NODES/EDGES B/T THE TWO ASSEMBLIES

        Currently done simply via tags
        More sophisticated metrics to be implemented in future

        Method of assembly class (StepParse) to set item tags to their IDs
        --------------------------------------------'''
        a1 = self._mgr[id1]
        a2 = self._mgr[id2]

        a1.set_all_tags()
        a2.set_all_tags()



        def similarity(str1, str2):

            _lev_dist  = nltk.edit_distance(str1, str2)
            _sim = 1 - _lev_dist/max(len(str1), len(str2))

            return _lev_dist, _sim



        # def remove_special_chars(_str):

        #     # Strip out special characters
        #     _str = re.sub('[!@#$_]', '', _str)

        #     return _str



        ''' Comparing nodes directly gives equality simply if both are NX nodes...
            ...i.e. same object type, but this isn't good enough...'
            ...so equality in this context defined as having same tags '''
        def return_eq(item1, item2):

            _eq = False

            tag1 = item1['tag']
            tag2 = item2['tag']

            ''' 1. Simple equality test based on tags
                (which are just IDs copied to "tag" field)... '''
            _eq = tag1 == tag2
            if _eq:
                print('Mapped ', tag1, 'to ', tag2)

            # ''' 2. ...then do test based on parts contained by nodes... '''
            # if tag1 and tag2 in (a1.nodes or a2.nodes) and not _eq:
            #     try:
            #         _eq = item1['parts'] == item2['parts']
            #     except:
            #         pass

            # ''' 3. ...then do test based on Levenshtein distance b/t items, if leaves '''
            # if not _eq and (tag1 and tag2 in (a1.leaves or a2.leaves)):

            #     tag1_ = remove_special_chars(tag1)
            #     tag2_ = remove_special_chars(tag2)

            #     try:
            #         dist = similarity(tag1_, tag2_)
            #         _eq  = dist < lev_tol
            #     except:
            #         pass

            # if _eq:
            #     print('Nodes/edges mapped:     ', tag1, tag2)
            # else:
            #     pass

            return _eq
            # return item1 == item2




        def MyReconcile(a1, a2, node_match = None, edge_match = None):

            a1.set_all_tags()
            a2.set_all_tags()

            n1 = set(a1.nodes)
            n2 = set(a2.nodes)
            e1 = set(a1.edges)
            e2 = set(a2.edges)

            node_deletions = []
            node_additions = []
            edge_deletions = []
            edge_additions = []

            ''' Find additions and deletions by set difference (relative complement) '''
            #
            for _node in n1 - n2:
                node_deletions.append((_node, None))
            print('Node deletions: ', node_deletions)

            for _node in n2 - n1:
                node_additions.append((None, _node))
            print('Node deletions: ', node_additions)

            for _edge in e1 - e2:
                edge_deletions.append((_edge, None))
            print('Edge deletions: ', edge_deletions)

            for _edge in e2 - e1:
                edge_additions.append((None, _edge))
            print('Edge additions: ', edge_additions)



            paths = [list(set(node_deletions + node_additions)), list(set(edge_deletions + edge_additions))]

            cost = len(node_deletions) + len(node_additions) + len(edge_deletions) + len(edge_additions)

            return paths, cost


        ''' -----------------------------------------------------
        STAGE 2: FIND EDIT PATHS VIA NETWORKX AND GENERATE REPORT
        ------------------------------------------------------'''

        # paths, cost_nx = nx.optimal_edit_paths(a1, a2, node_match = return_eq, edge_match = return_eq)
        # paths = paths[0]

        paths, cost = MyReconcile(a1, a2, node_match = return_eq, edge_match = return_eq)

        node_edits = [el for el in paths[0] if el[0] != el[1]]
        edge_edits = [el for el in paths[1] if el[0] != el[1]]
        cost_from_edits = len(node_edits) + len(edge_edits)

        print('Node edits: {}\nEdge edits: {}\nTotal cost (Networkx): {}\nTotal cost (no. of edits): {}'.format(
            node_edits, edge_edits, cost, cost_from_edits))

        return paths, cost, cost_from_edits, node_edits, edge_edits





    ''' HR June 21 Must refactor this, moved from StepParse class method '''
    def similarity(self, str1, str2):

        if type(str1) != str:
            str1 = str(str1)
        if type(str2) != str:
            str2 = str(str2)

        _lev_dist = nltk.edit_distance(str1, str2)
        _sim = 1 - _lev_dist/max(len(str1), len(str2))

        return _lev_dist, _sim



    def map_nodes(self, a1, a2, **kwargs):

        _mapped = {}



        '''
        1.  Easy part of mapping: exact 1:1 mappings
            and get dupe map for any unmapped exact matches
        '''
        _dupemap, _newitems = self.map_exact(a1,a2)
        _mapped.update(_newitems)



        ''' Then calculate similarity matrix for each duplicate group
            This effectively allows matching by similarity components
            other than (but also including) exact node-name matches,
            e.g. parent node names (or whatever the user specifies
            via "weight" values in "node_sim") '''

        _sim = {}
        for k,v in _dupemap.items():
            _sim[k] = self.node_sim(a1, a2, k, v)



        ''' Get total similarity (i.e. sum of all measures)
            "_sim" contains each separately; [0] element is total value '''
        _totals = {k:v[0] for k,v in _sim.items()}



        '''
        2.  Get all singular mappings within duplicate groupings,
            i.e. occurrence of max value is one, and remove from grouping
        '''

        _tomap = {k:v for k,v in _dupemap.items()}
        _totalscopy = {k:v for k,v in _totals.items()}

        for k,v in _tomap.items():

            ''' Get singular mappings and update global map '''
            _newlymapped = self.get_by_max(_totals[k])

            ''' Remove old/create new dict items if any mappings made above '''
            if _newlymapped:

                ''' Add new entries to master map '''
                _mapped.update(_newlymapped)

                ''' Get new entries with already-mapped items removed... '''
                _newdupe, _newtotals = self.remap_entries(k, v, _newlymapped, _totalscopy[k])

                ''' ...then update dicts with new entries '''
                if _newdupe:
                    _dupemap.update(_newdupe)
                if _newtotals:
                    _totals.update(_newtotals)

                ''' Remove old entries with "pop";
                    'None' default in "pop" avoids exception if item not found '''
                _dupemap.pop(k, None)
                _totals.pop(k, None)



        for k,v in _totals.items():

            ''' Reform sub-groupings within each duplicate grouping
                "_valuelen" should be two or more for all entries now,
                as all single-occurrence values removed above '''

            _newentries = self.reform_entries(k, _dupemap[k], _totals[k])
            _dupemap.pop(k, None)
            _dupemap.update(_newentries)



        '''
        3.  Map remaining exact duplicate groupings, which all now have v = 1 due to reforming above
        '''

        _tomap = {k:v for k,v in _dupemap.items()}

        for k,v in _tomap.items():

            ''' Remove from map of duplicates '''
            _dupemap.pop(k)

            _newones = self.map_multi_grouping(k, v)
            _mapped.update(_newones)



        ''' Put together all unmapped items '''
        _u1 = [el for el in a1.nodes if el not in _mapped]
        _u2 = [el for el in a2.nodes if el not in _mapped.values()]



        '''
        4.  Now need to continue mapping all nodes without exact label matches
        '''

        ''' Get total similarity (i.e. sum of all measures), currently element [0] '''
        if _u1 and _u2:
            _sim_u = self.node_sim(a1, a2, _u1, _u2, weight = [1,0,1,0,0])[0]

            ''' First job, as in previous sections: get any easy mappings where
                max sim value appears once, and remove from dict '''
            _newmap = self.get_by_max(_sim_u)
            if _newmap:
                _mapped.update(_newmap)

                for node1 in _newmap:
                    _u1.remove(node1)
                for node2 in _newmap.values():
                    _u2.remove(node2)

                _dupenew, _simnew = self.remap_entries(_u1, _u2, _newmap, _sim_u)
                _dupemap.update(_dupenew)

                # ''' Next stage is to get sim groupings
                #     i.e. where max sim value appears more than once '''
                # _newentries = self.reform_entries(tuple(_u1), tuple(_u2), _simnew)
                # print('New sim map by reforming: ', _newentries)



        # return _mapped, (_u1, _u2), _sim, _dupemap, _totals, _tomap, _simnew
        return _mapped, (_u1, _u2)



    def node_sim(self, a1, a2, nodes1 = None, nodes2 = None, weight = [1,0,1,0,0], C1 = 0, C2 = 0, field = 'occ_name'):
        ''' Weights apply to similarity of following metrics (by index):
            0. Depth of nodes in tree (i.e. from root)
            1. Number of siblings
            2. Number of children
            3. Name of parent '''

        print('Running "node_sim"')

        if not nodes1:
            nodes1 = a1.nodes
        if not nodes2:
            nodes2 = a2.nodes

        # if type(nodes1) is not list:
        #     nodes1 = [nodes1]
        # if type(nodes2) is not list:
        #     nodes2 = [nodes2]

        _r1 = a1.get_root()
        _r2 = a2.get_root()

        _sim_label = {}
        _sim_depth = {}
        _sim_sibs = {}
        _sim_children = {}
        _sim_parent = {}
        _sim = {}

        for n1 in nodes1:
            _sim_label[n1] = {}
            _sim_depth[n1] = {}
            _sim_sibs[n1] = {}
            _sim_children[n1] = {}
            _sim_parent[n1] = {}
            _sim[n1] = {}

            for n2 in nodes2:

                ''' Get node label similarity '''
                # print('n1, n2, field:')
                # print(n1, n2, field)

                _sim_label[n1][n2] = self.similarity(a1.nodes[n1][field], a2.nodes[n2][field])[1]



                ''' Get tree-depth similarity '''
                _d1 = nx.shortest_path_length(a1, _r1, n1)
                _d2 = nx.shortest_path_length(a2, _r2, n2)
                if (_d1 == 0) and (_d2 == 0):
                    c = C1
                elif (_d1 == 0) != (_d2 == 0):
                    c = C2
                else:
                    c = min(_d1, _d2)/max(_d1, _d2)
                _sim_depth[n1][n2] = c



                ''' Get parents, where None is default if no parent... '''
                _p1 = next(a1.predecessors(n1), None)
                _p2 = next(a2.predecessors(n2), None)
                ''' ...then get parent label similarity, if both parents exist '''
                if (_p1 == None) and (_p2 == None):
                    c = C1
                elif (_p1 == None) != (_p2 == None):
                    c = C2
                else:
                    c = self.similarity(a1.nodes[_p1][field], a2.nodes[_p2][field])[1]
                _sim_parent[n1][n2] = c



                ''' Get number of siblings... '''
                try:
                    _ns1 = len([el for el in a1.successors(_p1)]) - 1
                    _ns2 = len([el for el in a2.successors(_p2)]) - 1
                except:
                    _ns1 = 0
                    _ns2 = 0
                ''' ...then get similarity '''
                if (_ns1 == 0) and (_ns2 == 0):
                    c = C1
                elif (_ns1 == 0) != (_ns2 == 0):
                    c = C2
                else:
                    c = min(_ns1, _ns2)/max(_ns1, _ns2)
                _sim_sibs[n1][n2] = c



                ''' Get number of children... '''
                _nc1 = len([el for el in a1.successors(n1)])
                _nc2 = len([el for el in a2.successors(n2)])
                ''' ...then get similarity '''
                if (_nc1 == 0) and (_nc2 == 0):
                    c = C1
                elif (_nc1 == 0) != (_nc2 == 0):
                    c = C2
                else:
                    c = min(_nc1, _nc2)/max(_nc1, _nc2)
                _sim_children[n1][n2] = c


                _norm = sum(weight)
                ''' Get total (aggregate) similarity '''
                _sim[n1][n2] = (_sim_label[n1][n2]*weight[0] \
                        + _sim_depth[n1][n2]*weight[1] \
                        + _sim_parent[n1][n2]*weight[2] \
                        + _sim_sibs[n1][n2]*weight[3] \
                        + _sim_children[n1][n2]*weight[4])/_norm

        return _sim, _sim_label, _sim_depth, _sim_parent, _sim_sibs, _sim_children



    ''' Get all mappings by exact matching of field '''
    def map_exact(self, a1, a2, nodes1 = None, nodes2 = None, _field = 'occ_name'):
        print('Running "map_exact"')

        if (not nodes1) and (not nodes2):
            nodes1 = a1.nodes
            nodes2 = a2.nodes
        elif (not nodes1) != (not nodes2):
            return None

        _map = {}

        _values = set([a1.nodes[el][_field] for el in a1.nodes])
        _field_dict = {}

        for el in _values:
            _n1 = [_el for _el in a1.nodes if a1.nodes[_el][_field] == el]
            _n2 = [_el for _el in a2.nodes if a2.nodes[_el][_field] == el]
            if _n1 and _n2:
                if len(_n1) == 1 and len(_n2) == 1:
                    ''' If single-value mapping, then map... '''
                    if _n1[0] not in _map:
                        _map[_n1[0]] = _n2[0]
                else:
                    ''' ...else create dupe dict entry '''
                    _field_dict[tuple(_n1)] = tuple(_n2)

        return _field_dict, _map



    ''' Get mappings by max value
        If "singles_only" is true, only map for single-occurrence max sim values
        Else map anyway, which means first node2 found with max sim value is mapped '''
    def get_by_max(self, _sim, singles_only = True):
        print('Running "get_by_max"')

        _map = {}

        nodes1 = _sim.keys()

        ''' Loop over node1 items, which are contained in key of "_sim" '''
        for node1 in nodes1:
            _simdict = _sim[node1]
            ''' Remove already-mapped entries '''
            for _done2 in _map.values():
                _simdict.pop(_done2, None)
            ''' Short-circuit if _simdict empty
                This will happen when fewer n1 than n2 '''
            if not _simdict:
                return _map

            _max = max([el for el in _simdict.values()])
            _occ = sum(value == _max for value in _simdict.values())

            ''' Get valid (i.e. not already mapped) k-v pairs in simdict '''
            if (singles_only and _occ == 1) or not singles_only:
                node2 = [_k for _k,_v in _simdict.items() if _v == _max][0]
                _map[node1] = node2

        return _map



    def remap_entries(self, k, v, _dupe, _sim):
        print('Running "remap_entries"')

        ''' Start building new dupe map elements... '''
        _toremove1 = [el for el in _dupe]
        _toremove2 = [el for el in _dupe.values()]

        _n1 = tuple([el for el in k if el not in _toremove1])
        _n2 = tuple([el for el in v if el not in _toremove2])

        ''' ...and new total sim dict entry '''
        _newv = {_k:_v for _k,_v in _sim.items() if _k in _n1}
        _klist = list(_newv)
        for el in _klist:
            for _el in _toremove2:
                if _el in _newv[el]:
                    _newv[el].pop(_el, None)

        _dupenew = {}
        _simnew = {}
        ''' Check that n1 and n2 both have items in, otherwise would be redundant... '''
        if (len(_n1) > 0) and (len(_n2) > 0):
            ''' ...then actually create entries... '''
            _dupenew[_n1] = _n2
            _simnew[_n1] = _newv

        return _dupenew, _simnew



    ''' HR 24/11/20
        reform_entries not working as intended when tested with torch assembly
        and HHC's alternative assembly with four bulbs
        Problem is matching nodes within multiplicity groupings '''
    def reform_entries(self, nodes1, nodes2, _sim):
        print('Running "reform_entries"')

        nodes1 = list(nodes1)
        nodes2 = list(nodes2)

        ''' HR 26/11/20 Workaround to avoid problems for node sets with differing sizes
            Larger problems with this method remain, as described above '''
        if len(nodes1) != len(nodes2):
            return {tuple(nodes1):tuple(nodes2)}

        _first = nodes1[0]
        _firstdict = _sim[_first]
        _firstvalueset = set(_firstdict.values())

        if len(_firstvalueset) == 1:
            return {tuple(nodes1):tuple(nodes2)}

        _sims = list(_firstdict.values())

        _newentries = {}

        for el in _firstvalueset:

            _i = [i for i,val in enumerate(_sims) if val == el]
            _n1 = [nodes1[i] for i in _i]
            _n2 = [nodes2[i] for i in _i]

            ''' Reform grouping; no need to rebuild totals dict as not used after this '''
            _newentries[tuple(_n1)] = tuple(_n2)

        return _newentries



    ''' Map same-sim-value grouping
        (a) by same node IDs or
        (b) in numerical order '''
    def map_multi_grouping(self, k, v):
        print('Running "map_multi_grouping"')

        _toremove = []
        _newmap = {}

        _klist = sorted([el for el in k])
        _vlist = sorted([el for el in v])

        ''' First match any with the same IDs... '''
        for el in _klist:
            if el in _vlist:
                _newmap[el] = el
                _toremove.append(el)

        for el in _toremove:
            _klist.remove(el)
            _vlist.remove(el)

        ''' ...then match the remainder in numerical order
            N.B. "zip" truncates to length of smaller list '''
        if _klist and _vlist:
            _remainder = dict(zip(_klist, _vlist))
            for _k,_v in _remainder.items():
                _newmap[_k] = _v

        return _newmap



    ''' ----------------------------------------------------------------------
        ALL GRAPH/LATTICE PLOT METHODS HERE
        ----------------------------------------------------------------------
    '''



    ''' Create all plot objects from scratch '''
    def create_plot_elements(self):

        latt = self._lattice
        pos = latt.get_positions()

        # dc = self.dc
        # sc = self.sc
        lc = self.lc
        ic = self.ic

        ''' Bodge to set nodes/edges to one colour
            then recolour later (as most will not be selected, so quick) '''
        c = ic

        latt.line_dict = {}
        latt.node_dict = {}
        latt.edge_dict = {}

        ''' Draw outline of each (populated) level, with end points '''
        ''' HR 28/10/21 To add option to realise all lines, not just populated ones '''
        if self.DO_ALL_LATTICE_LINES:
            lines = latt.S_p_all
        else:
            lines = latt.S_p

        for k,v in lines.items():
            if v <= 1:
                line_pos = 0
            else:
                line_pos = np.log(v-1)
            latt.line_dict[k] = self.axes.plot([-0.5*line_pos, 0.5*line_pos], [k, k], c = lc, marker = 'o', mfc = lc, mec = lc, zorder = -1)

        ''' Draw nodes '''
        for node in latt.nodes:
            latt.node_dict[node] = self.axes.scatter(pos[node][0], pos[node][1], c = c, zorder = 1)

        ''' Draw edges '''
        for u,v in latt.edges:
            latt.edge_dict[(u,v)] = self.axes.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], c = c, zorder = 0)[0] # [0] index to get single list item

        ''' Create edges b/t infimum and leaves '''
        origin = latt.origin
        ''' Here set v in edge (u,v) to None if v is infimum '''
        for leaf in latt.leaves:
            latt.edge_dict[(leaf,None)] = self.axes.plot([origin[0], pos[leaf][0]], [origin[1], pos[leaf][1]], c = c, zorder = 0)[0] # [0] index to get single list item



        ''' Minimise white space around plot in panel '''
        self.viewer.subplots_adjust(left = 0.01, bottom = 0.01, right = 0.99, top = 0.99)

        self.axes.axes.axis('off')
        self.axes.axes.get_xaxis().set_ticks([])
        self.axes.axes.get_yaxis().set_ticks([])



    def update_colours_selected(self, active, selected = [], to_select = [], to_unselect = []):

        selected = [self.get_master_node(active, node) for node in selected]
        to_select = [self.get_master_node(active, node) for node in to_select]
        to_unselect = [self.get_master_node(active, node) for node in to_unselect]

        print('selected: ', selected)
        print('to_select: ', to_select)
        print('to_unselect: ', to_unselect)

        dc = self.dc
        sc = self.sc

        latt = self._lattice
        leaves = latt.leaves

        ''' Selections '''
        for node in to_select:
            ''' Nodes '''
            latt.node_dict[node].set_facecolor(sc)
            ''' Edges '''
            for u,v in latt.in_edges(node):
                if (u in selected) or (u in to_select):
                    latt.edge_dict[(u,v)].set_color(sc)
            for u,v in latt.out_edges(node):
                if (v in selected) or (v in to_select):
                    latt.edge_dict[(u,v)].set_color(sc)

        ''' Deselections '''
        for node in to_unselect:
            ''' Nodes '''
            latt.node_dict[node].set_facecolor(dc)
            ''' Edges '''
            for u,v in latt.in_edges(node):
                if u in selected:
                    latt.edge_dict[(u,v)].set_color(dc)
            for u,v in latt.out_edges(node):
                if v in selected:
                    latt.edge_dict[(u,v)].set_color(dc)

        ''' Edges from leaves to infimum '''
        to_select_leaves = [el for el in to_select if el in leaves]
        to_unselect_leaves = [el for el in to_unselect if el in leaves]
        ''' Selections '''
        for leaf in to_select_leaves:
            latt.edge_dict[(leaf,None)].set_color(sc)
        ''' Deselections '''
        for leaf in to_unselect_leaves:
            latt.edge_dict[(leaf,None)].set_color(dc)



        ''' Minimise white space around plot in panel '''
        self.viewer.subplots_adjust(left = 0.01, bottom = 0.01, right = 0.99, top = 0.99)

        self.axes.axes.axis('off')
        self.axes.axes.get_xaxis().set_ticks([])
        self.axes.axes.get_yaxis().set_ticks([])



    def update_colours_active(self, to_activate = [], to_deactivate = []):

        latt = self._lattice
        nodes = latt.nodes
        edges = latt.edges
        leaves = latt.leaves

        ic = self.ic
        dc = self.dc

        ''' Nodes '''
        for node in nodes:
            _dict = nodes[node]
            # ''' Activate '''
            if any(el in to_activate for el in _dict):
                latt.node_dict[node].set_facecolor(dc)
            # ''' Deactivate '''
            elif any(el in to_deactivate for el in _dict):
                latt.node_dict[node].set_facecolor(ic)

        ''' Edges '''
        for edge in edges:
            _dict = edges[edge]
            # ''' Activate '''
            if any(el in to_activate for el in _dict):
                latt.edge_dict[edge].set_color(dc)
            # ''' Deactivate '''
            elif any(el in to_deactivate for el in _dict):
                latt.edge_dict[edge].set_color(ic)

        ''' Edges from leaves to infimum '''
        for leaf in leaves:
            _dict = nodes[node]
            if any(el in to_activate for el in _dict):
                latt.edge_dict[(leaf,None)].set_color(dc)
            elif any(el in to_deactivate for el in _dict):
                latt.edge_dict[(leaf,None)].set_color(ic)



        ''' Minimise white space around plot in panel '''
        self.viewer.subplots_adjust(left = 0.01, bottom = 0.01, right = 0.99, top = 0.99)

        self.axes.axes.axis('off')
        self.axes.axes.get_xaxis().set_ticks([])
        self.axes.axes.get_yaxis().set_ticks([])




    ''' ----------------------------------------------------------------------
        ALL PROJECT/LATTICE DATA EXCHANGE HERE
        ----------------------------------------------------------------------
    '''



    ''' HR June 21 Method removed from StrEmbed
        Dumps all basic project/lattice, assembly and node info:
            Node ID, label/text, parent
        Keep for now, can reuse for larger "save" functionality later '''
    # ''' HR 25/02/21
    #     Basic XLSX output for whole lattice (i.e. all assemblies) '''
    # def xlsx_write(self, _ids = None):

    #     def get_header(_id, page):
    #         mgr = self._assembly_manager._mgr
    #         header = []
    #         header.append(mgr[_id].assembly_id)
    #         header.append(page.name)
    #         header.append(page.filename_fullpath)
    #         return header

    #     def get_output_data(_id, node):
    #         ass = self._assembly_manager._mgr[_id]
    #         data = []
    #         data.append(node)
    #         try:
    #             data.append(ass.nodes[node]['label'])
    #         except:
    #             data.append('')
    #         try:
    #             data.append(ass.nodes[node]['text'])
    #         except:
    #             data.append('')
    #         try:
    #             data.append(ass.get_parent(node))
    #         except:
    #             data.append('None (root)')
    #         return data

    #     header_fields = ['Assembly ID', 'Assembly name', 'STP/STEP file']
    #     y_offset = len(header_fields) + 2

    #     fields = ['Node ID', 'Label', 'Text', 'Parent ID', ]

    #     save_file = 'torch_project.xlsx'

    #     excel_file = os.getcwd() + '\\' + save_file
    #     workbook = xlsxwriter.Workbook(excel_file)

    #     '''Export all assemblies if none specified '''
    #     if not _ids:
    #         _ids = [el for el in self._assembly_manager._mgr]

    #     ''' Create worksheet for each assembly to be exported '''
    #     sheet_dict = {}
    #     for _id in _ids:
    #         sheet_dict[_id] = workbook.add_worksheet()
    #         page = [k for k,v in self._notebook_manager.items() if v == _id][0]

    #         ''' Write main header... '''
    #         header_data = get_header(_id, page)
    #         for i,el in enumerate(header_fields):
    #             sheet_dict[_id].write(i, 0, el)
    #             sheet_dict[_id].write(i, 1, header_data[i])

    #         ''' ...and node fields header '''
    #         for i,el in enumerate(fields):
    #             sheet_dict[_id].write(y_offset-1,i,el)

    #         ''' Get all nodes still present in CTC '''
    #         nodes = list(page.ctc_dict)

    #         counter = 0
    #         for node in nodes:
    #             data = get_output_data(_id, node)
    #             for i,el in enumerate(data):
    #                 x = i
    #                 y = counter + y_offset
    #                 sheet_dict[_id].write(y, x, data[i])
    #             counter += 1

    #     workbook.close()




class StepParse(nx.DiGraph):

    def __init__(self, assembly_id = None, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.part_level = 1

        ''' Below is full range of shape types, according to Open Cascade documentation here:
            https://dev.opencascade.org/doc/refman/html/class_topo_d_s___shape.html '''
        self.topo_types = (TopoDS_Shape, TopoDS_Solid, TopoDS_Compound, TopoDS_Shell, TopoDS_Face, TopoDS_Vertex, TopoDS_Edge, TopoDS_Wire, TopoDS_CompSolid)
        # self.topo_types = (TopoDS_Solid, TopoDS_Compound)
        # self.topo_types = (TopoDS_Solid, TopoDS_Compound, TopoDS_Shell, TopoDS_Face)
        # self.topo_types = (TopoDS_Solid,)

        self.assembly_id = assembly_id
        # self.OCC_dict = {}

        self.default_label_part = 'Unnamed item'
        self.default_label_ass = 'Unnamed item'
        self.head_name = '== PROJECT =='

        ''' Mid-grey for default shape colour '''
        self.SHAPE_COLOUR_DEFAULT = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)

        self.enforce_unary = True

        self.renderer = ShapeRenderer()
        self.PARTFIND_FOLDER_DEFAULT = "C:\_Work\_DCS project\__ALL CODE\_Repos\partfind\partfind for git"

        self.node_dict = {}

    @property
    def new_node_id(self):
        if not hasattr(self, 'id_counter'):
            self.id_counter = 0
        self.id_counter += 1
        while self.id_counter in self.nodes:
            self.id_counter += 1
        return self.id_counter



    ''' Overridden to add label to node upon creation '''
    def add_node(self, node, **attr):
        super().add_node(node, **attr)

        kwds = ['text', 'label']

        for kwd in kwds:
            if kwd in attr:
                value = self.nodes[node][kwd]
                if (value is not None):
                    try:
                        self.nodes[node][kwd] = self.remove_suffixes(value)
                    except:
                        pass
            else:
                self.nodes[node][kwd] = self.default_label_part



    # def print_all_items(self):
    #     print('\nAll nodes and edges:')
    #     for node in self.nodes:
    #         print(node, self.nodes[node])
    #     for edge in self.edges:
    #         print(edge, self.edges[edge])



    ''' Set node and edge labels to node identifier
        For use later in tree reconciliation '''
    def set_all_tags(self):
        for node in self.nodes:
            if not 'tag' in self.nodes[node]:
                self.nodes[node]['tag'] = node
        for edge in self.edges:
            if not 'tag' in self.edges[edge]:
                self.edges[edge]['tag'] = edge



    def get_screen_name(self, occ_name, shape):

        if not hasattr(self, 'name_root_counter'):
            self.name_root_counter = {}
        if not hasattr(self, 'type_counter'):
            self.type_counter = {}

        ''' HR 13/05/21
            If item is product -> name root = product name,
            which assumes all products have a name,
            otherwise root name is based on shape type;
            lastly, call it "item" '''
        if occ_name in self.product_names:
            nm_root = occ_name

        elif shape:
            # ''' Lower case, naive implementation '''
            # nm_root = str(type(shape).__name__).rsplit('_', 1)[1]
            ''' Upper case to match pythonocc behaviour
                e.g. TopoDS_Solid -> SOLID, SOLID_1, SOLID_2, etc. '''
            if not type(shape) in self.type_counter:
                self.type_counter[type(shape)] = 0
                nm_root = str(type(shape).__name__).rsplit('_', 1)[1].upper()
            else:
                nm_root = str(type(shape).__name__).rsplit('_', 1)[1].upper() + '_' + str(self.type_counter[type(shape)])
            self.type_counter[type(shape)] += 1

        else:
            nm_root = 'Item'

        if not nm_root in self.name_root_counter:
            self.name_root_counter[nm_root] = 0
            nm_full = nm_root
        else:
            nm_full = nm_root + '_' + str(self.name_root_counter[nm_root])

        self.name_root_counter[nm_root] += 1

        return nm_full



    @property
    def product_names(self):

        ''' HR 01/11/21 To fix STEP product name parsing problems '''
        def get_product_name(line):
            ''' First strip off basic extraneous stuff; this should work universally '''
            line_corr = line.split("PRODUCT")[1].strip().rstrip(";").lstrip("(").strip().split("#")[0].strip().rstrip("(").strip().strip(",").strip()
            ''' Next, deal with remaining rightmost field
                Fine for all case studies so far, but might not be universal solution; would need to deal with text in field, if present
                Note: Currently yields wrong name if text present in rightmost field '''
            line_corr = line_corr.rstrip("'").strip().rstrip("'").strip().rstrip(",")
            # print('Stripped back text: ', line_corr)

            chunks = line_corr.split(",")
            # print('Chunks by comma: ', chunks)

            l = len(chunks)
            # print('Length: ', l)

            if l == 2:
                ''' If only two chunks, first chunk must be name, even if two empty chunks '''
                name = chunks[0]
                # print("Length = 2, name is first chunk: ", name)

            else:
                if (l % 2) != 0:
                    ''' If l > 2 and odd, last chunk must be empty => name is all chunks except last '''
                    name = ''.join(chunks[:-1])
                    print("Length = ", l, " and odd, name is all chunks except last: ", name)
                else:
                    ''' Last remaining case is that l > 2 and even, for which two possible outcomes '''
                    lh = int(l/2)
                    print('Half length = ', lh)
                    ''' Chop text into two halves '''
                    half1 = ','.join(chunks[0:lh]).strip()
                    half2 = ','.join(chunks[lh:]).strip()
                    # print('Half 1: ', half1)
                    # print('Half 2: ', half2)
                    if half1 == half2:
                        ''' Outcome 1: Both halves the same, i.e. name repeated in two fields '''
                        name = half1
                        # print("Length > 2 and even and halves match, name is first half: ", name)
                    else:
                        ''' Outcome 2: Second field empty => name is all chunks except last '''
                        name = ','.join(chunks[:-1])
                        # print("Length > 2 and even and halves do NOT match, name is all chunks except last: ", name)

            ''' HR 01/11/21 Workaround for problem of multiple apostropges being reduced to single one in OCC
                Address unresolved OCC bug 32421: https://tracker.dev.opencascade.org/view.php?id=32421
                Possibly fixed via 32310: https://tracker.dev.opencascade.org/view.php?id=32310 
                but needs testing here after updating PythonOCC '''
            while "''" in name:
                name = name.replace("''", "'")

            ''' Remove double quotes if present; may be more elegant method for doing this '''
            name = name[1:-1]

            # return line_corr, name
            return name



        ''' HR May 21 To get all product names from STEP files
            This all assumes products have non-empty names,
            otherwise logic would have to be completely revised
            and would need to delve into OCC much further '''
        if not hasattr(self, '_product_names'):
            lines = step_search(file = self.step_filename, keywords = ['PRODUCT ', 'PRODUCT('], exclusions = ['kevinphillipsbong'])[0]
            ''' HR 03/06/21 Product name parsing corrected '''
            # self._product_names = [line.split(",")[0].split("(")[1].lstrip().rstrip().lstrip("'").rstrip("'").lstrip().rstrip() for line in lines]
            # self._product_names = [line.split("PRODUCT")[1].split(",")[0].rstrip().lstrip().lstrip("(").lstrip().lstrip("'").strip("'") for line in lines]



            self._product_names = []
            for line in lines:
                self._product_names.append(get_product_name(line))

        return self._product_names



    def load_step(self, filename, get_subshapes = False):
        ''' HR 11/05/21 Adapted from "read_step_file_with_names_colors"
            in OCC.Extend.DataExchange here:
            https://github.com/tpaviot/pythonocc-core/blob/master/src/Extend/DataExchange.py '''
        ##Copyright 2018 Thomas Paviot (tpaviot@gmail.com)
        ##
        ##This file is part of pythonOCC.
        ##
        ##pythonOCC is free software: you can redistribute it and/or modify
        ##it under the terms of the GNU Lesser General Public License as published by
        ##the Free Software Foundation, either version 3 of the License, or
        ##(at your option) any later version.
        ##
        ##pythonOCC is distributed in the hope that it will be useful,
        ##but WITHOUT ANY WARRANTY; without even the implied warranty of
        ##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
        ##GNU Lesser General Public License for more details.
        ##
        ##You should have received a copy of the GNU Lesser General Public License
        ##along with pythonOCC.  If not, see <http://www.gnu.org/licenses/>.
        """ Returns list of tuples (topods_shape, label, color)
        Use OCAF.
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError("%s not found." % filename)

        self.step_filename = filename

        doc = TDocStd_Document(TCollection_ExtendedString("pythonocc-doc"))

        shape_tool = XCAFDoc_DocumentTool_ShapeTool(doc.Main())
        color_tool = XCAFDoc_DocumentTool_ColorTool(doc.Main())
        #layer_tool = XCAFDoc_DocumentTool_LayerTool(doc.Main())
        #mat_tool = XCAFDoc_DocumentTool_MaterialTool(doc.Main())

        step_reader = STEPCAFControl_Reader()
        step_reader.SetColorMode(True)
        step_reader.SetLayerMode(True)
        step_reader.SetNameMode(True)
        step_reader.SetMatMode(True)
        step_reader.SetGDTMode(True)

        status = step_reader.ReadFile(filename)
        if status == IFSelect_RetDone:
            step_reader.Transfer(doc)

        ''' loc tracks spatial transformation through each level of assembly structure
            i.e. for each IsAssembly level, but not for sub-shapes '''
        locs = []



        ''' Create graph structure for shape data '''
        head = self.new_node_id
        self.add_node(head)
        self.nodes[head]['occ_label'] = None
        self.nodes[head]['occ_name'] = None
        self.nodes[head]['screen_name'] = self.head_name
        self.nodes[head]['shape_raw'] = (None, None)
        self.nodes[head]['shape_loc'] = (None, None)
        self.nodes[head]['is_subshape'] = False
        self.nodes[head]['is_product'] = False



        def _get_sub_shapes(lab, loc):
            #global cnt, lvl
            #cnt += 1
            #print("\n[%d] level %d, handling LABEL %s\n" % (cnt, lvl, _get_label_name(lab)))
            #print()
            #print(lab.DumpToString())
            #print()
            #print("Is Assembly    :", shape_tool.IsAssembly(lab))
            #print("Is Free        :", shape_tool.IsFree(lab))
            #print("Is Shape       :", shape_tool.IsShape(lab))
            #print("Is Compound    :", shape_tool.IsCompound(lab))
            #print("Is Component   :", shape_tool.IsComponent(lab))
            #print("Is SimpleShape :", shape_tool.IsSimpleShape(lab))
            #print("Is Reference   :", shape_tool.IsReference(lab))

            #users = TDF_LabelSequence()
            #users_cnt = shape_tool.GetUsers(lab, users)
            #print("Nr Users       :", users_cnt)

            name = lab.GetLabelName()
            # print("Name :", name)



            ''' Properties common to assemblies and shapes
                Assembly- and shape-specific properties added in if/else below '''
            node = self.new_node_id
            self.add_edge(self.parent, node)
            self.nodes[node]['occ_label'] = lab
            self.nodes[node]['occ_name'] = name
            self.nodes[node]['is_subshape'] = False
            if name in self.product_names:
                is_product = True
            else:
                is_product = False
            self.nodes[node]['is_product'] = is_product



            if shape_tool.IsAssembly(lab):

                ''' Get components -> l_c '''
                l_c = TDF_LabelSequence()
                shape_tool.GetComponents(lab, l_c)
                #print("Nb components  :", l_c.Length())
                #print()

                ''' Assembly-specific (i.e. non-shape) properties '''
                self.nodes[node]['screen_name'] = self.get_screen_name(name, None)
                self.nodes[node]['shape_raw'] = (None, None)
                self.nodes[node]['shape_loc'] = (None, None)


                for i in range(l_c.Length()):
                    label = l_c.Value(i+1)
                    if shape_tool.IsReference(label):
                        #print("\n########  reference label :", label)
                        label_reference = TDF_Label()
                        shape_tool.GetReferredShape(label, label_reference)
                        loc = shape_tool.GetLocation(label)

                        self.parent = node

                        ''' Append location for this level '''
                        locs.append(loc)
                        #print(">>>>")
                        #lvl += 1
                        _get_sub_shapes(label_reference, loc)
                        #lvl -= 1
                        #print("<<<<")
                        locs.pop()



            elif shape_tool.IsSimpleShape(lab):

                ''' Get sub-shapes-> l_subss '''
                l_subss = TDF_LabelSequence()
                shape_tool.GetSubShapes(lab, l_subss)
                #print("Nb subshapes   :", l_subss.Length())

                #print("\n########  simpleshape label :", lab)
                shape = shape_tool.GetShape(lab)
                #print("    all ass locs   :", locs)

                ''' Create location by applying all locations to that level in sequence
                    as they are applied in sequence '''
                loc = TopLoc_Location()
                for l in locs:
                    #print("    take loc       :", l)
                    loc = loc.Multiplied(l)

                ''' HR June 21 some code duplication for colour assignment
                    but didn't work when reduced to single block '''
                c = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)  # default color
                colorSet = False
                if (color_tool.GetInstanceColor(shape, 0, c) or
                        color_tool.GetInstanceColor(shape, 1, c) or
                        color_tool.GetInstanceColor(shape, 2, c)):
                    color_tool.SetInstanceColor(shape, 0, c)
                    color_tool.SetInstanceColor(shape, 1, c)
                    color_tool.SetInstanceColor(shape, 2, c)
                    colorSet = True
                    n = c.Name(c.Red(), c.Green(), c.Blue())
                    # print('    instance color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                if not colorSet:
                    if (color_tool.GetColor(lab, 0, c) or
                            color_tool.GetColor(lab, 1, c) or
                            color_tool.GetColor(lab, 2, c)):
                        color_tool.SetInstanceColor(shape, 0, c)
                        color_tool.SetInstanceColor(shape, 1, c)
                        color_tool.SetInstanceColor(shape, 2, c)

                        n = c.Name(c.Red(), c.Green(), c.Blue())
                        # print('    shape color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())



                ''' Shape-specific (i.e. non-assembly) properties '''
                self.nodes[node]['screen_name'] = self.get_screen_name(name, shape)
                self.nodes[node]['shape_raw'] = (shape, loc)
                self.nodes[node]['shape_loc'] = (BRepBuilderAPI_Transform(shape, loc.Transformation()).Shape(), c)
                self.parent = node



                # ''' Location (loc) is applied in sequence '''
                # shape_disp = BRepBuilderAPI_Transform(shape, loc.Transformation()).Shape()

                # if not shape_disp in output_shapes:
                #     output_shapes[shape_disp] = [lab.GetLabelName(), c]



                ''' Return if sub-shapes are not required '''
                if not get_subshapes:
                    return



                for i in range(l_subss.Length()):
                    lab_subs = l_subss.Value(i+1)
                    shape_sub = shape_tool.GetShape(lab_subs)
                    # print("\n########  simpleshape subshape label, type :", lab_subs.GetLabelName(), type(shape_sub))

                    c = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)  # default color
                    colorSet = False
                    if (color_tool.GetInstanceColor(shape_sub, 0, c) or
                            color_tool.GetInstanceColor(shape_sub, 1, c) or
                            color_tool.GetInstanceColor(shape_sub, 2, c)):
                        color_tool.SetInstanceColor(shape_sub, 0, c)
                        color_tool.SetInstanceColor(shape_sub, 1, c)
                        color_tool.SetInstanceColor(shape_sub, 2, c)
                        colorSet = True
                        # n = c.Name(c.Red(), c.Green(), c.Blue())
                        # print('    instance color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                    if not colorSet:
                        if (color_tool.GetColor(lab_subs, 0, c) or
                                color_tool.GetColor(lab_subs, 1, c) or
                                color_tool.GetColor(lab_subs, 2, c)):
                            color_tool.SetInstanceColor(shape_sub, 0, c)
                            color_tool.SetInstanceColor(shape_sub, 1, c)
                            color_tool.SetInstanceColor(shape_sub, 2, c)

                            # n = c.Name(c.Red(), c.Green(), c.Blue())
                            # print('    shape color Name & RGB: ', c, n, c.Red(), c.Green(), c.Blue())

                    # ''' Location (loc) is common to all sub-shapes '''
                    # shape_to_disp = BRepBuilderAPI_Transform(shape_sub, loc.Transformation()).Shape()

                    # if not shape_to_disp in output_shapes:
                    #     output_shapes[shape_to_disp] = [lab_subs.GetLabelName(), c]



                    ''' Sub-shape-specific (i.e. non-shape, non-assembly) properties '''
                    name_sub = lab_subs.GetLabelName()

                    node = self.new_node_id
                    self.add_edge(self.parent, node)
                    self.nodes[node]['occ_label'] = lab_subs
                    self.nodes[node]['occ_name'] = name_sub
                    self.nodes[node]['shape_raw'] = (shape_sub, loc)
                    self.nodes[node]['shape_loc'] = (BRepBuilderAPI_Transform(shape_sub, loc.Transformation()).Shape(), c)
                    self.nodes[node]['screen_name'] = self.get_screen_name(name_sub, shape_sub)
                    self.nodes[node]['is_subshape'] = True
                    self.nodes[node]['is_product'] = False




        def _get_shapes():
            labels = TDF_LabelSequence()
            ''' Free shapes are those not referred to by any other
                1. If assembly structure present, this gets root item
                2. If not, all items in flat structure
                https://dev.opencascade.org/doc/refman/html/class_x_c_a_f_doc___shape_tool.html '''
            shape_tool.GetFreeShapes(labels)
            #global cnt
            #cnt += 1
            print("Number of shapes at root :", labels.Length())

            for i in range(labels.Length()):

                root_item = labels.Value(i+1)

                self.parent = head
                _get_sub_shapes(root_item, None)

        _get_shapes()
        # return output_shapes

        self.remove_redundants()



    def get_image_data(self, node, default_colour = False):

        def render(nodes):

            try:
                self.renderer.EraseAll()

                for node in nodes:

                    if not default_colour:
                        ''' Render in correct colour... '''
                        shape, c = self.nodes[node]['shape_loc']
                        self.renderer.DisplayShape(shape, color = Quantity_Color(c.Red(),
                                                                                 c.Green(),
                                                                                 c.Blue(),
                                                                                 Quantity_TOC_RGB))
                    else:
                        ''' ...or in default colour (for better reference images), i.e. orange '''
                        self.renderer.DisplayShape(shape)

                self.renderer.View.FitAll()
                self.renderer.View.ZFitAll()

                # img = <DO IMAGE DATA GRAB HERE>
                W,H = self.renderer.GetSize()
                img_data = (W, H, self.renderer.GetImageData(W, H, Graphic3d_BufferType.Graphic3d_BT_RGB))
                # img = wx.Image(W, H, img_data)
                # ''' Then with "from PIL import Image"
                # via https://github.com/tpaviot/pythonocc-core/issues/976 '''
                # img = Image.frombytes('RGB', (W, H), img_data)
                # img = img.rotate(180, expand=True)

            except Exception as e:
                print('Could not create image; exception follows')
                print(e)
                img_data = None

            return img_data



        ''' Grab node dict, shorthand '''
        d = self.nodes[node]

        ''' If already rendered (and stored in node dict), just return it '''
        if 'image_data' in d:
            if d['image_data']:
                img_data = d['image_data']
                print('Image data found in node dict')
                return img_data
        else:
            print('Image not found in node dict; rendering...')

        ''' If shape exists in node dict, render node
            else (b/c node is assembly) get all non-sub-shapes and render all '''
        _to_render = []
        if 'shape_loc' in d:
            if d['shape_loc'][0]:
                _to_render.append(node)
            else:
                for el in nx.descendants(self, node):
                    d_sub = self.nodes[el]
                    ''' Add to render list if shape present and not sub-shape '''
                    if 'shape_loc' in d_sub:
                        if d_sub['shape_loc'][0] and not d_sub['is_subshape']:
                            _to_render.append(el)

        ''' Get image; default to "no image" png if not successful '''
        if _to_render:
            img_data = render(_to_render)
            if img_data:
                print('Successfully rendered image')
        else:
            img_data = None

        return img_data



    ''' Remove all single-child sub-assemblies as not compatible with lattice '''
    def remove_redundants(self, _tree = None):

        ''' Operate on whole tree by default '''
        if not _tree:
            _tree = self.nodes

        ''' Get list of redundant nodes and link past them... '''
        _to_remove = []
        for _node in _tree:
            if self.out_degree(_node) == 1 and self.nodes[_node]['screen_name'] != self.head_name:
                _parent = self.get_parent(_node)
                _child  = self.get_child(_node)
                ''' Don't remove if at head of tree (i.e. if in_degree == 0)...
                    ...as Networkx would create new "None" node as parent '''
                if self.in_degree(_node) != 0:
                    self.add_edge(_parent, _child)
                _to_remove.append(_node)

        ''' ...then remove in separate loop to avoid list changing size during previous loop '''
        for _node in _to_remove:
            self.remove_node(_node)
            print('Removing node ', _node)
        print('  Total nodes removed: ', len(_to_remove))

        print('Removed redundants')



    ''' Finds root of graph containing reference node, which is passed for speed;
        otherwise start with first in node list (as any random one will do) '''
    def get_root(self, node = None):

        # root = [el for el in self.nodes if self.in_degree(el) == 0][0]
        ''' Get random node if none given '''
        if node is None:
            node = list(self.nodes)[0]

        parent = self.get_parent(node)
        if parent is None:
            return node

        while parent is not None:
            child = parent
            parent = self.get_parent(child)

        return child



    def get_parent(self, node):
        ''' Get parent of node; return None if parent not present '''
        parent = [el for el in self.predecessors(node)]
        if parent:
            return parent[-1]
        else:
            return None



    def get_child(self, node):
        ''' Get (single) child of node; return None if parent not present
            Best used only when removing redundant (i.e. single-child) subassemblies '''
        child = [el for el in self.successors(node)]
        if child:
            return child[-1]
        else:
            return None



    @property
    def leaves(self):
        ''' Get leaf nodes '''
        leaves = {el for el in self.nodes if self.out_degree(el) == 0}
        return leaves



    def node_depth(self, node):
        ''' Get depth of node(s) from root '''
        root = self.get_root(node)
        depth = nx.shortest_path_length(self, root, node)
        return depth



    def move_node(self, node, new_parent):
        old_parent = self.get_parent(node)
        self.remove_edge(old_parent, node)
        self.add_edge(new_parent, node)



    '''
    HR 15/01/21
    New method(s) to fetch "parts in" and node positions, rather than set them
    '''

    ''' Generate set of parts contained by node(s); node list optional argument '''
    def get_leaves_in(self, _nodes = None):

        ''' If no nodes passed, default to all nodes in assembly '''
        if not _nodes:
            _nodes = self.nodes

        ''' Convert to list if only one item '''
        if type(_nodes) == int:
            _nodes = [_nodes]

        ''' Get all leaves in specified nodes by set intersection '''
        leaves = set(_nodes) & self.leaves
        subassemblies = set(_nodes) - leaves

        leaves_in = {}

        for leaf in leaves:
            leaves_in[leaf] = {leaf}

        for sub in subassemblies:
            leaves_in[sub] = nx.descendants(self, sub) - subassemblies

        return leaves_in



    ''' Memoise combinations '''
    def get_comb(self, n, k):
        if not hasattr(self, 'nCk'):
            print('Creating nCk dict for memoisation...')
            self.nCk = {}
        if (n,k) not in self.nCk:
            self.nCk[(n,k)] = binom(n,k)
        return self.nCk[(n,k)]



    def get_positions(self, _nodes = None):

        ''' If no nodes passed, default to all nodes in assembly '''
        if not _nodes:
            _nodes = self.nodes

        ''' Convert to list if only one item '''
        if type(_nodes) == int:
            _nodes = [_nodes]

        ''' Get parts in each node '''
        parts_in = self.get_leaves_in(_nodes)

        self.pos = {}

        ''' Get all levels, i.e. number of parts by inclusion '''
        levels = set([len(parts) for node,parts in parts_in.items()])

        ''' Get number of possible combinations for each level... '''
        leaves = self.leaves
        n = len(leaves)
        ''' ...but only needed for specified nodes '''
        ''' HR 28/10/21 To add option to display all lines, not just populated ones '''
        self.S_p_all = {level:self.get_comb(n,level) for level in range(int(n+1))}
        self.S_p = {level:self.get_comb(n,level) for level in levels}

        ''' Create map of leaves to combinatorial numbering starting at 1... '''
        leaves_list = list(leaves)
        leaf_map = {}
        ''' ...but only need to map specified nodes; do by index in list of all nodes '''
        for leaf in leaves:
            leaf_map[leaf] = leaves_list.index(leaf) + 1

        self.levels_map = {}
        for node in _nodes:
            parts = parts_in[node]
            num_parts = len(parts)
            comb_parts = [leaf_map[part] for part in parts]
            rank = self.rank(comb_parts)
            S = self.S_p[num_parts]
            if num_parts in self.levels_map:
                self.levels_map[num_parts].append(node)
            else:
                self.levels_map[num_parts] = [node]
            if S <= 1:
                x = 0
            else:
                x = ((rank/(S-1))-0.5)*np.log(S-1)
            self.pos[node] = (x, num_parts)

        return self.pos

    ''' ----------
    '''




    '''
    HR 12/05/20
    -----------
    All combinatorial ranking/unranking methods here
    And all class methods '''



    def stirling_ln(self, n):
        # if n in (0, 1):
        #     _result = 0
        #     return _result

        _result = (n+0.5)*np.log(n) - n + np.log(np.sqrt(2*np.pi)) + (1/(12*n)) - (1/(360*n**3)) + (1/(1260*n**5)) - (1/(1680*n**7))
        # _result = (n+0.5)*np.log(n) - n + np.log(np.sqrt(2*np.pi)) + (1/(12*n))
        # print('Log Stirling approx. for n = ', n, ': ', _result)
        return _result



    def comb_ln(self, n, k):
        _result = self.stirling_ln(n) - self.stirling_ln(k) - self.stirling_ln(n-k)
        # print('Log combination approx. for (n, k) = ', (n,k), ': ', _result)
        return _result



    # RANKING OF COMBINATION
    # --
    # Find position (rank) of combination in ordered list of all combinations
    # Items list argument consists of zero-based indices
    # --
    def rank(self, items):

        if not items:
            print('Item list empty or not conditioned: returning None')
            return None

        if 0 in items:
            print('Item list contains 0 element: returning None')
            return None

        if not all(isinstance(item, int) for item in items):
            print('One or more non-integers present in item list: returning None')
            return None

        if len(items) != len(set(items)):
            print('Item list contains duplicate(s): returning None')
            return None

        # if len(items) == 1:
        #     items = [items]

        if len(items) > 1:
            items.sort()

        _rank = 0
        items.sort()
        for i, item in enumerate(items):
            _comb = self.get_comb(item-1, i+1)
            _rank += _comb

        return _rank



    '''
    UNRANKING OF COMBINATORIAL INDEX
    --
    Find combination of nCk items at position "rank" in ordered list of all combinations
    Ordering is zero-based
    '''
    def unrank(self, n, k, rank):

        ''' Check all arguments (except "self") are integers '''
        args_ = {k:v for k,v in locals().items() if k != 'self'}
        # print(['{} = {}'.format(k,v) for k,v in locals().items() if k != 'self'])
        print(['{} = {}'.format(k,v) for k,v in args_.items()])

        if not all(isinstance(el, (int, float)) for el in args_.values()):
        # if not all(isinstance(el, int) for el in (n, k, rank)):
            print('Not all arguments are integers: returning None')
            return None

        if rank < 0:
            print('Rank must be b/t 0 and (nCk-1); returning None')
            return None

        ''' Increase by one to satisfy zero-based indexing; check/resolve in future '''
        rank += 1

        ''' Check whether "rank" within nCk '''
        max_ln = self.comb_ln(n, k)

        ''' Check whether rank is massive; if so, calculate log(x) = log(x/a) + log(a)
            where x = rank and a = chop
            as np.log can't handle large numbers (actually x > 1e308 or so) '''
        chop = 1
        if rank > 1e100:
            print('Chopping rank for log')
            chop = 1000

        log_  = np.log(chop) + np.log(rank/chop)
        print('log_  = ', log_)

        if log_ > max_ln:
            print('Rank outside nCk bounds: returning None')
            return None

        ''' Convert to float to allow large n values '''
        rank = float(rank)



        ''' Optimisation as (n+1 k) = (n k)*(n+1)/(n+1-m) '''
        def next_comb(n_, k_, _comb):
            _next = (_comb*(n_+1))/(n_+1-k_)
            return _next

        ''' Using scipy comb; can optimise in future, e.g. with Stirling approx. '''
        def comb_(n_, k_):
            _result = self.get_comb(n_, k_)
            return _result



        '''
        MAIN ALGORITHM
        '''
        _items = []
        remainder = rank

        # print('Starting, k = {}'.format(k))
        ''' Find each of k items '''
        for i in range(k, 0, -1):

            ''' Initialise at 1 as kCk = 1 for all k '''
            c_i = 1
            count = i

            if c_i >= remainder:
                last_comb = c_i
            else:
                while c_i < remainder:
                    last_comb = c_i
                    c_i = next_comb(count, i, c_i)
                    count += 1

            # print('i   = {}'.format(i))
            # print('c_i = {}\n'.format(c_i))
            _items.append(count)
            remainder -= last_comb

        return _items



        ''' Alternative algorithm for unranking '''
        # '''
        # Algorithm 515 (Buckles_77, DOI: https://doi.org/10.1145/355732.355739)
        # For indexing combinations -> lexicographic ordering for ranking/unranking
        # Taken from Github repo of sleeepyjack here:
        # https://github.com/sleeepyjack/alg515/blob/master/python/alg515.py
        # '''

        # from scipy.special import binom

        # def comb(N, P, L):
        #     C = [0] * P
        #     X = 1
        #     R = int(binom(N-X, P-1))
        #     K = R

        #     while (K <= L):
        #         X += 1
        #         R  = int(binom(N-X, P-1))
        #         K += R
        #     K -= R
        #     C[0] = X-1

        #     for I in range(2, P):
        #         X += 1
        #         R  = int(binom(N-X, P-I))
        #         K += R
        #         while (K <= L):
        #             X += 1
        #             R  = int(binom(N-X, P-I))
        #             K += R
        #         K -= R
        #         C[I-1] = X-1
        #     C[P-1] = X + L - K
        #     return C



    '''
    SPLIT AND RENDER METHODS HERE
    '''



    ''' Image renderer (copied from StrEmbed) '''
    def quick_render(self, shape, colour = None, img_file = None):

        self.renderer.EraseAll()

        if colour:
            ''' Render in specified colour... '''
            c = colour
            self.renderer.DisplayShape(shape, color = Quantity_Color(c.Red(),
                                                                      c.Green(),
                                                                      c.Blue(),
                                                                      Quantity_TOC_RGB))
        else:
            ''' ...or in default colour (for better reference images), i.e. orange '''
            self.renderer.DisplayShape(shape)

        try:
            # print('Fitting and dumping image ', img_name)
            ''' Create directory if it doesn't already exist '''
            img_path = os.path.split(img_file)[0]
            if not os.path.isdir(img_path):
                os.mkdir(img_path)

            self.renderer.View.FitAll()
            self.renderer.View.ZFitAll()
            self.renderer.View.Dump(img_file)
            ''' Check if rendered and dumped, i.e. if image file exists '''
            if os.path.exists(img_file):
                # print('Image saved to ', img_file)
                image_saved_ok = True
            else:
                print('Could not save image')
                image_saved_ok = False

        except Exception as e:
            print('Could not dump image to file; exception follows')
            print(e)
            image_saved_ok = False

        return image_saved_ok



    ''' HR June 21 Updated to allow only products to be dumped '''
    def split_and_render(self, path = None, products_only = False, subshapes = False):

        # for node in self.nodes:
        #     print(node, self.nodes[node]['screen_name'])

        ''' Collect nodes to be checked, remove unwanted nodes (non-products, subshapes) '''
        nodes = self.nodes
        _to_remove = []
        if products_only:
            _to_remove.extend([el for el in nodes if not self.nodes[el]['is_product']])
        if not subshapes:
            _to_remove.extend([el for el in nodes if self.nodes[el]['is_subshape']])
        if _to_remove:
            for el in _to_remove:
                nodes.remove(el)

        ''' Collect unique shapes (i.e. avoid duplication) with names '''
        shapes = {}

        for node in nodes:
            d = self.nodes[node]

            ''' Skip if no shape '''
            if not d['shape_raw'][0]:
                continue
            shape = d['shape_raw'][0]

            ''' Skip rest if shape already grabbed or is sub-shape '''
            if (shape in shapes):
                # print('Duplicate shape found')
                continue
            # if not subshapes and d['is_subshape']:
            #     # print('Sub-shape found; ignoring')
            #     continue

            ''' Else go through naming logic and add to shape map
                1. If product, get product name, as maps to shape,
                2. Otherwise get screen name '''
            if d['is_product']:
                name = d['occ_name']
            else:
                name = d['screen_name']
            shapes[shape] = name



        ''' Abort if no shapes '''
        if not shapes:
            print('No shapes found; aborting...')
            return


        ''' Get cwd as path if none given '''
        if not path:
            path = os.getcwd()

        ''' Create folder '''
        folder = os.path.join(path, remove_suffixes(self.step_filename))
        if not os.path.exists(folder):
            print('Creating folder...')
            os.makedirs(folder)

        ''' DO DUMP: Generate and save STEP and image files '''
        for k,v in shapes.items():
            step_file = os.path.join(folder, v + '.STEP')
            if os.path.isfile(step_file):
                print('Part model already exists; not saving')
            else:
                print('Saving STEP file for part: ', v)
                DataExchange.write_step_file(k, step_file)

            img_file = os.path.join(folder, v + '.jpg')
            if os.path.isfile(img_file):
                print('Part image file already exists; not saving')
            else:
                print('Saving image for part: ', v)
                self.quick_render(k, img_file = img_file)
