# HR June 2019 onwards
# Version 5 to follow HHC's StrEmbed-4 in Perl
# User interface for lattice-based assembly configurations

### ---
# HR 17/10/19
# Version 5.1 to draw main window as panels within flexgridsizer
# Avoids confusing setup for staticbox + staticboxsizer
### ---

### ---
# HR 12/12/2019 onwards
# Version 5.2
### ---

### BUGS LOG
# 1 // 7/2/20
# Images in selector view does not update when resized until next resize
# e.g. when maximised, images remain small
# FIXED Feb 2020 with CallAfter
# ---
# 2 // 7/2/20
# Image rescaling (via ScaleImage method) may need correction
# Sometimes appears that images overlap border of toggle buttons partly
# ---
# 3 // 6/3/20
# Assembly operation methods (flatten, assemble, etc.) need compressing into fewer methods
# as currently a lot of repeated code

### ---
# HR 23/03/2020 onwards
# Version 5.3
### ---

"""
HR 11/08/20 onwards
Version 5.5
"""


# WX stuff
import wx
# WX customtreectrl for parts list
import wx.lib.agw.customtreectrl as ctc
import wx.ribbon as RB

# # Allows inspection of app elements via Ctrl + Alt + I
# Use InspectableApp() in MainLoop()
# import wx.lib.mixins.inspection as wit

# For scrolled panel
import wx.lib.scrolledpanel as scr

# matplotlib stuff
import matplotlib as mpl
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

# Ordered dictionary
from collections import OrderedDict as odict

# Regular expressions
import re

# OS operations for exception-free file checking
import os.path

import shutil
import nltk

# For timings
import time

# Import networkx for plotting lattice
import networkx as nx

# Gets rid of blurring throughout application by getting DPI info
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(True)
except:
    pass

# For STEP import
from step_parse_5_5 import StepParse

# import matplotlib.pyplot as plt
import numpy as np
# from scipy.special import comb

import images

# For 3D CAD viewer based on python-occ
from OCC.Display import OCCViewer
# import wxDisplay
# from OCC.Display import wxDisplay
from OCC.Core.Quantity import (Quantity_Color, Quantity_NOC_WHITE, Quantity_TOC_RGB)
from OCC.Core.AIS import AIS_Shaded, AIS_WireFrame



''' Get bitmap from "images" script, which must itself be created
    via "embed_images" '''
def CreateBitmap(imgName, mask = wx.WHITE, size = None):
    if not size:
        size = (100,100)

    # Ah gorrit...
    _bmp = getattr(images, imgName).GetBitmap()
    _im = _bmp.ConvertToImage()

    # ...ah rescaled it...
    width, height = size
    _im = _im.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
    _bmp = wx.Bitmap(_im)

    # ...ah masked iroff
    if mask:
        _mask = wx.Mask(_bmp, wx.WHITE)
        _bmp.SetMask(_mask)

    return _bmp



''' To add some GUI-specific bits and bobs '''
class MyParse(StepParse):

    def __init__(self, _id = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._id = _id



class MyTree(ctc.CustomTreeCtrl):

    def __init__(self, parent, style):
        super().__init__(parent = parent, agwStyle = style)
        self.parent = parent
        self.reverse_sort = False
        self.alphabetical = True



    # Overridden method to allow sorting based on data other than text
    # Can be sorted alphabetically or numerically, and in reverse
    # ---
    # This method is called by sorting methods
    # ---
    # NOTE the functionality necessary for this was added to the wxWidgets / Phoenix Github repo
    # in 2018 in response to issue #774 here: https://github.com/wxWidgets/Phoenix/issues/774
    def OnCompareItems(self, item1, item2):

        if self.alphabetical:
            t1 = self.GetItemText(item1)
            t2 = self.GetItemText(item2)
        else:
            t1 = self.GetPyData(item1)['sort_id']
            t2 = self.GetPyData(item2)['sort_id']

        if self.reverse_sort:
            reverse = -1
        else:
            reverse = 1

        if t1 < t2:
            return -1*reverse
        if t1 == t2:
            return 0
        return reverse



    def GetDescendants(self, item):

        '''
        Get all children of CTC item recursively
        Named "GetDescendants" as recursive children in Networkx are "descendants"
        ---
        MUST create shallow copy of children here to avoid strange behaviour
        According to ctc docs, "It is advised not to change this list
        i.e. returned list] and to make a copy before calling
        other tree methods as they could change the contents of the list."
        See: https://wxpython.org/Phoenix/docs/html/wx.lib.agw.customtreectrl.GenericTreeItem.html
        '''
        descendants = item.GetChildren().copy()
        # They mess you up, your mum and dad
        parents = descendants
        while parents:
            # They may not mean to, but they do
            children = []
            for parent in parents:
                children = parent.GetChildren().copy()
                # They fill you with the faults they had
                descendants.extend(children)
                # And add some extra, just for you
                parents = children
        return descendants



    def SortAllChildren(self, item):

        # Get all non-leaf nodes of parent CTC object (always should be MainWindow)
        nodes = self.GetDescendants(item)
        nodes = [el for el in nodes if el.HasChildren()]
        for node in nodes:
            count = self.GetChildrenCount(node, recursively = False)
            if count > 1:
                self.SortChildren(node)



"""
HR 26/08/2020
ShapeRenderer, wxBaseViewer and wxViewer3D both adapted from pythonocc script "wxDisplay"
https://github.com/tpaviot/pythonocc-core
Copyright info below
"""

##Copyright 2008-2017 Thomas Paviot (tpaviot@gmail.com)
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

class ShapeRenderer(OCCViewer.Viewer3d):
    # HR 17/7/20
    # Adapted/simplified from OffScreenRenderer in OCCViewer <- OCC.Display
    # Dumps render of shape to jpeg file
    def __init__(self, screen_size = (1000,1000)):
        super().__init__()
        self.Create()
        self.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_WHITE))
        self.SetSize(screen_size[0], screen_size[1])
        # self.DisableAntiAliasing()
        self.SetModeShaded()
        # self.display_triedron()

        self._rendered = False



class wxBaseViewer(wx.Panel):
    def __init__(self, parent = None):
        super().__init__(parent, style = wx.BORDER_SIMPLE)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnLostFocus)
        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        # self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMiddleUp)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMiddleDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheelScroll)

        self._display = None
        self._inited = False

    def GetWinId(self):
        """ Returns the windows Id as an integer.
        issue with GetHandle on Linux for wx versions
        >3 or 4. Window must be displayed before GetHandle is
        called. For that, just wait for a few milliseconds/seconds
        before calling InitDriver
        a solution is given here
        see https://github.com/cztomczak/cefpython/issues/349
        but raises an issue with wxPython 4.x
        finally, it seems that the sleep function does the job
        reported as a pythonocc issue
        https://github.com/tpaviot/pythonocc-core/476
        """
        timeout = 10  # 10 seconds
        win_id = self.GetHandle()
        init_time = time.time()
        delta_t = 0.  # elapsed time, initialized to 0 before the while loop
        # if ever win_id is 0, enter the loop untill it gets a value
        while win_id == 0 and delta_t < timeout:
            time.sleep(0.1)
            wx.SafeYield()
            win_id = self.GetHandle()
            delta_t = time.time() - init_time
        # check that win_id is different from 0
        if win_id == 0:
            raise AssertionError("Can't get win Id")
        # otherwise returns the window Id
        return win_id

    def OnSize(self, event):
        if self._inited:
            self._display.OnResize()

    def OnIdle(self, event):
        pass

    def OnMove(self, event):
        pass

    def OnFocus(self, event):
        pass

    def OnLostFocus(self, event):
        pass

    def OnMaximize(self, event):
        pass

    def OnLeftDown(self, event):
        pass

    def OnRightDown(self, event):
        pass

    def OnMiddleDown(self, event):
        pass

    def OnLeftUp(self, event):
        pass

    def OnRightUp(self, event):
        pass

    def OnMiddleUp(self, event):
        pass

    def OnMotion(self, event):
        pass

    def OnKeyDown(self, event):
        pass



class wxViewer3d(wxBaseViewer):
    def __init__(self, *kargs):
        super().__init__(*kargs)

        self._drawbox = False
        self._zoom_area = False
        self._select_area = False
        self._inited = False
        self._leftisdown = False
        self._middleisdown = False
        self._rightisdown = False
        self._selection = None
        self._scrollwheel = False
        self._key_map = {}
        self.dragStartPos = None

    def InitDriver(self):
        ''' HR 26/12/20 modified to pass window handle to "Create" rather than "__init__""
            If handle not passed, renderer is off-screen (see OCCViewer) '''
        # self._display = OCCViewer.Viewer3d(self.GetWinId())
        # self._display.Create()
        self._display = OCCViewer.Viewer3d()
        self._display.Create(self.GetWinId())
        self._display.SetModeShaded()
        self._inited = True

        # dict mapping keys to functions
        self._SetupKeyMap()

    def _SetupKeyMap(self):
        def set_shade_mode():
            self._display.DisableAntiAliasing()
            self._display.SetModeShaded()

        self._key_map = {ord('W'): self._display.SetModeWireFrame,
                         ord('S'): set_shade_mode,
                         ord('A'): self._display.EnableAntiAliasing,
                         ord('B'): self._display.DisableAntiAliasing,
                         ord('H'): self._display.SetModeHLR,
                         ord('G'): self._display.SetSelectionModeVertex,
                         # 306: lambda: print('Shift pressed')
                        }

    def OnKeyDown(self, evt):
        code = evt.GetKeyCode()
        try:
            self._key_map[code]()
            # print('Key pressed: %i' % code)
        except KeyError:
            # print('Unrecognized key pressed %i' % code)
            pass

    def OnMaximize(self, event):
        if self._inited:
            self._display.Repaint()

    def OnMove(self, event):
        if self._inited:
            self._display.Repaint()

    def OnIdle(self, event):
        if self._drawbox:
            pass
        elif self._inited:
            self._display.Repaint()

    def Test(self):
        if self._inited:
            self._display.Test()

    def OnFocus(self, event):
        if self._inited:
            self._display.Repaint()

    def OnLostFocus(self, event):
        if self._inited:
            self._display.Repaint()

    def OnPaint(self, event):
        if self._inited:
            self._display.Repaint()

    def ZoomAll(self, evt):
        self._display.FitAll()

    def Repaint(self, evt):
        if self._inited:
            self._display.Repaint()

    def OnLeftDown(self, evt):
        self.SetFocus()
        self.dragStartPos = evt.GetPosition()
        self._display.StartRotation(self.dragStartPos.x, self.dragStartPos.y)

    def OnLeftUp(self, evt):
        pt = evt.GetPosition()
        if self._select_area:
            [Xmin, Ymin, dx, dy] = self._drawbox
            self._display.SelectArea(Xmin, Ymin, Xmin+dx, Ymin+dy)
            self._select_area = False
        else:
            self._display.Select(pt.x, pt.y)

    def OnMiddleDown(self, evt):
        self.dragStartPos = evt.GetPosition()
        self._display.StartRotation(self.dragStartPos.x, self.dragStartPos.y)

    def OnMiddleUp(self, evt):
        pass

    def OnRightDown(self, evt):
        self.dragStartPos = evt.GetPosition()
        self._display.StartRotation(self.dragStartPos.x, self.dragStartPos.y)

    def OnRightUp(self, evt):
        if self._zoom_area:
            [Xmin, Ymin, dx, dy] = self._drawbox
            self._display.ZoomArea(Xmin, Ymin, Xmin+dx, Ymin+dy)
            self._zoom_area = False

    def OnWheelScroll(self, evt):
        # Zooming by wheel
        if evt.GetWheelRotation() > 0:
            zoom_factor = 2.
        else:
            zoom_factor = 0.5
        self._display.Repaint()
        self._display.ZoomFactor(zoom_factor)

    def DrawBox(self, event):
        tolerance = 2
        pt = event.GetPosition()
        dx = pt.x - self.dragStartPos.x
        dy = pt.y - self.dragStartPos.y
        if abs(dx) <= tolerance and abs(dy) <= tolerance:
            return
        dc = wx.ClientDC(self)
        dc.SetPen(wx.Pen(wx.WHITE, 1, wx.DOT))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.XOR)
        if self._drawbox:
            r = wx.Rect(*self._drawbox)
            dc.DrawRectangle(r)
        r = wx.Rect(self.dragStartPos.x, self.dragStartPos.y, dx, dy)
        dc.DrawRectangle(r)
        self._drawbox = [self.dragStartPos.x, self.dragStartPos.y, dx, dy]

    def OnMotion(self, evt):
        pt = evt.GetPosition()

        # ROTATE
        if evt.LeftIsDown() and not evt.ShiftDown():
            self._display.Rotation(pt.x, pt.y)
            self._drawbox = False
        # DYNAMIC ZOOM
        elif evt.RightIsDown() and not evt.ShiftDown():
            self._display.Repaint()
            self._display.DynamicZoom(abs(self.dragStartPos.x), abs(self.dragStartPos.y), abs(pt.x), abs(pt.y))
            self.dragStartPos.x = pt.x
            self.dragStartPos.y = pt.y
            self._drawbox = False
        # PAN
        elif evt.MiddleIsDown():
            dx = pt.x - self.dragStartPos.x
            dy = pt.y - self.dragStartPos.y
            self.dragStartPos.x = pt.x
            self.dragStartPos.y = pt.y
            self._display.Pan(dx, -dy)
            self._drawbox = False
        # DRAW BOX
        elif evt.RightIsDown() and evt.ShiftDown():  # ZOOM WINDOW
            self._zoom_area = True
            self.DrawBox(evt)
        elif evt.LeftIsDown() and evt.ShiftDown():  # SELECT AREA
            self._select_area = True
            self.DrawBox(evt)
        else:
            self._drawbox = False
            self._display.MoveTo(pt.x, pt.y)



