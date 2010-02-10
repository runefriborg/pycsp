"""
Play a trace of a PyCSP application

Usage:
  python play_pycsp_trace.py <trace file>

Requires:
  wxPython 2.8+
  PyCSP

The DrawFrame class has been based on the FloatCanvas.py demo from the wxPython
package written by Chris Barker <Chris.Barker@noaa.gov>.

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import sys
import wx
import numpy as N
import numpy.random as RandomArray

#from pycsp.threads import *
from pycsp_import import *
from pycsp.common import toolkit

try:
    from floatcanvas import NavCanvas, FloatCanvas, Resources
except ImportError: # if it's not there locally, try the wxPython lib.
    from wx.lib.floatcanvas import NavCanvas, FloatCanvas, Resources
import wx.lib.colourdb
import time, random


STATE_INIT, STATE_BLOCKED, STATE_RUNNING = range(3)
READ, WRITE = range(2)

class DrawFrame(wx.Frame):
    """
    A frame used for the FloatCanvas Demo

    """

    def __init__(self,parent, id,title,position,size):
        wx.Frame.__init__(self,parent, id,title,position, size)

        ## Set up the MenuBar
        MenuBar = wx.MenuBar()

        file_menu = wx.Menu()
        item = file_menu.Append(-1, "&Close","Close this frame")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)

        item = file_menu.Append(-1, "&SavePNG","Save the current image as a PNG")
        self.Bind(wx.EVT_MENU, self.OnSavePNG, item)
        MenuBar.Append(file_menu, "&File")

        view_menu = wx.Menu()
        item = view_menu.Append(-1, "Zoom to &Fit","Zoom to fit the window")
        self.Bind(wx.EVT_MENU, self.ZoomToFit, item)
        MenuBar.Append(view_menu, "&View")

        help_menu = wx.Menu()
        item = help_menu.Append(-1, "&About",
                                "More information About this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        MenuBar.Append(help_menu, "&Help")

        self.SetMenuBar(MenuBar)

        self.CreateStatusBar()

        # Add Extra buttons
        self.stateBtnPlay = 'pause'
        self.btnPlay = wx.Button(self, wx.ID_NEW, "Play Trace", (215,48), (100,30))
        self.Bind(wx.EVT_BUTTON, self.onPlayTrace, self.btnPlay)

        self.delay = wx.Slider(
            self, 1000, 25, 1, 1000, (30, 60), (200, -1), 
            wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS 
            )
        

        self.btnStep = wx.Button(self, wx.ID_OK, "Step Trace", (215,48), (100,30))
        self.Bind(wx.EVT_BUTTON, self.onStepTrace, self.btnStep)
        

        # Add the Canvas
        NC = NavCanvas.NavCanvas(self,
                                 Debug = 0,
                                 BackgroundColor = "WHITE")

        self.Canvas = NC.Canvas # reference the contained FloatCanvas

        self.MsgWindow = wx.TextCtrl(self, wx.ID_ANY,
                                     "Look Here for output from events\n",
                                     style = (wx.TE_MULTILINE |
                                              wx.TE_READONLY |
                                              wx.SUNKEN_BORDER)
                                     )

        ##Create a sizer to manage the Canvas and message window
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.btnPlay, 1 , wx.EXPAND | wx.ALL, 1)
        buttonSizer.Add(self.delay, 1 , wx.EXPAND | wx.ALL, 1)        
        buttonSizer.Add(self.btnStep, 1 , wx.EXPAND | wx.ALL, 1)
        MainSizer.Add(buttonSizer, 1, wx.EXPAND | wx.ALL, 1)

        MainSizer.Add(NC, 10, wx.EXPAND)
        MainSizer.Add(self.MsgWindow, 2, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(MainSizer)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.Canvas.Bind(FloatCanvas.EVT_MOTION, self.OnMove) 
        self.Canvas.Bind(FloatCanvas.EVT_MOUSEWHEEL, self.OnWheel) 

        self.EventsAreBound = False

        self.TRACE_PROCESSES = {}
        self.TRACE_CHANNELS = {}
        self.send_objects = -TRACE_OBJECTS_CHAN
        self.get_objects = +TRACE_OBJECTS_CHAN

        return None

    def Log(self, text):
        self.MsgWindow.AppendText(text)
        if not text[-1] == "\n":
            self.MsgWindow.AppendText("\n")


    def BindAllMouseEvents(self):
        if not self.EventsAreBound:
            ## Here is how you catch FloatCanvas mouse events
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_DOWN, self.OnLeftDown) 
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_UP, self.OnLeftUp)
            self.Canvas.Bind(FloatCanvas.EVT_LEFT_DCLICK, self.OnLeftDouble) 

            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_DOWN, self.OnMiddleDown) 
            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_UP, self.OnMiddleUp) 
            self.Canvas.Bind(FloatCanvas.EVT_MIDDLE_DCLICK, self.OnMiddleDouble) 

            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_DOWN, self.OnRightDown) 
            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_UP, self.OnRightUp) 
            self.Canvas.Bind(FloatCanvas.EVT_RIGHT_DCLICK, self.OnRightDouble) 

        self.EventsAreBound = True


    def UnBindAllMouseEvents(self):
        ## Here is how you unbind FloatCanvas mouse events
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_LEFT_DCLICK)

        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_MIDDLE_DCLICK)

        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_DOWN)
        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_UP)
        self.Canvas.Unbind(FloatCanvas.EVT_RIGHT_DCLICK)

        self.EventsAreBound = False


    def PrintCoords(self,event):
        self.Log("coords are: %s"%(event.Coords,))
        self.Log("pixel coords are: %s\n"%(event.GetPosition(),))

    def OnSavePNG(self, event=None):
        import os
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=os.getcwd(), 
            defaultFile="", wildcard="*.png", style=wx.SAVE
            )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not(path[-4:].lower() == ".png"):
                path = path+".png"
            self.Canvas.SaveAsImage(path)


    def OnLeftDown(self, event):
        self.Log("LeftDown")
        self.PrintCoords(event)

    def OnLeftUp(self, event):
        self.Log("LeftUp")
        self.PrintCoords(event)

    def OnLeftDouble(self, event):
        self.Log("LeftDouble")
        self.PrintCoords(event)

    def OnMiddleDown(self, event):
        self.Log("MiddleDown")
        self.PrintCoords(event)

    def OnMiddleUp(self, event):
        self.Log("MiddleUp")
        self.PrintCoords(event)

    def OnMiddleDouble(self, event):
        self.Log("MiddleDouble")
        self.PrintCoords(event)

    def OnRightDown(self, event):
        self.Log("RightDown")
        self.PrintCoords(event)

    def OnRightUp(self, event):
        self.Log("RightUp")
        self.PrintCoords(event)

    def OnRightDouble(self, event):
        self.Log("RightDouble")
        self.PrintCoords(event)

    def OnWheel(self, event):
        self.Log("Mouse Wheel")
        self.PrintCoords(event)
        Rot = event.GetWheelRotation()
        Rot = Rot / abs(Rot) * 0.1
        if event.ControlDown(): # move left-right
            self.Canvas.MoveImage( (Rot, 0), "Panel" )
        else: # move up-down
            self.Canvas.MoveImage( (0, Rot), "Panel" )

    def OnMove(self, event):
        """
        Updates the status bar with the world coordinates
        """
        self.SetStatusText("%.2f, %.2f"%tuple(event.Coords))
        event.Skip()

    def OnAbout(self, event):
        dlg = wx.MessageDialog(self,
                               "This is a small program to demonstrate\n"
                               "the use of the FloatCanvas\n",
                               "About Me",
                               wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def ZoomToFit(self,event):
        self.Canvas.ZoomToBB()

    def Clear(self,event = None):
        self.UnBindAllMouseEvents()
        self.Canvas.InitAll()
        self.Canvas.Draw()

    def OnQuit(self,event):
        poison(self.send_objects, self.get_objects)
        self.Close(True)

    def OnCloseWindow(self, event):
        poison(self.send_objects, self.get_objects)
        self.Destroy()

    def onPlayTrace(self, event=None):
        if self.stateBtnPlay == 'pause':
            self.stateBtnPlay = 'play'
            self.btnPlay.SetLabel('Pause Trace')
            self.btnStep.Enabled = False

            self.onPlayTrace2()
        else:
            self.stateBtnPlay = 'pause'
            self.btnPlay.SetLabel('Play Trace')
            self.btnStep.Enabled = True
            

    def onPlayTrace2(self):
        if self.stateBtnPlay == 'pause':
            return
        else:
            self.onStepTrace()
            wx.CallLater(self.delay.Value ,self.onPlayTrace2)

    def onStepTrace(self,event=None):

        wx.GetApp().Yield(True)

        self.BindAllMouseEvents()
        Canvas = self.Canvas

        Canvas.InitAll()
        #            
        ## these set the limits for how much you can zoom in and out
        Canvas.MinScale = 1
        Canvas.MaxScale = 500
    
        self.send_objects((self.TRACE_PROCESSES, self.TRACE_CHANNELS))
        (self.TRACE_PROCESSES, self.TRACE_CHANNELS) = self.get_objects()

        if self.TRACE_PROCESSES.has_key('__main__'):
            self.TRACE_PROCESSES['__main__'].draw(Canvas, only_update_pos = True)
            self.TRACE_PROCESSES['__main__'].draw(Canvas)
        
        Canvas.ZoomToBB()


class MainApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)

    def OnInit(self):

        wx.InitAllImageHandlers()
        frame = DrawFrame(None , -1, "PyCSP Trace Visualizer",wx.DefaultPosition,(700,700))

        self.SetTopWindow(frame)
        frame.Show()
        return True

class TracedChannel():
    def __init__(self, chan_name):
        self.processes = {}
        
        # Channel center.
        self.center = (0,0)

    def talking_to(self, p):
        if not self.processes.has_key(p):
            self.processes[p] = 1
        else:
            self.processes[p] += 1

    def update_center(self):
        x_sum, y_sum = (0, 0)
        count = len(self.processes)
        for p in self.processes.keys():
            box_center = p.box_get_center(p.real_box)
            x_sum += box_center[0]
            y_sum += box_center[1]
        
        self.center = (x_sum / count, y_sum / count)
        #print self.center

    def draw_for_process(self, Canvas, p, _type):
        self.update_center()

        box_center = p.box_get_center(p.real_box)
            
        if _type == READ:
            #print p.virtual_pos, self.center            
            Canvas.AddArrowLine([self.center, box_center], LineWidth = 1, LineColor = 'BLACK', ArrowHeadSize= 10)
        else:
            Canvas.AddArrowLine([box_center, self.center], LineWidth = 1, LineColor = 'BLACK', ArrowHeadSize= 10)


class TracedProcess():
    def __init__(self, id, func_name):
        self.id = id
        self.func_name = func_name
        self.processes = {}
        self.parent = None
        # The virtual grid contains links to processes, such that
        # we can update the location of processes based on the actual
        # communication from a process.
        # The virtual grid is initialized with a dimension of Zero = None
        # The dimensions are computed like this:
        # x,y = (len(self.processes), len(self.processes))
        self.virtual_grid = []
        self.virtual_grid_width_dim = 0
        self.virtual_grid_height_dim = 0
        self.channels = {}

        self.real_box = None

        # STATE_INIT, STATE_BLOCKED, STATE_RUNNING
        self.state = STATE_INIT
        self.state_msg = ""


        self.reading = {}
        self.writing = {}
        self.local_reading_processes = {}

    def update_chan(self, chan, _type, subprocess=False):
        if self.parent != None:
            if self.parent.channels.has_key(chan):
                self.parent.channels[chan][self] = _type
            else:
                self.parent.channels[chan] = {self:_type}

            self.parent.update_chan(chan, _type, subprocess=True)
            self.parent.compute_virtual_grid(self)

        if not subprocess:
            if _type == WRITE:
                self.writing[chan] = 1
            else:
                self.reading[chan] = 1


    def compute_virtual_grid(self, caller):
        if self.processes:
            if self.channels:
                # Make copy and remove one by one
                todo = self.processes.values()
                
                # New virtual_grid
                self.virtual_grid = []

                for chan in self.channels:
                    proclist = self.channels[chan]
                    L , R = [], []
                    for proc in proclist:
                        if proc in todo:
                            if proclist[proc] == WRITE:
                                L.append(proc)
                            else:
                                R.append(proc)
                            todo.remove(proc)
                            
                    if (len(L) == 1 and len(R) == 1):
                        self.virtual_grid.append(L+R)
                    else:
                        if (L):
                            self.virtual_grid.append(L)
                        if (R):
                            self.virtual_grid.append(R)


                for proc in todo:
                    self.virtual_grid.append([proc])

                self.update_virtual_grid_dim()

    def virtual_move(self, p, below):

        current_x, current_y = p.get_virtual_index()

        # Remove current pos
        del self.virtual_grid[current_x][current_y]

        # Remove empty x positions
        self.virtual_grid = [x_list for x_list in self.virtual_grid if len(x_list) > 0]

        below_sum = 0
        below_len = 0
        for below_p in below:
            below_x,below_y = below[0].get_virtual_index()
            below_len += 1
            below_sum += below_x
        
        new_pos = int(below_sum / below_len)

        # Insert new pos        
        self.virtual_grid[new_pos].append(p)

        # Update
        self.update_virtual_grid_dim()

    def get_virtual_index(self):
        
        x = 0
        y = 0
        if self.parent != None:
            for x_list in self.parent.virtual_grid:
                if self in x_list:
                    y = x_list.index(self)
                    break
                x += 1        
        return (x,y)


    def addProcess(self, p):
        self.processes[p.id] = p
        self.virtual_grid.append([p])
        
        self.update_virtual_grid_dim()

    def removeProcess(self, p):
        if self.processes.has_key(p.id):

            x = 0
            y = 0
            for x_list in self.virtual_grid:
                if p in x_list:
                    y = x_list.index(p)
                    break
                x += 1

            del self.virtual_grid[x][y]

            del self.processes[p.id]

            # Remove empty x positions
            self.virtual_grid = [x_list for x_list in self.virtual_grid if len(x_list) > 0]

            self.update_virtual_grid_dim()


    def update_virtual_grid_dim(self):
        self.virtual_grid_width_dim = len(self.virtual_grid)
        height_dim = 0
        for h in self.virtual_grid:
            if height_dim < len(h):
                height_dim = len(h)
        self.virtual_grid_height_dim = height_dim


    def box_scale(self, box , scale=0.9):
        (w,h) = self.box_get_size(box)
        ((x1,y1),(x2,y2)) = box
        new_w, new_h = (w*scale, h*scale)
        change_w, change_h = ((w-new_w)/2, (h-new_h)/2)
        return ((x1 + change_w, y1 + change_h), (x2 - change_w, y2 - change_h))

    def box_get_size(self, ((x1,y1),(x2,y2))):
        return (x2-x1, y2-y1)
                
    def box_get_dim(self, box, xboxcount, yboxcount):
        w,h = self.box_get_size(box)
        return (w/xboxcount, h/yboxcount)

    def box_get_center(self, box):
        w,h = self.box_get_size(box)
        return (box[0][0]+(w/2), box[0][1]+(h/2))

    def draw(self, Canvas, box= ((-200, -100), (200, 100)), only_update_pos = False):

        #Make frame
        box = self.box_scale(box, scale = 0.8)

        fillColor = 'WHITE'
        if self.state == STATE_BLOCKED:
            fillColor = 'GRAY'


        if not only_update_pos:
            for c in self.reading.keys():
                c.draw_for_process(Canvas, self, READ)
            for c in self.writing.keys():
                c.draw_for_process(Canvas, self, WRITE)

        
        if self.processes:
            
            # Rectangle
            box_size = self.box_get_size(box)
            if only_update_pos:
                self.real_box = box
            else:
                Canvas.AddRectangle(box[0], box_size , LineWidth = 2, FillColor = fillColor)
                #Canvas.AddScaledText(self.func_name, box[0], Size = box_size[0]*0.1, Color = 'BLACK', Position = "bl")
                Canvas.AddText(self.func_name + ' ' + self.state_msg, box[0], Size = 10.0, Color = 'BLACK', Position = "bl")
            
            #offset = box[0][0]
            #add = (box[1][0] - box[0][0]) / len(self.processes)
            dim = self.box_get_dim(box, self.virtual_grid_width_dim, self.virtual_grid_height_dim)
            x_i = box[0][0]
            for x_loc in self.virtual_grid:
                y_i = box[0][1]
                for y_loc in x_loc:                    
                    if y_loc != None:
                        y_loc.draw(Canvas, box = ((x_i,y_i), (x_i+dim[0], y_i+dim[1])), only_update_pos = only_update_pos)
                    y_i += dim[1]
                x_i += dim[0]
        else:
            # Ellipse
            box = self.box_scale(box, scale = 0.5)
            box_size = self.box_get_size(box)
            if only_update_pos:
                self.real_box = box
            else:
                Canvas.AddEllipse(box[0], box_size, LineWidth = 2,FillColor = fillColor)
                #Canvas.AddScaledText(self.func_name, self.box_get_center(box), Size = box_size[0]*0.2, Color = 'BLACK', Position = "cc")
                Canvas.AddText(self.func_name, self.box_get_center(box), Size = 10.0, Color = 'BLACK', Position = "cc")

            

@process
def UpdateTrace(get_trace, get_objects, send_objects):
    while True:
        try:
            tracelist = get_trace()
        except ChannelRetireException:
            poison(get_objects)
            return

        # Parse..
        for trace in tracelist:
            trace = eval(trace)

            #print trace

            if False:
                pass
            else:
                if trace['type'] == 'BlockOnParallel':
                    (trace_processes, trace_channels) = get_objects()

                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.addProcess(p)
                        p.parent = parent

                    parent.state = STATE_BLOCKED
                    parent.state_msg = 'Parallel'
                    send_objects((trace_processes, trace_channels))

                elif trace['type'] == 'BlockOnSequence':
                    (trace_processes, trace_channels) = get_objects()

                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.addProcess(p)
                        p.parent = parent

                    parent.state = STATE_BLOCKED
                    parent.state_msg = 'Sequence'
                    send_objects((trace_processes, trace_channels))

                elif trace['type'] == 'Spawn':
                    (trace_processes, trace_channels) = get_objects()

                    if not trace_processes.has_key(trace['process_id']):
                        # Main process
                        p = TracedProcess(trace['process_id'], '__main__')
                        trace_processes[trace['process_id']] = p
                        trace_processes['__main__'] = p

                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # Add to subprocess list
                        p = TracedProcess(proc['process_id'], proc['func_name'])
                        trace_processes[proc['process_id']] = p
                        parent.addProcess(p)
                        p.parent = parent

                    send_objects((trace_processes, trace_channels))

                elif trace['type'] == 'QuitProcess':
                    (trace_processes, trace_channels) = get_objects()
                    proc = trace_processes[trace['process_id']]
                    if proc.parent != None:
                        proc.parent.removeProcess(proc)
                    send_objects((trace_processes, trace_channels))
                    
                elif trace['type'] == 'DoneParallel':
                    (trace_processes, trace_channels) = get_objects()
                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # remove from subprocess list
                        parent.removeProcess(trace_processes[proc['process_id']])
                    parent.state = STATE_RUNNING
                    parent.state_msg = ''

                    send_objects((trace_processes, trace_channels))

                elif trace['type'] == 'DoneSequence':
                    (trace_processes, trace_channels) = get_objects()
                    parent = trace_processes[trace['process_id']]
                    for proc in trace['processes']:
                        # remove from subprocess list
                        parent.removeProcess(trace_processes[proc['process_id']])
                    parent.state = STATE_RUNNING
                    parent.state_msg = ''

                    send_objects((trace_processes, trace_channels))                            
                elif (trace['type'] == 'BlockOnRead' or 
                      trace['type'] == 'BlockOnWrite'):
                    (trace_processes, trace_channels) = get_objects()
                    trace_processes[trace['process_id']].state = STATE_BLOCKED

                    if not trace_channels.has_key(trace['chan_name']):
                        trace_channels[trace['chan_name']] = TracedChannel(trace['chan_name'])                    

                    chan = trace_channels[trace['chan_name']]
                    p = trace_processes[trace['process_id']]

                    chan.talking_to(p)

                    if trace['type'] == 'BlockOnRead':
                        p.update_chan(chan, READ)
                    else:
                        p.update_chan(chan, WRITE)

                    send_objects((trace_processes, trace_channels))     
                elif (trace['type'] == 'DoneRead' or
                      trace['type'] == 'DoneWrite'):
                    (trace_processes, trace_channels) = get_objects()
                    trace_processes[trace['process_id']].state = STATE_RUNNING
                    send_objects((trace_processes, trace_channels))     

                elif (trace['type'] == 'BlockOnAlternation.execute' or
                      trace['type'] == 'BlockOnAlternation.select'):
                    (trace_processes, trace_channels) = get_objects()
                    trace_processes[trace['process_id']].state = STATE_BLOCKED
                    send_objects((trace_processes, trace_channels))

                elif (trace['type'] == 'DoneAlternation.execute' or
                      trace['type'] == 'DoneAlternation.select'):
                    (trace_processes, trace_channels) = get_objects()
                    trace_processes[trace['process_id']].state = STATE_RUNNING
                    guard = trace['guard']

                    _type = None
                    if guard['type'] == 'ReadGuard':
                        _type = READ
                    elif guard['type'] == 'WriteGuard':
                        _type = WRITE

                    if _type != None:

                        if not trace_channels.has_key(guard['chan_name']):
                            trace_channels[guard['chan_name']] = TracedChannel(guard['chan_name'])

                        chan = trace_channels[guard['chan_name']]
                        p = trace_processes[trace['process_id']]

                        chan.talking_to(p)

                        p.update_chan(chan, _type)

                    send_objects((trace_processes, trace_channels))     
            

@process
def TestDraw(cin, cout):
    TRACE_PROCESSES = {}
    TRACE_CHANNELS = {}
    while True:
        cout((TRACE_PROCESSES,TRACE_CHANNELS))
        #print TRACE_PROCESSES
        TRACE_PROCESSES, TRACE_CHANNELS = cin()

             

if len(sys.argv) > 1:
    TRACE_FILE = sys.argv[1]
    TRACE_FILE_CHAN = Channel('TraceFile')
    TRACE_OBJECTS_CHAN = Channel('TraceObjects')

    Spawn(
        toolkit.file_r(-TRACE_FILE_CHAN, TRACE_FILE),
        UpdateTrace(+TRACE_FILE_CHAN, +TRACE_OBJECTS_CHAN, -TRACE_OBJECTS_CHAN)
        )
    
    #Parallel(TestDraw(+TRACE_OBJECTS_CHAN, -TRACE_OBJECTS_CHAN))

    app = MainApp()
    app.MainLoop()

else:
    print __doc__
    