''' Class to veto unsplit when sash is double-clicked '''
class MySplitter(wx.SplitterWindow):
    def __init__(self, parent):

        super().__init__(parent = parent)
        self.Bind(wx.EVT_SPLITTER_DCLICK, self.OnSashDoubleClick)

    def OnSashDoubleClick(self, event):
        event.Veto()



class NotebookPanel(wx.Panel):
    def __init__(self, parent, name, _id, border = 0, panel_style = None):

        super().__init__(parent = parent)

        self.name = name
        self._id = _id
        if panel_style == None:
            self.panel_style = wx.BORDER_SIMPLE
        else:
            self.panel_style = panel_style



        # OVERALL SIZER AND FIRST SPLITTER SETUP
        _splitter = MySplitter(self)

        self.part_panel = wx.Panel(_splitter, style = self.panel_style)
        # self.view_panel = wx.Panel(_splitter, style = self.panel_style)
        self._view_splitter = MySplitter(_splitter)

        # _splitter.SplitVertically(self.part_panel, self.view_panel)
        _splitter.SplitVertically(self.part_panel, self._view_splitter)
        _splitter.SetSashGravity(0.5)

        self_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self_sizer.Add(_splitter, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(self_sizer)

        _splitter_sizer = wx.BoxSizer(wx.HORIZONTAL)
        _splitter_sizer.Add(self.part_panel, wx.ALL|wx.EXPAND)
        _splitter_sizer.Add(self._view_splitter, wx.ALL|wx.EXPAND)
        _splitter.SetSizer(_splitter_sizer)



        # PARTS VIEW SETUP
        self.treeStyle = (ctc.TR_MULTIPLE | ctc.TR_EDIT_LABELS | ctc.TR_HAS_BUTTONS)
        self.partTree_ctc = MyTree(self.part_panel, style = self.treeStyle)

        part_sizer = wx.BoxSizer(wx.VERTICAL)
        part_sizer.Add(self.partTree_ctc, 1, wx.ALL|wx.EXPAND)
        self.part_panel.SetSizer(part_sizer)



        # GEOMETRY VIEWS SETUP

        self.occ_panel = wxViewer3d(self._view_splitter)
        self.occ_panel.InitDriver()
        self.occ_panel._display.View.SetBackgroundColor(Quantity_Color(Quantity_NOC_WHITE))

        self.slct_panel = scr.ScrolledPanel(self._view_splitter, style = self.panel_style)
        self.slct_panel.SetupScrolling()
        self.slct_panel.SetBackgroundColour('white')

        # Set up image-view grid, where "rows = 0" means the sizer updates dynamically
        # according to the number of elements it holds
        self.image_cols = 4
        self.slct_sizer = wx.FlexGridSizer(cols = self.image_cols, rows = 0, hgap = 5, vgap = 5)

        self.slct_panel.SetSizer(self.slct_sizer)

        self._view_splitter.SplitHorizontally(self.slct_panel, self.occ_panel)
        self._view_splitter.SetSashGravity(0.5)

        # _view_splitter_sizer = wx.BoxSizer(wx.VERTICAL)
        # _view_splitter_sizer.Add(_view_splitter, 1, wx.ALL|wx.EXPAND)
        # self.view_panel.SetSizer(_view_splitter_sizer)



        ## Discard pile and alternative assembly
        # self.discarded = StepParse()
        self.alt = StepParse()

        self.edge_alt_dict = {}
        self.node_alt_dict = {}

        self.ctc_dict     = {}
        self.ctc_dict_inv = {}

        # Toggle buttons
        self.button_dict     = odict()
        self.button_dict_inv = odict()
        self.button_img_dict = {}

        self.file_open = False

        # self.occ_panel.Refresh()



        ''' A starter tree for the user, deleted when file opened '''
        ctc_root_item = self.partTree_ctc.AddRoot(text = 'Root', ct_type = 1)
        self.partTree_ctc.AppendItem(ctc_root_item, text = 'Child 1', ct_type = 1)
        self.partTree_ctc.AppendItem(ctc_root_item, text = 'Child 2', ct_type = 1)
        self.partTree_ctc.ExpandAll()




class MainWindow(wx.Frame):
    def __init__(self):

        super().__init__(parent = None, title = "StrEmbed-5-5")

        ''' All other app-wide initialisation '''
        self.SetBackgroundColour('white')
        self.SetIcon(wx.Icon(wx.ArtProvider.GetBitmap(wx.ART_PLUS)))

        self.no_image_ass  = images.no_image_ass_png.GetBitmap()
        self.no_image_part = images.no_image_part_png.GetBitmap()

        self.im_folder = 'Temp'
        # _path = os.getcwd()
        self.im_path = os.path.join(os.getcwd(), self.im_folder)
        if not os.path.exists(self.im_path):
            os.mkdir(self.im_path)
            print('Created temporary image folder at ', self.im_path)

        # Off-screen renderer for producing static images for toggle buttons
        self.renderer = ShapeRenderer()

        self.tight = 0.9
        self._border = 1
        self._default_size = (30,30)
        self._button_size = (50,50)
        self.veto = False

        self._highlight_colour = wx.RED

        ''' OBJECT FOR ASSEMBLY MANAGEMENT '''
        self.assembly_manager = {}
        # self.assembly_id = 0

        # Themes for assembly suggestions in "Assistant"
        # self.themes = ['Group items by similar names',
        #                'Group items by material',
        #                'Group by part dimensions',
        #                'Create maintenance bill',
        #                'Create manufacturing bill,
        #                Create transport bill']
        self.themes = ['Create maintenance bill',
                       'Create manufacturing bill',
                       'Create transport bill']



        ID_NEW = self.NewControlId()
        ID_DELETE = self.NewControlId()
        ID_FILE_OPEN = self.NewControlId()
        ID_FILE_SAVE = self.NewControlId()
        ID_FILE_SAVE_AS = self.NewControlId()

        ID_ASSEMBLE = self.NewControlId()
        ID_FLATTEN = self.NewControlId()
        ID_DISAGGREGATE = self.NewControlId()
        ID_AGGREGATE = self.NewControlId()
        ID_ADD_NODE = self.NewControlId()
        ID_REMOVE_NODE = self.NewControlId()
        ID_SORT_MODE = self.NewControlId()
        ID_SORT_REVERSE = self.NewControlId()

        ID_CALC_SIM = self.NewControlId()
        ID_ASS_MAP = self.NewControlId()
        ID_RECON = self.NewControlId()
        ID_SUGGEST = self.NewControlId()

        ID_SETTINGS = self.NewControlId()
        ID_ABOUT = self.NewControlId()

        self.ID_ASSISTANT_PAGE = self.NewControlId()



        ''' Main panel containing everything '''
        panel_top = wx.Panel(self)

        ''' Ribbon with tools '''
        self._ribbon = RB.RibbonBar(panel_top, style=RB.RIBBON_BAR_DEFAULT_STYLE
                                                |RB.RIBBON_BAR_SHOW_PANEL_EXT_BUTTONS)



        home = RB.RibbonPage(self._ribbon, wx.ID_ANY, "Home")

        file_panel = RB.RibbonPanel(home, wx.ID_ANY, "File",
                                       style=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)
        toolbar = RB.RibbonToolBar(file_panel, wx.ID_ANY)

        toolbar.AddTool(ID_FILE_OPEN, wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, wx.Size(self._default_size)))
        toolbar.AddTool(ID_FILE_SAVE, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, wx.Size(self._default_size)))
        toolbar.AddTool(ID_FILE_SAVE_AS, wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_OTHER, wx.Size(self._default_size)))
        toolbar.AddSeparator()
        toolbar.AddHybridTool(ID_NEW, wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_OTHER, wx.Size(self._default_size)))
        toolbar.AddHybridTool(ID_DELETE, wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_OTHER, wx.Size(self._default_size)))
        toolbar.SetRows(2, 3)

        ass_panel = RB.RibbonPanel(home, wx.ID_ANY, "Assembly")

        ass_ops = RB.RibbonButtonBar(ass_panel)
        ass_ops.AddButton(ID_ADD_NODE, "Add node", CreateBitmap("add_node_png", size = self._button_size),
                          help_string="Add node at selected position")
        ass_ops.AddButton(ID_REMOVE_NODE, "Remove node", CreateBitmap("remove_node_png", size = self._button_size),
                         help_string = "Remove selected node")
        ass_ops.AddButton(ID_ASSEMBLE, "Assemble", CreateBitmap("assemble_png", size = self._button_size),
                         help_string = "Assemble parts into sub-assembly")
        ass_ops.AddButton(ID_FLATTEN, "Flatten", CreateBitmap("flatten_png", size = self._button_size),
                         help_string = "Remove sub-assemblies")
        ass_ops.AddButton(ID_DISAGGREGATE, "Disaggregate", CreateBitmap("disaggregate_png", size = self._button_size),
                         help_string = "Create sub-assembly with two parts")
        ass_ops.AddButton(ID_AGGREGATE, "Aggregate", CreateBitmap("aggregate_png", size = self._button_size),
                         help_string = "Remove all contained parts and create single part")

        sort_panel = RB.RibbonPanel(home, wx.ID_ANY, "Sort")

        sort_ops = RB.RibbonButtonBar(sort_panel)
        sort_ops.AddButton(ID_SORT_MODE, "Sort mode", CreateBitmap("sort_mode_png", size = self._button_size),
                         help_string = "Toggle alphabetical/numerical sort in parts list")
        sort_ops.AddButton(ID_SORT_REVERSE, "Sort reverse", CreateBitmap("sort_reverse_png", size = self._button_size),
                         help_string = "Reverse sort order in parts list")



        assistant_tab = RB.RibbonPage(self._ribbon, self.ID_ASSISTANT_PAGE, "Assistant")



        selector_panel = RB.RibbonPanel(assistant_tab, wx.ID_ANY, "Selector")
        self.selector_1 = wx.Choice(selector_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, [])
        self.selector_2 = wx.Choice(selector_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, [])
        self.selector_1.SetMinSize(wx.Size(100, -1))
        self.selector_2.SetMinSize(wx.Size(100, -1))


        selector_sizer = wx.BoxSizer(wx.VERTICAL)
        # selector_sizer.AddStretchSpacer(1)
        selector_sizer.Add(self.selector_1, 0, wx.ALL|wx.EXPAND, border = 10)
        selector_sizer.Add(self.selector_2, 0, wx.ALL|wx.EXPAND, border = 10)
        # selector_sizer.AddStretchSpacer(1)
        selector_panel.SetSizer(selector_sizer)

        recon_panel = RB.RibbonPanel(assistant_tab, wx.ID_ANY, "Comparison tools")

        recon_ops = RB.RibbonButtonBar(recon_panel)
        recon_ops.AddButton(ID_CALC_SIM, "Calculate similarity", CreateBitmap("compare_png", size = self._button_size),
                         help_string = "Calculate and report similarity between two assemblies")
        recon_ops.AddButton(ID_ASS_MAP, "Map assembly elements", CreateBitmap("injection_png", size = self._button_size),
                         help_string = "Map elements in first assembly to those in second")
        recon_ops.AddButton(ID_RECON, "Reconcile assemblies", CreateBitmap("tree_png", size = self._button_size),
                         help_string = "Calculate and report edit path(S) to transform one assembly into another")

        suggestions_panel = RB.RibbonPanel(assistant_tab, wx.ID_ANY, "Configuration suggestions")

        suggestions_ops = RB.RibbonButtonBar(suggestions_panel)
        suggestions_ops.AddHybridButton(ID_SUGGEST, "Suggest new assembly", CreateBitmap("bulb_sharp_small_png", size = self._button_size))



        settings_tab = RB.RibbonPage(self._ribbon, wx.ID_ANY, "Settings & help")

        settings_panel = RB.RibbonPanel(settings_tab, wx.ID_ANY, "Settings",
                                       style=RB.RIBBON_PANEL_NO_AUTO_MINIMISE)

        settings_tools = RB.RibbonToolBar(settings_panel, wx.ID_ANY)
        settings_tools.AddTool(ID_SETTINGS, wx.ArtProvider.GetBitmap(wx.ART_HELP_SETTINGS, wx.ART_OTHER, wx.Size(self._default_size)))
        settings_tools.AddTool(ID_ABOUT, wx.ArtProvider.GetBitmap(wx.ART_QUESTION, wx.ART_OTHER, wx.Size(self._default_size)))

        self._ribbon.Realize()



        ''' Initialise main layout:
                (L) Assembly-specific notebook pages
                (R) Lattice view containing all assemblies '''

        _splitter = MySplitter(panel_top)

        self.latt_panel = wx.Panel(_splitter)
        self._notebook = wx.Notebook(_splitter)

        _splitter.SplitVertically(self._notebook,self.latt_panel)
        _splitter.SetSashGravity(0.5)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(self._ribbon, 0, wx.EXPAND)
        s.Add(_splitter, 1, wx.ALL|wx.EXPAND, self._border)
        panel_top.SetSizer(s)

        # LATTICE VIEW SETUP
        # Set up matplotlib FigureCanvas with toolbar for zooming and movement
        self.latt_figure = mpl.figure.Figure()
        self.latt_canvas = FigureCanvas(self.latt_panel, -1, self.latt_figure)
        self.latt_axes   = self.latt_figure.add_subplot(111)
        # self.latt_axes.axis('off')
        self.latt_tb = NavigationToolbar(self.latt_canvas)

        # Remove plot border/axes and tick marks
        self.latt_axes.axes.axis('off')
        self.latt_axes.axes.get_xaxis().set_ticks([])
        self.latt_axes.axes.get_yaxis().set_ticks([])

        s2 = wx.BoxSizer(wx.HORIZONTAL)
        s2.Add(self._notebook, 1, wx.ALL|wx.EXPAND, self._border)
        s2.Add(self.latt_panel, 1, wx.ALL|wx.EXPAND, self._border)
        _splitter.SetSizer(s2)

        sb = wx.StaticBox(self.latt_panel, -1, label = 'Lattice view')
        self.latt_sizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.latt_sizer.Add(self.latt_canvas, 1, wx.EXPAND | wx.ALIGN_TOP | wx.ALL, self._border)
        self.latt_sizer.Add(self.latt_tb, 0, wx.ALL|wx.EXPAND, self._border)
        self.latt_panel.SetSizer(self.latt_sizer)

        # Can call Realize() and/or Hide(), to be shown later when file loaded/data updated
        # self.latt_canvas.Hide()
        # self.latt_tb.Realize()
        # self.latt_tb.Hide()



        self.default_colour  = 'red'
        self.selected_colour = 'blue'
        self.alt_colour      = 'green'



        ''' Status bar '''
        self.statbar = self.CreateStatusBar()



        ''' App-wide bindings '''
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, self.OnNewButton, id = ID_NEW)
        self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, self.OnDeleteAssembly, id = ID_DELETE)
        self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, self.OnFileOpen, id = ID_FILE_OPEN)

        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnAddNode, id = ID_ADD_NODE)
        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnRemoveNode, id = ID_REMOVE_NODE)
        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnAssemble, id = ID_ASSEMBLE)
        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnFlatten, id = ID_FLATTEN)
        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnDisaggregate, id = ID_DISAGGREGATE)
        ass_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnAggregate, id = ID_AGGREGATE)

        sort_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSortMode, id = ID_SORT_MODE)
        sort_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSortReverse, id = ID_SORT_REVERSE)

        recon_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnCalcSim, id = ID_CALC_SIM)
        recon_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnMapAssemblies, id = ID_ASS_MAP)
        recon_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnRecon, id = ID_RECON)

        suggestions_ops.Bind(RB.EVT_RIBBONBUTTONBAR_CLICKED, self.OnSuggestionsButton, id = ID_SUGGEST)
        suggestions_ops.Bind(RB.EVT_RIBBONBUTTONBAR_DROPDOWN_CLICKED, self.OnSuggestionsDropdown, id = ID_SUGGEST)

        self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, self.OnSettings, id = ID_SETTINGS)
        self.Bind(RB.EVT_RIBBONTOOLBAR_CLICKED, self.OnAbout, id = ID_ABOUT)

        self.Bind(RB.EVT_RIBBONBAR_PAGE_CHANGING, self.OnRibbonTabChanging)

        self._notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnNotebookPageChanged)
        self._notebook.Bind(wx.EVT_RIGHT_DOWN, self.OnNotebookRightDown)




        ''' Lattice view bindings: "mpl_connect" is equivalent of WX "Bind" '''
        self.latt_canvas.mpl_connect('button_press_event', self.GetLattPos)
        # self.latt_canvas.mpl_connect('button_release_event', self.LattNodeSelected)
        self.latt_canvas.mpl_connect('button_release_event', self.OnLatticeMouseRelease)
        # self.latt_canvas.mpl_connect('pick_event', self.OnNodePick)



        self.new_assembly_text = 'Unnamed item'
        self.new_part_text     = 'Unnamed item'



        ''' Starter assembly '''
        self.MakeNewAssembly()



    def get_selected_assemblies(self):

        self.AddText('Trying to get selected assemblies...')

        if self.selector_1.GetSelection() == wx.NOT_FOUND or self.selector_2.GetSelection() == wx.NOT_FOUND:
            self.AddText('Two assemblies not selected')
            return

        _s1 = self.selector_1.GetSelection()
        _s2 = self.selector_2.GetSelection()

        if _s1 == _s2:
            self.AddText('Two different assemblies must be selected')
            return None

        _name1 = self.selector_1.GetString(_s1)
        _name2 = self.selector_1.GetString(_s2)
        self.AddText('Assemblies selected:')
        print(_name1)
        print(_name2)

        a1 = [el for el in self.assembly_manager if el.name == _name1][0]
        a1 = self.assembly_manager[a1]
        a2 = [el for el in self.assembly_manager if el.name == _name2][0]
        a2 = self.assembly_manager[a2]

        return a1, a2



    def OnMapAssemblies(self, event):

        print('Mapping assembly elements...')
        _assemblies = self.get_selected_assemblies()

        if not _assemblies:
            self.AddText('Could not get assemblies')
            return None

        a1 = _assemblies[0]
        a2 = _assemblies[1]

        _mapped, _unmapped = StepParse.map_nodes(a1, a2)
        self.AddText('Done mapping nodes')
        print('Mapped nodes: ', _mapped)
        print('Unmapped nodes: ', _unmapped)



    def OnCalcSim(self, event):

        self.AddText('Calculate similarity button pressed')

        _assemblies = self.get_selected_assemblies()

        if not _assemblies:
            self.AddText('Could not get assemblies')
            return None

        a1 = _assemblies[0]
        a2 = _assemblies[1]
        _map = {}

        l1 = a1.leaves
        l2 = a2.leaves

        for n1 in l1:
            for n2 in l2:
                _map[(n1, n2)] = StepParse.similarity(a1.nodes[n1]['label'], a2.nodes[n2]['label'])

        _g = nx.compose(a1,a2)
        print('Nodes:', _g.nodes)
        print('Edges:', _g.edges)

        return _map



    def OnRecon(self, event = None):

        self.AddText('Tree reconciliation running...')

        _assemblies = self.get_selected_assemblies()

        if not _assemblies:
            self.AddText('Could not get assemblies')
            return None

        a1 = _assemblies[0]
        a2 = _assemblies[1]

        paths, cost, cost_from_edits, node_edits, edge_edits = StepParse.Reconcile(a1, a2)

        _textout = 'Node edits: {}\nEdge edits: {}\nTotal cost (Networkx): {}\nTotal cost (no. of edits): {}'.format(
            node_edits, edge_edits, cost, cost_from_edits)

        self.AddText('Tree reconciliation finished')
        self.DoNothingDialog(event, _textout)



    def OnSuggestionsButton(self, event):
        self.AddText('Generating suggestions for new assembly based on selected them (priorities)...')



    def OnSuggestionsDropdown(self, event):
        menu = wx.Menu()
        for item in self.themes:
            menu.Append(wx.ID_ANY, item)

        event.PopupMenu(menu)



    def OnRibbonTabChanging(self, event = None):
        print('Ribbon tab changing')

        ''' To repopulate assembly selectors (ComboBox)whenever that tab is selected '''
        if event.GetPage().GetId() == self.ID_ASSISTANT_PAGE:
            print('Assistant page selected')
            try:
                _list = self.assembly_list
                print('List of assemblies:', _list)
                self.selector_1.Set(_list)
                self.selector_2.Set(_list)
            except:
                print('Could not reset assembly selector tools')

        if event:
            event.Skip()



    def OnNotebookRightDown(self, event):
        menu = wx.Menu()
        ID_DELETE_ASSEMBLY = self.NewControlId()
        ID_RENAME_ASSEMBLY = self.NewControlId()

        menu.Append(ID_DELETE_ASSEMBLY, 'Delete assembly')
        menu.Append(ID_RENAME_ASSEMBLY, 'Rename assembly')

        menu.Bind(wx.EVT_MENU, self.OnRenameAssembly, id = ID_RENAME_ASSEMBLY)
        menu.Bind(wx.EVT_MENU, self.OnDeleteAssembly, id = ID_DELETE_ASSEMBLY)

        self.PopupMenu(menu)



    def UserInput(self, message = 'Text input', caption = 'Enter text', value = None):
        dlg = wx.TextEntryDialog(self, message, caption, value = value)
        dlg.ShowModal()
        result = dlg.GetValue()
        dlg.Destroy()
        return result



    def OnRenameAssembly(self, event):
        _page = self._notebook.GetPage(self._notebook.GetSelection())
        _old_name = _page.name

        _new_name_okay= False
        while not _new_name_okay:
            _new_name = self.UserInput(caption = 'Enter new assembly name', value = _old_name)
            if _old_name == _new_name:
                return
            # Remove special characters
            _new_name_corr = re.sub('[!@~#$_]', '', _new_name)
            if _new_name_corr != _new_name:
                _new_name = _new_name_corr
                print('Special characters removed')
            # Check new name not in existing names (excluding current)
            _names = [el.name for el in self.assembly_manager]
            _names.remove(_old_name)
            if _new_name not in _names:
                print('New name not in existing names')
                _new_name_okay = True
            else:
                print('New name in existing names! No can do, buddy!')
                continue
            # Check new name is string of non-zero length
            if isinstance(_new_name, str) and _new_name:
                print('New name applied')
                _new_name_okay = True

        _page.name = _new_name
        self._notebook.SetPageText(self._notebook.GetSelection(), _new_name)



    def OnDeleteAssembly(self, event):
        ''' Veto if page being deleted is only one... '''
        if self._notebook.GetPageCount() <= 1:
            print('Cannot delete only assembly')
            return

        _selection = self._notebook.GetSelection()
        _page = self._notebook.GetPage(_selection)

        # Delete notebook page, correponding assembly object and dictionary entry
        self._notebook.DeletePage(_selection)
        _assembly = self.assembly_manager[_page]
        del self.assembly_manager[_page]
        del _assembly

        self.AddText('Assembly deleted')

        # _dialog = self.DoNothingDialog(event = None, text= '6 issues found in 2 assemblies', message = 'Change report')



    @property
    def assembly_list(self):
        try:
            _list = [el.name for el in self.assembly_manager]
        except:
            print('Exception while trying to populate assembly list')
            _list = []

        return _list



    def GetFilename(self, dialog_text = "Open file", starter = None, ender = None):

        ### General file-open method; takes list of file extensions as argument
        ### and can be used for specific file names ("starter", string)
        ### or types ("ender", string or list)

        # Convert "ender" to list if only one element
        if isinstance(ender, str):
            ender = [ender]

        # Check that only one argument is present
        # Create text for file dialog
        if starter is not None and ender is None:
            file_open_text = starter.upper() + " files (" + starter.lower() + "*)|" + starter.lower() + "*"
        elif starter is None and ender is not None:
            file_open_text = [el.upper() + " files (*." + el.lower() + ")|*." + el.lower() for el in ender]
            file_open_text = "|".join(file_open_text)
        else:
            raise ValueError("Requires starter or ender only")

        # Create file dialog
        fileDialog = wx.FileDialog(self, dialog_text, "", "",
                                   file_open_text,
                                   wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        fileDialog.ShowModal()
        filename = fileDialog.GetPath()
        fileDialog.Destroy()

        # Return file name, ignoring rest of path
        return filename



    def OnFileOpen(self, event = None):

        # Get STEP filename
        open_filename = self.GetFilename(ender = ["stp", "step"]).split("\\")[-1]

        # Return if filename is empty, i.e. if user selects "cancel" in file-open dialog
        if not open_filename:
            print('File not found')
            return
        else:
            print('Trying to load file...')

        # Wipe existing assembly if one already loaded; replace with empty one
        if self._active.file_open:
            _page = self._notebook.GetPage(self._notebook.GetSelection())
            _old = self.assembly_manager[_page]
            self.assembly_manager[_page] = MyParse()
            self.assembly = self.assembly_manager[_page]
            del _old

        # Load data, create nodes and edges, etc.
        self.assembly.load_step(open_filename)
        self.assembly.create_tree()
        self.assembly.set_node_positions()

        # OCC 3D data returned here
        self.assembly.OCC_read_file(open_filename)
        print('Loaded 3D data...')

        # "File is open" tag
        if not self._active.file_open:
            self._active.file_open = True
            self._active.Enable()



        # Show parts list and lattice
        self.DisplayPartsList()

        # Clear selector window if necessary
        try:
            self._active.slct_sizer.Clear(True)
        except:
            pass

        # Clear lattice plot if necessary
        try:
            self.latt_axes.clear()
        except:
            pass

        # Display lattice and start 3D viewer data structure
        self.DisplayLattice(set_pos = False)
        self.Update3DView(self.selected_items)



    def DisplayPartsList(self):

        print('Running DisplayPartsList')
        # Check if file loaded previously
        try:
            self._active.partTree_ctc.DeleteAllItems()
        except:
            pass

        # Create root node...
        root_id = self.assembly.get_root()
        print('Found root:', root_id)
        text = self.assembly.nodes[root_id]['text']
        label = self.assembly.nodes[root_id]['label']

        ctc_root_item = self._active.partTree_ctc.AddRoot(text = text, ct_type = 1, data = {'id_': root_id, 'sort_id': root_id, 'label': label})

        self._active.ctc_dict     = {}
        self._active.ctc_dict_inv = {}

        self._active.ctc_dict[root_id] = ctc_root_item
        self._active.ctc_dict_inv[ctc_root_item] = root_id

        # ...then all others
        # tree_depth = nx.dag_longest_path_length(self.assembly, root_id)
        tree_depth = nx.dag_longest_path_length(self.assembly)

        for i in range(tree_depth + 1)[1:]:
            for node in self.assembly.nodes:
                depth = nx.shortest_path_length(self.assembly, root_id, node)

                if depth == i:
                    parent_id = [el for el in self.assembly.predecessors(node)][-1]
                    print('Parent ID:', parent_id)
                    ctc_parent = self._active.ctc_dict[parent_id]

                    # Text and label will differ if changed previously by user in parts view
                    label = self.assembly.nodes[node]['label']
                    text = self.assembly.nodes[node]['text']

                    print('Node: ', node)
                    ctc_item = self._active.partTree_ctc.AppendItem(ctc_parent, text = text, ct_type = 1, data = {'id_': node, 'sort_id': node, 'label': label})

                    self._active.ctc_dict[node]         = ctc_item
                    self._active.ctc_dict_inv[ctc_item] = node



        self._active.partTree_ctc.ExpandAll()

        # Sort all tree items
        self._active.partTree_ctc.SortAllChildren(self._active.partTree_ctc.GetRootItem())

        print('Running DisplayPartsList')




    '''Propagate user selections in 3D view to all views'''
    def OnLeftUp_3D(self, event):
        # Pass event to Viewer3D class (goes via Select or SelectArea)
        self._active.occ_panel.OnLeftUp(event)

        # Grab selected parts in 3D view
        print('Getting selected part(s) from 3D view...')
        _shapes = self._active.occ_panel._display.selected_shapes

        if not _shapes:
            return

        _already_selected = self.selected_items

        # Get IDs of 3D shapes
        _to_update = []
        print('IDs of item(s) selected:')
        for shape in _shapes:
            # Inverse dict look-up
            _id = [k for k,v in self.assembly.OCC_dict.items() if v == shape][-1]
            _to_update.append(_id)
            print(_id)

        # Check if CTRL key pressed; if so, append selected items to existing
        # GetModifiers avoids problems with different keyboard layouts...
        # ...but is equivalent to ControlDown, see here:
        # https://wxpython.org/Phoenix/docs/html/wx.KeyboardState.html#wx.KeyboardState.ControlDown
        if event.GetModifiers() == wx.MOD_CONTROL:
            print('CTRL held during 3D selection; appending selected item(s)...')
            _to_update = set(_to_update)
            print('To select item(s):', _to_update)
            _to_update.update(_already_selected)
            _to_update = list(_to_update)

        # Freeze (and later thaw) to stop flickering while updating all views
        self.Freeze()

        # Update parts view
        print('Updating parts view...')
        '''
        self.veto is workaround to avoid ctc.EVT_TREE_SEL_CHANGED event...
        firing for each part selected
        '''
        self.veto = True
        self._active.partTree_ctc.UnselectAll()
        for _id in _to_update:
            self.UpdateListSelections(_id)
        self.veto = False

        # Update other views
        self.UpdateToggledImages()
        self.UpdateSelectedNodes()
        self.Update3DView()

        self.Thaw()



    def Update3DView(self, items = None):

        '''
        transparency = None:    shaded
        transparency = 1:       wireframe
        '''
        def display_part(part, transparency = None):
            # if part in self.assembly.OCC_dict:
            shape = self.assembly.OCC_dict[part]
            label, c = self.assembly.shapes[shape]
            ais_shape = self._active.occ_panel._display.DisplayShape(shape,
                                                                     color = Quantity_Color(c.Red(),
                                                                                            c.Green(),
                                                                                            c.Blue(),
                                                                                            Quantity_TOC_RGB),
                                                                     transparency = transparency)

        self._active.occ_panel._display.EraseAll()

        ''' Display parts as shaded if selected, transparent/wireframe if not '''
        selected_items = self.selected_items
        for item in self.assembly.OCC_dict:
            if item in selected_items:
                display_part(item)
            else:
                display_part(item, transparency = 1)

        self._active.occ_panel._display.View.FitAll()
        self._active.occ_panel._display.View.ZFitAll()
        print('Done "Update3DView"')



    def ScaleImage(self, img, target_w = None, scaling = 0.95):

        ''' Default: target width is that of selector view holding image '''
        if target_w == None:
            target_w  = self.tight * self._active.slct_panel.GetSize()[0]/self._active.image_cols

        w, h = img.GetSize()

        if h/w > 1:
            h_new = target_w
            w_new = h_new*w/h
        else:
            w_new = target_w
            h_new = w_new*h/w

        # Rescale
        img = img.Scale(w_new, h_new, wx.IMAGE_QUALITY_HIGH)

        return img



    def get_node_colours(self, return_list = True):

        selected_items = self.selected_items

        # List version of node colours based on which are selected in parts view
        if return_list:
            node_colours = [self.selected_colour if node in selected_items else self.default_colour for node in self.assembly.nodes]

        # Dictionary version (in case useful in future)
        else:
            node_colours = {node:(self.selected_colour if node in selected_items else self.default_colour) for node in self.assembly.nodes}

        return node_colours



    def DisplayLattice(self, set_pos = True, assembly = None):


        print('Running DisplayLattice')

        if set_pos:
            self.assembly.set_node_positions()

        pos = self.assembly.get_positions()[0]
        print('Got positions')

        colour_map = self.get_node_colours(return_list = False)
        print('Got colour map')

        try:
            self.latt_axes.cla()
            print('Cleared axes')
        except:
            pass

        # Draw to lattice panel figure
        # nx.draw(self.assembly, pos, node_color = colour_map, with_labels = True, ax = self.latt_axes)

        ## -----------------------------------------------
        ## HR 20/05/20
        ## Alternative lattice plot routine in Hasse-like format

        # Draw outline of each level, with end point
        self.assembly.line_dict = {}
        for k,v in self.assembly.S_p.items():

            # comb_ = np.log(comb(max_,el))
            if v <= 1:
                line_pos = 0
            else:
                line_pos = 0.5*np.log(v-1)
            self.assembly.line_dict[k] = self.latt_axes.plot([-line_pos, line_pos], [k, k], c = 'gray', marker = 'o', mfc = 'gray', mec = 'gray', zorder = -1)

        # Draw nodes
        self.assembly.node_dict = {}
        for node in self.assembly.nodes:
            self.assembly.node_dict[node] = self.latt_axes.scatter(pos[node][0], pos[node][1], c = colour_map[node], zorder = 1)

        # Draw edges
        self.assembly.edge_dict = {}
        for u,v in self.assembly.edges:
            self.assembly.edge_dict[(u,v)] = self.latt_axes.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], c = 'red', zorder = 0)

        # Create edges b/t infimum and leaves
        origin = (0,0)
        # Here set v in edge (u,v) to None if v is infimum
        for leaf in self.assembly.leaves:
            self.assembly.edge_dict[(leaf, None)] = self.latt_axes.plot([origin[0], pos[leaf][0]], [origin[1], pos[leaf][1]], c = 'red', zorder = 0)

        ## -----------------------------------------------



        # Minimise white space around plot in panel
        self.latt_figure.subplots_adjust(left = 0.01, bottom = 0.01, right = 0.99, top = 0.99)

        # try:
        #     self.latt_axes.set_xlim(self.latt_plotlims[0])
        #     self.latt_axes.set_ylim(self.latt_plotlims[1])
        # except:
        #     pass

        print('Finished "DisplayLattice"')
        self.DoDraw('DisplayLattice')



    def DoDraw(self, called_by = None):

        if called_by:
            print('DoDraw called by ', called_by)

        self.latt_axes.axes.axis('off')
        self.latt_axes.axes.get_xaxis().set_ticks([])
        self.latt_axes.axes.get_yaxis().set_ticks([])

        # Show lattice figure
        self.latt_canvas.draw()
        print('Done "draw"')

        self.latt_canvas.Show()
        print('Done canvas "Show"')

        self.latt_tb.Show()
        print('Done toolbar "Show"')

        # Update lattice panel layout
        self.latt_panel.Layout()
        print('Done layout')




    def OnRightClick(self, event):

        # HR 5/3/20 SOME DUPLICATION HERE WITH OPERATION-SPECIFIC METHOD, E.G. "ONFLATTEN"
        # IN TERMS OF FILTERING/SELECTION OF OPTIONS BASED ON SELECTED ITEM TYPE/QUANTITY

        # HR 5/3/20 SHOULD ADD CHECK HERE THAT MOUSE CLICK IS OVER A SELECTED ITEM
        # pos = event.GetPosition()

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # POPUP MENU (WITH BINDINGS) UPON RIGHT-CLICK IN PARTS VIEW
        # ---
        menu = wx.Menu()
        menu_item = menu.Append(wx.ID_ANY, 'Change item and get all affected', 'Change item property and find affected parts in all assemblies')
        self.Bind(wx.EVT_MENU, self.OnChangeItemProperty, menu_item)


        # FILTERING OF ITEM TYPES -> PARTICULAR POP-UP MENU OPTIONS
        # ---
        # Single-item options
        if len(selected_items) == 1:
            # id_ = self._active.ctc_dict_inv[selected_items[-1]]
            id_ = selected_items[-1]
            # Part options
            if id_ in self.assembly.leaves:
                menu_item = menu.Append(wx.ID_ANY, 'Disaggregate', 'Disaggregate part into parts')
                self.Bind(wx.EVT_MENU, self.OnDisaggregate, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Remove part', 'Remove part')
                self.Bind(wx.EVT_MENU, self.OnRemoveNode, menu_item)
            # Assembly options
            else:
                menu_item = menu.Append(wx.ID_ANY, 'Flatten', 'Flatten assembly')
                self.Bind(wx.EVT_MENU, self.OnFlatten, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Aggregate', 'Aggregate assembly')
                self.Bind(wx.EVT_MENU, self.OnAggregate, menu_item)
                menu_item = menu.Append(wx.ID_ANY, 'Add node', 'Add node to assembly')
                self.Bind(wx.EVT_MENU, self.OnAddNode, menu_item)
                # Sorting options
                menu_text = 'Sort children alphabetically'
                menu_item = menu.Append(wx.ID_ANY, menu_text, menu_text)
                self.Bind(wx.EVT_MENU, self.OnSortAlpha, menu_item)
                menu_text = 'Sort children by unique ID'
                menu_item = menu.Append(wx.ID_ANY, menu_text, menu_text)
                self.Bind(wx.EVT_MENU, self.OnSortByID, menu_item)

        # Multiple-item options
        elif len(selected_items) > 1:
            menu_item = menu.Append(wx.ID_ANY, 'Assemble', 'Form assembly from selected items')
            self.Bind(wx.EVT_MENU, self.OnAssemble, menu_item)
            menu_item = menu.Append(wx.ID_ANY, 'Remove parts', 'Remove parts')
            self.Bind(wx.EVT_MENU, self.OnRemoveNode, menu_item)

        # Create popup menu at current mouse position (default if no positional argument passed)
        self.PopupMenu(menu)
        menu.Destroy()



    def OnChangeItemProperty(self, event):
        _selected = self.selected_items
        for item in _selected:
            tree_item = self._active.ctc_dict[item]
            self._active.partTree_ctc.SetItemTextColour(tree_item, self._highlight_colour)
        print('Changing item property and finding affected items...')



    @property
    def selected_items(self):

        '''
        Get items selected in parts view using GetSelections() rather than maintaining list
        b/c e.g. releasing ctrl key during multiple selection
        means not all selections are tracked easily '''

        try:
            _selected_items = [self._active.ctc_dict_inv[item] for item in self._active.partTree_ctc.GetSelections()]
            return _selected_items
        except AttributeError('No items selected'):
            return None

    @selected_items.setter
    def selected_items(self, items):
        if type(items) is list:
            self.selected_items = items
        else:
            print('Selected items not reset: items must be list')



    def render_by_id(self, id_):

        image_saved_ok = False
        self.renderer.EraseAll()

        ''' Get all parts in assembly, including assembly '''
        children = nx.descendants(self.assembly, id_)
        children.add(id_)
        if not children:
            print('No items to render')
            return None

        print('Children = ', children)

        ''' Render each item, if OCC data exists for it in OCC_dict '''
        for child in children:
            if child in self.assembly.OCC_dict:
                shape = self.assembly.OCC_dict[child]
                label, c = self.assembly.shapes[shape]
                print('Rendering shape for item', child)
                self.renderer.DisplayShape(shape, color = Quantity_Color(c.Red(),
                                                                         c.Green(),
                                                                         c.Blue(),
                                                                         Quantity_TOC_RGB))
            else:
                print('Cannot render item ', child, ' as not present as CAD model')

        try:
            img_name = self.get_image_name(id_)
            print('Fitting and dumping image ', img_name)
            # Create directory if it doesn't already exist
            img_path = os.path.split(img_name)[0]
            if not os.path.isdir(img_path):
                os.mkdir(img_path)

            self.renderer.View.FitAll()
            self.renderer.View.ZFitAll()
            self.renderer.View.Dump(img_name)
            # Check if rendered and dumped, i.e. if image file exists
            if os.path.exists(img_name):
                image_saved_ok = True

        except Exception as e:
            print('Could not dump image to file; exception follows')
            print(e)

        return image_saved_ok



    def get_image_name(self, _id, suffix = '.jpg'):
        ''' Image file type and "suffix" here (jpg) is dictated by python-occ "Dump" method 
            which can't be changed without delving into C++ '''
        full_name = os.path.join(self.im_path, str(self.assembly._id), str(_id)) + suffix
        print('Full path of image to fetch:\n', full_name)

        return full_name



    def TreeItemChecked(self, event):

        ''' Always return something! '''
        def get_image(id_):

            print('Getting image...')
            print('ID = ', id_)
            img = None
            img_name = None

            ''' Check if ID has CAD data, which is the case if it comes from STEP file...
                If not, check if any descendants have CAD data, in which case send to renderer...
                which also finds those descendants '''
            if id_ not in self.assembly.step_dict:
                if id_ in self.assembly.leaves:
                    print('Item is leaf')
                    img_name = self.no_image_part
                else:
                    print('Item is assembly')
                    descendants = nx.descendants(self.assembly, id_)
                    _to_render = []
                    for item in descendants:
                        if item in self.assembly.step_dict:
                            _to_render.append(item)
                    # If _to_render isn't empty, then render
                    print('To render: ', _to_render)
                    if _to_render:
                        if self.render_by_id(id_):
                            img_name = self.get_image_name(id_)
                            print('Image name from parts in subassembly:', img_name)
                        else:
                            img_name = self.no_image_ass
                    else:
                        img_name = self.no_image_ass

            # ...else if it does have a CAD model, create image of all contained parts
            else:
                ''' Just render image each time, don't check for existing image file...
                    as parts contained by item may change and not be shown in saved image '''
                if self.render_by_id(id_):
                    img_name = self.get_image_name(id_)
                else:
                    if id_ in self.assembly.leaves:
                        img_name = self.no_image_part
                    else:
                        img_name = self.no_image_ass

            ''' Ultimately "img" here is from either:
                1. "no_image_<part or ass>" -> ConvertToImage(), or
                2. Image file just created  -> Image() '''
            if img_name:
                try:
                    img = wx.Image(img_name, wx.BITMAP_TYPE_ANY)
                    print('Image from file: ', img_name)
                except:
                    img = img_name.ConvertToImage()
                    print('Image from bitmap object: ', img_name)
            return img



        # Get checked item and search for corresponding image
        item = event.GetItem()
        id_  = self._active.ctc_dict_inv[item]

        selected_items = self.selected_items

        if item.IsChecked():
            ''' Get image; method always returns something '''
            img = get_image(id_)

            # Create/add button in slct_panel
            #
            # 1/ Start with null image...
            button = wx.BitmapToggleButton(self._active.slct_panel)
            button.SetBackgroundColour('white')
            self._active.slct_sizer.Add(button, 1, wx.EXPAND)
            # 2/ Add image after computing size and rescaling
            button.SetBitmap(wx.Bitmap(self.ScaleImage(img)))

            # Update global list and dict
            #
            # Data is list, i.e. same format as "selected_items"
            # but ctc lacks "get selections" method for checked items
            self._active.button_dict[id_]         = button
            self._active.button_dict_inv[button]  = id_
            self._active.button_img_dict[id_]     = img

            # Toggle if already selected elsewhere
            if id_ in selected_items:
                button.SetValue(True)
            else:
                pass

        else:
            # Remove button from slct_panel
            button = self._active.button_dict[id_]
            button.Destroy()

            # Update global list and dict
            self._active.button_dict.pop(id_)
            self._active.button_dict_inv.pop(button)
            self._active.button_img_dict.pop(id_)

        self._active.slct_panel.SetupScrolling(scrollToTop = False)



    def TreeItemSelected(self, event):

        '''
        Don't execute if raised by 3D view selection...
        as would redo for every selected item
        '''
        if self.veto:
            print('Vetoing')
            event.Veto()
            return

        print('Tree item selected, updating selector, lattice and 3D views...')
        # Update images and lattice view
        self.UpdateToggledImages()
        self.UpdateSelectedNodes()
        self.Update3DView(self.selected_items)



    def ImageToggled(self, event):

        print('Image toggled')
        id_ = self._active.button_dict_inv[event.GetEventObject()]
        self.UpdateListSelections(id_)



    def GetLattPos(self, event):

        print('GetLattPos')

        # print('%s: button = %d, x = %d, y = %d, xdata = %f, ydata = %f' %
        #       ('Double click' if event.dblclick else 'Single click', event.button,
        #        event.x, event.y, event.xdata, event.ydata))

        # Get position and type of click event
        self.click_pos = (event.xdata, event.ydata)
        # print('Click_position = ', self.click_pos)



    def OnLatticeMouseRelease(self, event):

        print('OnLatticeMouseRelease')

        # Tolerance for node/line picker; tweak if necessary
        picker_tol = len(self.assembly.leaves)/100

        # Retain zoom settings for later
        self.latt_plotlims = (self.latt_axes.get_xlim(), self.latt_axes.get_ylim())
        # print('Plot limits: ', self.latt_plotlims)

        # If right-click event, then use pop-up menu...
        if event.button == 3:
            self.OnRightClick(event)
            return

        # ...otherwise select item
        # ---
        # Functor to find nearest value in sorted list
        # ---
        # HR 4/3/20 THIS SHOULD BE REWRITTEN COMPLETELY TO USE MPL PICKER/ARTIST FUNCTIONALITY
        def get_nearest(value, list_in):

            # print('list_in = ', list_in)
            # First check if value beyond upper bound
            if value > list_in[-1]:
                print('case 1: beyond upper bound')
                answer = list_in[-1]

            else:
                for i,el in enumerate(list_in):
                    if value < el:

                        # Then check if below lower bound
                        if i == 0:
                            print('case 2: below lower bound')
                            answer = list_in[0]
                            break

                        # All other cases: somewhere in between
                        else:
                            print('case 3: intermediate')
                            if abs(value - el) < abs(value - list_in[i-1]):
                                answer = el
                            else:
                                answer = list_in[i-1]
                            break

            return answer

        # Check that click and release are in same position
        # as FigureCanvas also allows dragging to move plot position
        if event.xdata == self.click_pos[0] and event.ydata == self.click_pos[1]:

            # Get nearest y value (same as lattice level)
            y_list = self.assembly.levels_p_sorted[:]
            # Must prepend lattice level of single part to list
            y_list.insert(0, self.assembly.part_level)
            y_  = get_nearest(event.ydata, y_list)
            print('y_list = ', y_list)
            print('y_     = ', y_)

            # Get nearest x value within known y level
            # x_dict = {self.assembly.nodes[el]['x']:el for el in self.assembly.nodes if self.assembly.nodes[el]['n_p'] == y_}
            x_all  = self.assembly.levels_dict[y_]
            x_dict = {self.assembly.nodes[el]['x']:el for el in x_all}
            x_list = sorted([k for k,v in x_dict.items()])
            x_  = get_nearest(event.xdata, x_list)
            print('x_list = ', x_list, '\n')
            print('x_dict = ', x_dict, '\n')
            print('x_     = ', x_, '\n')

            # Get nearest node
            id_ = x_dict[x_]

            print('Nearest node: x = %f, y = %f; node ID: %i\n' %
                  (x_, y_, id_))



            ##############################

            ## HR 1/6/20 Added calculation of distance nearest node + tolerance
            ## If outside tolerance, ignore nodes
            ## and generate point on nearest line instead
            ## then unrank and generate alternative assembly

            x_dist = event.xdata - x_
            y_dist = event.ydata - y_
            dist = np.sqrt(x_dist**2 + y_dist**2)

            print('x_dist = %f, y_dist = %f, dist = %f' % (x_dist, y_dist, dist))

            # If too far from any node, get alternative assembly by unranking position
            if dist > picker_tol:
                print('Outside tolerance, getting position on nearest line')

                list_ = [el for el in range(len(self.assembly.leaves)+1)]
                y__ = get_nearest(event.ydata, list_)


                self.OnNewNodeClick(y__, event.xdata)
                return

            print('Inside tolerance, (de)selecting nearest node')

            ##############################



            # Update items in parts list
            self.UpdateListSelections(id_)

            # Update node in lattice view
            # self.UpdateSelectedNodes(id_)

            selected_items = self.selected_items
            if id_ in selected_items:
                self.assembly.node_dict[id_].set_facecolor(self.selected_colour)
            else:
                self.assembly.node_dict[id_].set_facecolor(self.default_colour)

            # if not self.drawn:
            #     self.DoDraw('OnLatticeMouseRelease')
            self.DoDraw('OnLatticeMouseRelease')



    ## HR 1/6/20 abandoned OnNodePick as MPL generates pick_event for every artist within pick radius
    ## Leaving here for reference

    # def OnNodePick(self, event):

    #     print('OnNodePick')

    #     # N.B. MPL generates a pick event for EVERY artist at the click point!

    #     event.artist.set_color('green')

    #     # Get node ID from artist object (i.e. reverse dictionary lookup)
    #     if event.artist in self.node_dict.values():
    #         print('Found artist in node_dict!')
    #         id_ = next(node for node, artist in self.assembly.node_dict.items() if event.artist == artist)
    #     elif event.artist in self.line_dict.values():
    #         print('Found artist in line dict!')
    #         id_ = next(line for line, artist in self.line_dict.items() if event.artist == artist)
    #     else:
    #         id_ = None

    #     print('ID = ', id_)
    #     print('Artist = ', event.artist)
    #     print('Event index = ', event.ind)



    def UpdateLatticeView(self, event = None):

        for assembly in self.assembly_manager:
            pass



    def OnNewNodeClick(self, y_, x_):

        print('Creating new nodes and edges by unranking')

        # Ref to alternative assembly for ease of reading
        # ---------------------
        # ass = self.assembly
        # alt = self.assembly.alt
        ax  = self.latt_axes
        # ---------------------

        try:
            # Remove MPL plot objects corresponding to alternative nodes and edges...
            # ...if they exist
            if self.assembly.alt.node_dict:
                for k,v in self.assembly.alt.node_dict.items():
                    # Remove from plot (MPL)
                    v.remove()

            if self.assembly.alt.edge_dict:
                for k,v in self.assembly.alt.edge_dict.items():
                    # Remove from plot (MPL)
                    v.remove()
            self.assembly.alt.clear()
        except:
            pass



        n = len(self.assembly.leaves)

        S     = self.assembly.S_p[y_]
        width = np.log(S-1)
        rank  = int(round(((x_/width) + 0.5)*(S-1)))
        print('rank = ', rank)

        # Quantise x_ to be at position of rank
        x_quant = ((rank/(S-1))-0.5)*np.log(S-1)

        _parts  = self.assembly.unrank(n, y_, rank)



        # Create and populate alternative assembly
        _node_one = self.assembly.new_id
        _node_two = _node_one + 1

        _parts_ids = [self.assembly.leaf_dict_inv[el] for el in _parts]
        _others_ids = list(self.assembly.leaves - set(_parts_ids))

        # ...and also create second node containing all other leaves, for illustration
        _others = [self.assembly.leaf_dict[el] for el in _others_ids]

        _y_others = len(_others_ids)
        S_others = self.assembly.S_p[_y_others]

        _others_rank = self.assembly.rank(_others)
        _x_others = ((_others_rank/(S_others-1))-0.5)*np.log(S_others-1)

        ## NX 1. Create and populate data of two new nodes



        ## ------------------------

        ### TO TRY COPYING ASSEMBLY AND REMOVING/ADDING ONLY THOSE NODES NECESSARY
        ### TO AVOID OPTIMAL_EDIT_PATHS TAKING SEVERAL MINUTES!

        self.assembly.alt = self.assembly.copy()
        # alt = self.assembly.alt

        # Remove unwanted edges between root and leaves
        _root = self.assembly.get_root()
        _leaves = self.assembly.leaves
        # _edges_to_remove = [(u,v) for u,v in alt.edges if u == alt_root and v in leaves]
        # # # _edges_to_remove = [(u,v) for u,v in alt.edges]
        # for edge in _edges_to_remove:
        #     alt.remove_edge(edge)

        nodes_to_remove = [node for node in self.assembly.nodes if node not in _leaves and node != _root]
        self.assembly.alt.remove_nodes_from(nodes_to_remove)

        self.assembly.alt.remove_edges_from(list(self.assembly.alt.edges))

        self.assembly.alt.add_edge(_root,_node_one)
        for leaf in _parts_ids:
            self.assembly.alt.add_edge(_node_one,leaf)

        self.assembly.alt.add_edge(_root,_node_two)
        for leaf in _others_ids:
            self.assembly.alt.add_edge(_node_two,leaf)

        ### ------------------------



        self.assembly.alt.nodes[_node_one]['x']     = x_quant
        self.assembly.alt.nodes[_node_one]['n_p']   = y_
        self.assembly.alt.nodes[_node_one]['n_a']   = y_ + 1
        self.assembly.alt.nodes[_node_one]['parts'] = _parts_ids

        self.assembly.alt.nodes[_node_two]['x']     = _x_others
        self.assembly.alt.nodes[_node_two]['n_p']   = _y_others
        self.assembly.alt.nodes[_node_two]['n_a']   = _y_others + 1
        self.assembly.alt.nodes[_node_two]['parts'] = _others_ids

        self.assembly.alt.node_dict = {}
        self.assembly.alt.edge_dict = {}



        # # ## NX 2. ...copy data to new leaf nodes and root in new assembly...

        # # leaves_and_supremum = list(leaves) + [ass.get_root()]

        # # for _node in leaves_and_supremum:
        # #     alt.add_node(_node)
        # #     for _k,_v in ass.nodes[_node].items():
        # #         alt.nodes[_node][_k] = _v

        # ## NX 3. ...draw edges b/t first new node and its leaves...
        # for leaf in ass.leaves:
        #     alt.add_edge(_node_one, leaf)

        # ## NX 4. ...then b/t second new node and its leaves...
        # for _leaf in _others_ids:
        #     alt.add_edge(_node_two,_leaf)

        # ## NX 4. ...then edges between root and two new nodes
        # alt.add_edge(root,_node_one)
        # alt.add_edge(root,_node_two)

        # for u,v in old_edges:
        #     self.assembly.alt.remove_edge(u,v)

        # Get positions and populate dictionary of MPL objects
        self.assembly.alt.set_node_positions()
        pos_nodes, pos_edges = self.assembly.alt.get_positions()

        for node in self.assembly.alt.nodes:
            pos = pos_nodes[node]
            self.assembly.alt.node_dict[node] = ax.scatter(pos[0], pos[1], c = self.alt_colour, zorder = 0)


        ## HR 17/6/20
        ## MAJOR NOTE: NO EDGES FROM ORIGINAL ASSEMBLY ARE REMOVED AS DOING THAT BREAKS NX'S OPTIMAL_EDIT_PATHS
        ## AND CAUSES IT TO SLOW DOWN SEVERELY
        ## INSTEAD RETAIN THEM AND VARY COLOUR

        for edge in self.assembly.alt.edges:
            pos = pos_edges[edge]
            # if edge in self.assembly.edges:
            #     c = self.default_colour
            # else:
            #     c = self.alt_colour
            self.assembly.alt.edge_dict[edge] = ax.plot([pos[0][0], pos[1][0]], [pos[0][1], pos[1][1]], c = self.alt_colour, zorder = 0)[0]

        self.DoDraw('OnNewNodeClick')



    def UpdateSelectedNodes(self, nodes = None):

        if not nodes:
            nodes = self.selected_items
        elif type(nodes) == int:
            nodes = [nodes]

        nodes_not = self.assembly.nodes - nodes

        # Update selected nodes
        for node in nodes:
            self.assembly.node_dict[node].set_facecolor(self.selected_colour)
        # Update unselected nodes
        for node in nodes_not:
            self.assembly.node_dict[node].set_facecolor(self.default_colour)

        self.DoDraw('UpdateSelectedNodes')



    def UpdateListSelections(self, id_):

        # Select/deselect parts list item
        # With "select = True", SelectItem toggles state if multiple selections enabled
        self._active.partTree_ctc.SelectItem(self._active.ctc_dict[id_], select = True)



    def UpdateToggledImages(self):

        for id_, button in self._active.button_dict.items():
            button.SetValue(False)

        selected_items = self.selected_items

        for id_ in selected_items:
            if id_ in self._active.button_dict:
                button = self._active.button_dict[id_]
                button.SetValue(True)
            else:
                pass



    # def create_new_id(self):

    #     # Get new item ID that is greater than largest existing ID
    #     try:
    #         id_ = max([el for el in self.assembly.nodes] + [el_ for el_ in self._active.discarded.nodes]) + 1
    #     except AttributeError:
    #         try:
    #             id_ = max([el for el in self.assembly.nodes]) + 1
    #         except AttributeError:
    #             return 0
    #     return id_



    def OnTreeCtrlChanged(self):

        print('Running OnTreeCtrlChanged')
        # Remake parts list and lattice
        # HR 17/02/2020 CAN BE IMPROVED SO ONLY AFFECTED CTC AND LATTICE ITEMS MODIFIED
        self.DisplayPartsList()
        self.DisplayLattice()



    def OnAssemble(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # Further checks
        if len(selected_items) > 1:
            print('Selected items to assemble:\n')
            for id_ in selected_items:
                print('\nID = ', id_)
        else:
            print('Cannot assemble: no items or only one item selected\n')
            return

        # Check root is not present in selected items
        if self.assembly.get_root() in selected_items:
            print('Cannot create assembly: items to assemble include root')
            return



        # MAIN "ASSEMBLE" ALGORITHM
        # ---
        # Get selected item that is highest up tree (i.e. lowest depth)
        depths = {}
        for id_ in selected_items:
            depths[id_] = self.assembly.get_node_depth(id_)
            print('ID = ', id_, '; parent depth = ', depths[id_])
        highest_node = min(depths, key = depths.get)
        new_parent = self.assembly.get_parent(highest_node)
        print('New parent = ', new_parent)

        # Get valid ID for new node then create
        new_id   = self.assembly.new_id
        text = self.new_assembly_text
        self.assembly.add_node(new_id, text = text, label = text)
        self.assembly.add_edge(new_parent, new_id)

        # Move all selected items to be children of new node
        for id_ in selected_items:
            self.assembly.move_node(id_, new_id)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()
        self.Update3DView()



    def OnFlatten(self, event):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of item to flatten = ', id_)
            else:
                print('Cannot flatten: item is a leaf node/irreducible part\n')
                return
        else:
            print('Cannot flatten: more than one item selected\n')
            return



        # MAIN "FLATTEN" ALGORITHM
        # ---
        # Get all children of item
        children_ = nx.descendants(self.assembly, id_)
        children_parts = [el for el in children_ if el in leaves]
        print('Children parts = ', children_parts)
        children_ass = [el for el in children_ if not el in leaves]
        print('Children assemblies = ', children_ass)

        # Move all children that are indivisible parts
        for child in children_parts:
            self.assembly.move_node(child, id_)

        # Delete all children that are assemblies
        for child in children_ass:
            successors = self.assembly.successors(child)
            parent     = self.assembly.get_parent(child)
            # self._active.discarded.add_node(child)
            # # Add immediate children to data of discarded node for future reconstruction
            # self._active.discarded.nodes[child]['flatten_children'] = successors
            # self._active.discarded.nodes[child]['flatten_parent']   = parent
            # self.assembly.remove_node(child)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnDisaggregate(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ in leaves:
                print('ID of item to disaggregate = ', id_)
            else:
                print('Cannot disaggregate: item is not a leaf node/irreducible part\n')
                return
        else:
            print('Cannot disaggregate: no or more than one item selected\n')
            return



        # MAIN "DISAGGREGATE" ALGORITHM
        # ---
        # Get valid ID for new node then create
        no_disagg = 2
        for i in range(no_disagg):
            new_id   = self.assembly.new_id
            text = self.new_part_text
            self.assembly.add_node(new_id, text = text, label = text)
            self.assembly.add_edge(id_, new_id)

            print('New assembly ID = ', new_id)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnAggregate(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of item to aggregate = ', id_)
            else:
                print('Cannot aggregate: item is a leaf node/irreducible part\n')
                return
        else:
            print('Cannot aggregate: more than one item selected\n')
            return



        # MAIN "AGGREGATE" ALGORITHM
        # ---
        # Get children of node and remove
        children_ = [el for el in self.assembly.successors(id_)]
        print('Children aggregated: ', children_)
        for child in children_:
            # Get subgraph and add recreate in discard pile
            subgraph = nx.dfs_tree(self.assembly, child)
            # self._active.discarded.add_nodes_from(subgraph.nodes)
            # self._active.discarded.add_edges_from(subgraph.edges)
            ## Delete from assembly
            self.assembly.remove_nodes_from(subgraph.nodes)

        # Add list of children IDs as data for future reference
        self.assembly.nodes[id_]['aggregated'] = children_

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnAddNode(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        leaves = self.assembly.leaves

        # Further checks
        if len(selected_items) == 1:
            # id_ = self._active.ctc_dict_inv[selected_items[-1]]
            # if id_ not in leaves:
            #     print('ID of item to add node to = ', id_)
            id_ = selected_items[-1]
            if id_ not in leaves:
                print('ID of items to add not to = ', id_)
            else:
                print('Cannot add node: item is a leaf node/irreducible part\n')
                print('To add node, disaggregate part first\n')
                return
        else:
            print('Cannot add node: more than one item selected\n')
            return



        # MAIN "ADD NODE" ALGORITHM
        # ---
        # Create new node with selected item as parent
        new_id = self.assembly.new_id
        text = self.new_part_text
        self.assembly.add_node(new_id, text = text, label = text)
        self.assembly.add_edge(id_, new_id)

        print('New node ID = ', new_id)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnRemoveNode(self, event = None):

        selected_items = self.selected_items

        # Check selected items are present and suitable
        if not selected_items:
            print('No items selected')
            return

        # Further checks
        if len(selected_items) >= 1:
            print('Selected item(s) to remove:\n')
            for id_ in selected_items:
                # id_ = self._active.ctc_dict_inv[item]
                # print('ID = ', id_)
                # self.selected_list.append(id_)
                print('ID = ', id_)
        else:
            print('Cannot remove: no items selected\n')
            return

        # Check root is not present in selected items
        _root = self.assembly.get_root()
        if _root in selected_items:
            if len(selected_items) == 1:
                print('Cannot remove root')
                return
            else:
                print('Cannot remove root; removing other selected nodes')
                selected_items.remove(_root)



        # MAIN "REMOVE NODE" ALGORITHM
        # ---
        ## Get all non-connected nodes in list...
        dependants_removed = self.assembly.remove_dependants_from(selected_items)
        # ...then create subtree and copy it to discard pile...
        for node in dependants_removed:
            subgraph = nx.dfs_tree(self.assembly, node)
            parent   = self.assembly.get_parent(node)
            # self._active.discarded.add_nodes_from(subgraph.nodes)
            # self._active.discarded.add_edges_from(subgraph.edges)
            # # ... retaining head-parent data for future reconstruction...
            # self._active.discarded.nodes[node]['remove_parent'] = parent
            # ...then remove subtree from main assembly
            self.assembly.remove_nodes_from(subgraph.nodes)


            # And lastly, if only one remaining sibling, remove it as redundant
            # N.B. No need to track back up through parents and remove redundant nodes...
            # ...if they are thus created, as this is done by "remove_redundant_nodes"...
            # ...when entire tree is redrawn via "OnTreeCtrlChanged"...
            # ---
            # ...but it WOULD be necessary if it weren't redrawn in full
            siblings = [el for el in self.assembly.successors(parent)]
            print('Removed all user-specified nodes')
            print('Remaining siblings: ', siblings)
            if len(siblings) == 1:
                print('Removing single remaining sibling as redundant nodes not allowed')
                self.assembly.remove_node(siblings[-1])

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def sort_check(self):

        # Check only one non-part item selected
        # ---
        if not self.assembly.nodes:
            print('No assembly present')
            return

        if len(self._active.partTree_ctc.GetSelections()) != 1:
            print('No or more than one item(s) selected')
            return

        item = self._active.partTree_ctc.GetSelection()
        if not item.HasChildren():
            print('Item is leaf node, cannot sort')
            return

        children_count = item.GetChildrenCount(recursively = False)
        if not children_count > 1:
            print('Cannot sort: item has single child')
            return

        # If all checks above passed...
        return True



    def OnSortMode(self, event):

        if not self.sort_check():
            return

        item = self._active.partTree_ctc.GetSelection()

        # Toggle sort mode, then sort
        if self._active.partTree_ctc.alphabetical:
            self._active.partTree_ctc.alphabetical = False
        else:
            self._active.partTree_ctc.alphabetical = True
        self._active.partTree_ctc.SortChildren(item)



    def OnSortReverse(self, event):

        if not self.sort_check():
            return

        item = self._active.partTree_ctc.GetSelection()

        # Toggle sort mode, then sort
        if self._active.partTree_ctc.reverse_sort:
            self._active.partTree_ctc.reverse_sort = False
        else:
            self._active.partTree_ctc.reverse_sort = True
        self._active.partTree_ctc.SortChildren(item)



    def OnSortAlpha(self, event = None):

        # Sort children of selected items alphabetically
        item = self._active.partTree_ctc.GetSelection()
        self._active.partTree_ctc.alphabetical = True
        self._active.partTree_ctc.SortChildren(item)



    def OnSortByID(self, event = None):

        # Sort children of selected item by ID
        item = self._active.partTree_ctc.GetSelection()

        # First reset "sort_id" as can be changed by drap and drop elsewhere
        # ---
        # MUST create shallow copy here (".copy()") to avoid strange behaviour
        # According to ctc docs, "It is advised not to change this list
        # [i.e. returned list] and to make a copy before calling
        # other tree methods as they could change the contents of the list."
        children = item.GetChildren().copy()
        for child in children:
            data = self._active.partTree_ctc.GetPyData(child)
            data['sort_id'] = data['id_']

        self._active.partTree_ctc.alphabetical = False
        self._active.partTree_ctc.SortChildren(item)



    def OnTreeDrag(self, event):

        # Drag and drop events are vetoed by default
        event.Allow()
        self.tree_drag_item = event.GetItem()
        id_ = self._active.ctc_dict_inv[event.GetItem()]
        print('ID of drag item = ', id_)
        self.tree_drag_id = id_



    def OnTreeDrop(self, event):

        # Allow event: drag and drop events vetoed by WX by default
        event.Allow()

        drop_item = event.GetItem()
        id_ = self._active.ctc_dict_inv[drop_item]
        print('ID of item at drop point = ', id_)

        drag_parent = self.tree_drag_item.GetParent()
        drop_parent = drop_item.GetParent()

        # Check if root node involved; return if so
        if (not drag_parent) or (not drop_parent):
            print('Drag or drop item is root: cannot proceed')
            return


        # CASE 1: DRAG AND DROP ITEMS HAVE THE SAME PARENT: MODIFY SORT ORDER
        # ---
        # If so, prepare sibling items by changing "sort_id" in part tree data
        # ---
        # HR 17/03/20: WHOLE SECTION NEEDS REWRITING TO BE SHORTER AND MORE EFFICIENT
        # PROBABLY VIA A FEW LIST OPERATIONS
        if drop_parent == drag_parent:

            sort_id = 1
            (child_, cookie_) = self._active.partTree_ctc.GetFirstChild(drop_parent)

            # If drop item found, slip drag item into its place
            if child_ == drop_item:
                self._active.partTree_ctc.GetPyData(self.tree_drag_item)['sort_id'] = sort_id
                sort_id += 1
            elif child_ == self.tree_drag_item:
                pass
            else:
                self._active.partTree_ctc.GetPyData(child_)['sort_id'] = sort_id
                sort_id += 1

            child_ = self._active.partTree_ctc.GetNextSibling(child_)
            while child_:

                # If drop item found, slip drag item into its place
                if child_ == drop_item:
                    self._active.partTree_ctc.GetPyData(self.tree_drag_item)['sort_id'] = sort_id
                    sort_id += 1
                elif child_ == self.tree_drag_item:
                    pass
                else:
                    self._active.partTree_ctc.GetPyData(child_)['sort_id'] = sort_id
                    sort_id += 1
                child_ = self._active.partTree_ctc.GetNextSibling(child_)

            # Re-sort, then return to avoid redrawing part tree otherwise
            self._active.partTree_ctc.alphabetical = False
            self._active.partTree_ctc.SortChildren(drop_parent)
            return

        # CASE 2: DRAG AND DROP ITEMS DO NOT HAVE THE SAME PARENT: SIMPLE MOVE
        # ---
        # Drop item is sibling unless it's root, then it's parent
        if self.assembly.get_parent(id_):
            parent = self.assembly.get_parent(id_)
        else:
            parent = id_
        self.assembly.move_node(self.tree_drag_id, parent)

        # Propagate changes
        self.ClearGUIItems()
        self.OnTreeCtrlChanged()



    def OnTreeLabelEditEnd(self, event):

        text_before = event.GetItem().GetText()
        wx.CallAfter(self.AfterTreeLabelEdit, event, text_before)
        event.Skip()



    def AfterTreeLabelEdit(self, event, text_before):

        item_ = event.GetItem()
        text_ = item_.GetText()
        if text_before != text_:
            id_ = self._active.ctc_dict_inv[item_]
            self.assembly.nodes[id_]['text'] = text_
        print('Text changed to:', item_.GetText())



    def ClearGUIItems(self):

        # Destroy all button objects
        for button_ in self._active.button_dict:
            obj = self._active.button_dict[button_]
            obj.Destroy()

        # Clear all relevant lists/dictionaries
        self._active.ctc_dict.clear()
        self._active.ctc_dict_inv.clear()

        self._active.button_dict.clear()
        self._active.button_dict_inv.clear()
        self._active.button_img_dict.clear()



    def OnSettings(self, event):
        self.AddText('Settings button pressed')



    def OnAbout(self, event):

        # Show program info
        abt_text = """StrEmbed-5-5: A user interface for manipulation of design configurations\n
            Copyright (C) 2019-2020 Hugh Patrick Rice\n
            This research is supported by the UK Engineering and Physical Sciences
            Research Council (EPSRC) under grant number EP/S016406/1.\n
            This program is free software: you can redistribute it and/or modify
            it under the terms of the GNU General Public License as published by
            the Free Software Foundation, either version 3 of the License, or
            (at your option) any later version.\n
            This program is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU General Public License for more details.\n
            You should have received a copy of the GNU General Public License
            along with this program. If not, see <https://www.gnu.org/licenses/>."""

        abt = wx.MessageDialog(self, abt_text, 'About StrEmbed-5-5', wx.OK)
        # Show dialogue that stops process (modal)
        abt.ShowModal()
        abt.Destroy()



    def OnResize(self, event):
        # Display window size in status bar
        self.AddText("Window size = " + format(self.GetSize()))
        wx.CallAfter(self.AfterResize, event)
        event.Skip()



    def AfterResize(self, event = None):

        ''' HR 06/10/20 ISSUE: Button widths don't resize (although images do)
            when window is resized '''
        try:
            # Resize all images in selector view
            if self._active.file_open:
                # Get size of selector grid element
                for k, v in self._active.button_dict.items():
                    img = self._active.button_img_dict[k]
                    v.SetBitmap(wx.Bitmap(self.ScaleImage(img)))

                self._active.slct_panel.SetupScrolling(scrollToTop = False)
        except:
            pass



    def DoNothingDialog(self, event = None, text = 'Dialog', message = 'Dialog'):
        nowt = wx.MessageDialog(self, text, message, wx.OK)
        # Create modal dialogue that stops process
        nowt.ShowModal()
        nowt.Destroy()



    def OnNewButton(self, event):
        self.AddText("New assembly button pressed")
        self.MakeNewAssembly()



    @property
    def new_assembly_id(self):
        if not hasattr(self, "assembly_id_counter"):
            self.assembly_id_counter = 0
        self.assembly_id_counter += 1
        return self.assembly_id_counter



    def MakeNewAssembly(self, _name = None):

        self.Freeze()

        if _name is None:
            new_id = self.new_assembly_id
            name_id = new_id
            _name = 'Assembly ' + str(name_id)
            # Check name doesn't exist; create new name by increment if so
            _names = [el.name for el in self.assembly_manager]
            while _name in _names:
                print('Name already exists, you drongo!')
                name_id += 1
                _name = 'Assembly ' + str(name_id)
                continue
        _page = NotebookPanel(self._notebook, _name, new_id, border = self._border)



        ''' Create assembly object and add to assembly manager '''
        assembly = MyParse(_id = new_id)
        self.assembly_manager[_page] = assembly



        ''' Add tab with select = True, so EVT_NOTEBOOK_PAGE_CHANGED fires
            and relevant assembly is activated via OnNotebookPageChanged '''
        self._notebook.AddPage(_page, _name, select = True)
        self._active = _page



        ''' All tab-specific bindings '''
        self._active.partTree_ctc.Bind(wx.EVT_RIGHT_DOWN,          self.OnRightClick)
        self._active.partTree_ctc.Bind(wx.EVT_TREE_BEGIN_DRAG,     self.OnTreeDrag)
        self._active.partTree_ctc.Bind(wx.EVT_TREE_END_DRAG,       self.OnTreeDrop)
        self._active.partTree_ctc.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnTreeLabelEditEnd)

        self._active.Bind(ctc.EVT_TREE_ITEM_CHECKED, self.TreeItemChecked)
        self._active.Bind(ctc.EVT_TREE_SEL_CHANGED,  self.TreeItemSelected)

        self._active.Bind(wx.EVT_TOGGLEBUTTON, self.ImageToggled)

        self._active.occ_panel.Bind(wx.EVT_LEFT_UP, self.OnLeftUp_3D)

        ''' Disable until file loaded '''
        self._active.Disable()

        self.Thaw()



    def OnNotebookPageChanged(self, event = None):

        _selection = self._notebook.GetSelection()
        print('Notebook tab index: ', _selection)
        _page = self._notebook.GetPage(_selection)
        print('Notebook tab name: ', _page.name)

        _text = 'Active notebook tab: ' + self._notebook.GetPageText(_selection)
        self.AddText(_text)

        ''' Activate window (here NotebookPanel) and assembly (MyParse)'''
        self.assembly = self.assembly_manager[_page]
        self._active = _page
        print('Assembly ID:   ', self.assembly._id)

        ''' Switch to selected assembly in lattive view '''
        try:
            self.DisplayLattice()
        except:
            pass

        if event:
            event.Skip()



    def AddText(self, msg):
        self.statbar.SetStatusText(msg)
        print(msg)



    def remove_saved_images(self):
        ''' Remove all saved images '''
        print('Trying to remove saved images...')
        try:
            shutil.rmtree(self.im_path)
            print('Done')
        except:
            print('Could not delete saved images: none may be present')



    def OnExit(self, event):
        self.remove_saved_images()
        event.Skip()



if __name__ == '__main__':
    # app = wit.InspectableApp()
    app = wx.App()
    frame = MainWindow()

    frame.Show()
    # frame.SetTransparent(220)
    frame.Maximize()

    app.MainLoop()