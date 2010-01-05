#!/usr / bin / env python
# $Revision: 229 $ $Date: 2009-01-26 16:17:21 +0100 (Mon, 26 Jan 2009) $ kgm
""" SimPlot 2.0  Provides basic plotting services based on Tk / Tkinter.

LICENSE:
Copyright (C) 2002, 2005, 2006, 2007, 2008  Klaus G. Muller, Tony Vignaux
mailto: kgmuller@xs4all.nl and Tony.Vignaux@vuw.ac.nz

    This library is free software; you can redistribute it and / or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111 - 1307  USA
END OF LICENSE

Derived from plotting package in Grayson's Tkinter book.
The idea to use this package came from Prof. Simon Frost
of U of California, San Diego who also strongly contributed
to the design and implementation of SimPlot.


Change history:

    Nov 2, 2003 :  Combined utils.py (also from Grayson) with plotting package.
    Nov 11, 2003: Made totally OO
    Dec 16, 2003: Completion of SimPlot 1.4alpha
    Feb 2004:       Release with SimPy 1.4
    Aug 27, 2005: Added tests for empty point sets to plotXXX functions.
    Sep 15, 2008: Adjusted to SimPy 2.0 changes

"""
__version__ = '2.0 $Revision: 229 $ $Date: 2009-01-26 16:17:21 +0100 (Mon, 26 Jan 2009) $'
from Tkinter import *
from Canvas import Line, CanvasText, Rectangle
from tkMessageBox import *
from tkSimpleDialog import askinteger, askstring, askfloat
from tkFileDialog import *
import string, math
from math import pi
from recording import Monitor

def minCoordinate(clist):
    if len(clist) < 2: return clist[0]
    try:
        x,  y  = clist[0]
        for x1, y1 in clist[1:]:
            if x1 <= x or y1 <= y:
                x, y = x1, y1
    except:
        x, y = 0, 0

    return x, y

def maxCoordinate(clist):
    if len(clist) < 2: return clist[0]
    try:
        x,  y  = clist[0]
        for x1, y1 in clist[1:]:
            if x1 >= x or y1 >= y:
                x, y = x1, y1
    except:
        x, y = 0, 0

    return x, y

def minBound(clist):
    x = 10000000
    y = 10000000
    for x1, y1 in clist:
        if x1 < x: x = x1
        if y1 < y: y = y1        
    return x, y

def maxBound(clist):
    x = -10000000
    y = -10000000
    for x1, y1 in clist:
        if x1 > x: x = x1
        if y1 > y: y = y1        
    return x, y

class SimPlot(object):
    def __init__(self, root = Tk()):
        self.root = root
        pass

    def mainloop(self):
        self.root.mainloop()

    def makeLine(self, points,**attr):
        return GraphLine(points, **attr)
    def makeStep(self, points, **attr):
        #convert data list to steps
        step0 = points[:]
        step1 = [[0, 0]] * 2*len(step0)
        prev = [step0[0][0],0]
        for x in range(len(step0)):
            step1[2 * x] = [step0[x][0],prev[1]]
            step1[2 * x + 1] = step0[x]
            prev = step0[x]
        #draw the line
        return self.makeLine(step1, smooth = False, **attr)
    
    def makeHistogram(self, points,**attr):
        """Makes a histogram graph. 'points' must be a Histogram - like
        object.
        """
        #convert data list to bars
        step0 = points[:]
        step1 = [[0, 0]] * 3*len(step0)
        prev = [step0[0][0],0]
        for x in range(len(step0)):
            step1[3 * x] = [step0[x][0],prev[1]]
            step1[3 * x + 1] = [step0[x][0],0.0]
            step1[3 * x + 2] = step0[x]
            prev = step0[x]
        deltax = step0[1][0] - step0[0][0]
        step1.append([prev[0] + deltax, prev[1]])
        step1.append([prev[0] + deltax, 0])
        #make the line
        return self.makeLine(step1, smooth = False,
                             xaxis = (step1[0][0],step1[-1][0]),
                             **attr)        
    
    def makeSymbols(self, points,**attr):
        return GraphSymbols(points,**attr)
    def makeBars(self, points,**attr):
        return GraphBars(points,**attr)
    def makeGraphObjects(self, objects):
        return GraphObjects(objects)
    def makeGraphBase(self, master, width, height,
                 background = 'white', title = '', xtitle = '', ytitle = '', **kw):
        return GraphBase(master, width, height,
                 background, title, xtitle, ytitle,**kw)

    def graphMenu(self, root, graph):
        """To provide a File menu (postscript output, more to come)
        to the plotxxxx plots"""
        mainMenu = Menu(root)
        root.config(menu = mainMenu)
        def postscriptout():
            graph.postscr()
        file = Menu(mainMenu)
        file.add_command(label = 'Postscript', command = postscriptout)
        mainMenu.add_cascade(label = 'File', menu = file, underline = 0)
        
    def plotLine(self, points, windowsize = (500, 300),title = '', width = 1, color = 'black',
                 smooth = 0, background = 'white', xlab = 'x', ylab = 'y',
                 xaxis = 'automatic', yaxis = 'automatic'):
        """Generates a line chart, with menu to save as Postscript file.
        'points' can be a Monitor instance.
        """
        if points != []:
            root = Toplevel()
            f = Frame(root)
            try: #if it is like a Monitor, take xlab, ylab from it
                ylab = points.ylab
                xlab = points.tlab
                if not title: title = points.name 
            except:
                pass
            line = self.makeLine(points, width = width, color = color, smooth = smooth)
            gr = self.makeGraphObjects([line])
            graph = self.makeGraphBase(f, windowsize[0], windowsize[1],
                                   title = title, xtitle = xlab,
                                   ytitle = ylab, background = background)
            graph.pack(side = LEFT, fill = BOTH, expand = YES)
            graph.draw(gr, xaxis = xaxis, yaxis = yaxis)
            #File menu
            self.graphMenu(root, graph)
            f.pack()
            return graph
        else:
            print 'SimPlot.plotline: dataset empty, no plot.'
            return None
    
    def plotStep(self, points, windowsize = (500, 300),title = '', width = 1, color = 'black',
                 background = 'white', xlab = 'x', ylab = 'y',
                 xaxis = 'automatic', yaxis = 'automatic'):
        """Generates a step chart, with menu to save as Postscript file.
        'points' can be a Monitor instance.
        """
        if points != []:
            #convert data list to steps
            step0 = points[:]
            step1 = [[0, 0]] * 2*len(step0)
            prev = [step0[0][0],0]
            for x in range(len(step0)):
                step1[2 * x] = [step0[x][0],prev[1]]
                step1[2 * x + 1] = step0[x]
                prev = step0[x]
            #treat monitor case
            try: #if it is like a Monitor, take xlab, ylab from it
                ylab = points.ylab
                xlab = points.tlab
                if not title: title = points.name 
            except:
                pass
            #draw the line
            smooth = False
            return self.plotLine(step1, windowsize, title, width, color,
                 smooth, background, xlab, ylab,
                 xaxis, yaxis)
        else:
            print 'SimPlot.plotStep: dataset empty, no plot.'
            return None

    def plotHistogram(self, points, windowsize = (500, 300),title = '', width = 1, color = 'black',
                 background = 'white', xlab = 'x', ylab = 'y',
                 xaxis = 'automatic', yaxis = 'automatic'):
        """Makes a histogram plot. 'points' can be a Monitor  instance.
        """
        if points != []:
            #convert data list to bars
            step0 = points[:]
            step1 = [[0, 0]] * 3*len(step0)
            prev = [step0[0][0],0]
            for x in range(len(step0)):
                step1[3 * x] = [step0[x][0],prev[1]]
                step1[3 * x + 1] = [step0[x][0],0.0]
                step1[3 * x + 2] = step0[x]
                prev = step0[x]
            deltax = step0[1][0] - step0[0][0]
            step1.append([prev[0] + deltax, prev[1]])
            step1.append([prev[0] + deltax, 0])
            #treat monitor case
            try: #if it is like a Monitor, take xlab, ylab from it
                ylab = points.ylab
                xlab = points.tlab
                if not title: title = points.name 
            except:
                pass
            #draw the line
            smooth = False
            return self.plotLine(step1, windowsize = windowsize, title = title, width = width,
                             color = color, smooth = smooth, background = background,
                             xlab = xlab, ylab = ylab, xaxis = (step1[0][0],step1[-1][0]),
                             yaxis = yaxis)
        else:
            print 'SimPlot.plotHistogram: dataset empty, no plot.'
            return None
    
    def plotBars(self, points, windowsize = (500, 300),title = '', color = 'black',
                 width = 1, size = 3, fillcolor = 'black', fillstyle = '',
                 outline = 'black', background = 'white', xlab = 'x', ylab = 'y',
                 xaxis = 'automatic', yaxis = 'automatic', anchor = 0.0):
        """Generates a bar chart, with menu to save as Postscript file.
        'points' can be a Monitor instance.
        """
        if points != []:
            root = Toplevel()
            f = Frame(root)
            try: #if it is like a Monitor, take xlab, ylab from it
                ylab = points.ylab
                xlab = points.tlab
                if not title: title = points.name 
            except:
                pass
            bars = self.makeBars(points, width = width, size = size, color = color,
                           fillcolor = fillcolor, fillstyle = fillstyle,
                           outline = outline, anchor = anchor)
            gr = self.makeGraphObjects([bars])
            graph = self.makeGraphBase(f, windowsize[0],windowsize[1],
                                   title = title, xtitle = xlab,
                                   ytitle = ylab, background = background)
            graph.pack(side = LEFT, fill = BOTH, expand = YES)
            graph.draw(gr, xaxis = xaxis, yaxis = yaxis)
            #File menu
            self.graphMenu(root, graph)
            f.pack()
            return graph
        else:
            print 'SimPlot.plotBars dataset empty, no plot.'
            return None

    def plotScatter(self, points, windowsize = (500, 300),title = '', width = 1, color = 'black',
                    fillcolor = 'black', size = 2, fillstyle = '',
                    outline = 'black', marker = 'circle',
                    background = 'white', xlab = 'x', ylab = 'y',
                    xaxis = 'automatic', yaxis = 'automatic'):
        if points != []:
            root = Toplevel()
            f = Frame(root)
            try: #if it is like a Monitor, take xlab, ylab from it
                ylab = points.ylab
                xlab = points.tlab
                if not title: title = points.name 
            except:
                pass
            scat = self.makeSymbols(points, width = width, color = color, size = size,
                              marker = marker, fillcolor = fillcolor,
                              fillstyle = fillstyle, outline = outline)
            gr = self.makeGraphObjects([scat])
            graph = self.makeGraphBase(f, windowsize[0],windowsize[1],
                                   title = title, xtitle = xlab,
                                   ytitle = ylab, background = background)
            graph.pack(side = LEFT, fill = BOTH, expand = YES)
            graph.draw(gr, xaxis = xaxis, yaxis = yaxis)
            #File menu
            self.graphMenu(root, graph)
            f.pack()
            return graph
        else:
            print 'SimPlot.plotScatter: dataset empty, no plot.'
            return None

    def mainloop(self):
        self.root.mainloop()
    
class GraphPoints:
    def __init__(self, points, attr):
        self.points = points
        self.scaled = self.points
        self.attributes = {}
        for name, value in self._attributes.items():
            try:
                value = attr[name]
            except KeyError: pass
            self.attributes[name] = value

    def boundingBox(self):
        return minBound(self.points),  maxBound(self.points)

    def fitToScale(self, scale = (1, 1), shift = (0, 0)):
        self.scaled = []
        for x, y in self.points:
            self.scaled.append(((scale[0] * x) + shift[0],\
                               (scale[1] * y) + shift[1]))
            self.attributes.get('anchor', 0.0)
        self.anchor = scale[1] * self.attributes.get('anchor', 0.0)+\
                      shift[1]

class GraphLine(GraphPoints):
    def __init__(self, points, **attr):
        GraphPoints.__init__(self, points, attr)

    _attributes = {'color':       'black',
                   'width':        1,
                   'smooth':       0,
                   'splinesteps': 12}

    def draw(self, canvas):
        color  = self.attributes['color']
        width  = self.attributes['width']
        smooth = self.attributes['smooth']
        steps  = self.attributes['splinesteps']
        arguments = (canvas,)
        if smooth:
            for i in range(len(self.points)):
                x1, y1 = self.scaled[i]
                arguments = arguments + (x1, y1)
        else:
            for i in range(len(self.points) - 1):
                x1, y1 = self.scaled[i]
                x2, y2 = self.scaled[i + 1]
                arguments = arguments + (x1, y1, x2, y2)
        apply(Line, arguments, {'fill': color, 'width': width,
                                'smooth': smooth, 'splinesteps':steps})

class GraphSymbols(GraphPoints):
    def __init__(self, points, **attr):
        GraphPoints.__init__(self, points, attr)

    _attributes = {'color': 'black',
                   'width': 1,
                   'fillcolor': 'black',
                   'size': 2,
                   'fillstyle': '',
                   'outline': 'black',
                   'marker': 'circle'}

    def draw(self, canvas):
        color     = self.attributes['color']
        size      = self.attributes['size']
        fillcolor = self.attributes['fillcolor']
        marker    = self.attributes['marker']
        fillstyle = self.attributes['fillstyle']

        self._drawmarkers(canvas, self.scaled, marker, color,
                          fillstyle, fillcolor, size)

    def _drawmarkers(self, c, coords, marker = 'circle', color = 'black',
                     fillstyle = '', fillcolor = '', size = 2):
        l = []
        f = eval('self._' + marker)
        for xc, yc in coords:
            id = f(c, xc, yc, outline = color, size = size,
                   fill = fillcolor, fillstyle = fillstyle)
            if type(id) is type(()):
                for item in id: l.append(item)
            else:
                l.append(id)
        return l
    
    def _circle(self, c, xc, yc, size = 1, fill = '', outline = 'black',
                fillstyle = ''):
        id = c.create_oval(xc - 0.5, yc - 0.5, xc + 0.5, yc + 0.5, 
                           fill = fill, outline = outline,
                           stipple = fillstyle)
        c.scale(id, xc, yc, size * 5, size * 5)
        return id

    def _dot(self, c, xc, yc, size = 1, fill = '', outline = 'black',
             fillstyle = ''):
        id = c.create_oval(xc - 0.5, yc - 0.5, xc + 0.5, yc + 0.5, 
                           fill = fill, outline = outline,
                           stipple = fillstyle)
        c.scale(id, xc, yc, size * 2.5, size * 2.5)
        return id

    def _square(self, c, xc, yc, size = 1, fill = '', outline = 'black',
                fillstyle = ''):
        id = c.create_rectangle(xc - 0.5, yc - 0.5, xc + 0.5, yc + 0.5,
                                fill = fill, outline = outline,
                                stipple = fillstyle)
        c.scale(id, xc, yc, size * 5, size * 5)
        return id
    
    def _triangle(self, c, xc, yc, size = 1, fill = '', outline = 'black',
                  fillstyle = ''):
        id = c.create_polygon(-0.5, 0.288675134595,
                              0.5, 0.288675134595,
                              0.0, -0.577350269189, fill = fill,
                              outline = outline, stipple = fillstyle)
        c.move(id, xc, yc)
        c.scale(id, xc, yc, size * 5, size * 5)
        return id

    def _triangle_down(self, c, xc, yc, size = 1, fill = '',
                       outline = 'black', fillstyle = ''):
        id = c.create_polygon(-0.5, -0.288675134595,
                              0.5, -0.288675134595,
                              0.0, 0.577350269189, fill = fill,
                              outline = outline, stipple = fillstyle)
        c.move(id, xc, yc)
        c.scale(id, xc, yc, size * 5, size * 5)
        return id

    def _cross(self, c, xc, yc, size = 1, fill = 'black', outline = None,
               fillstyle = ''):
        if outline: fill = outline
        id1 = c.create_line(xc - 0.5, yc - 0.5, xc + 0.5, yc + 0.5,
                            fill = fill)
        id2 = c.create_line(xc - 0.5, yc + 0.5, xc + 0.5, yc - 0.5,
                            fill = fill)
        c.scale(id1, xc, yc, size * 5, size * 5)
        c.scale(id2, xc, yc, size * 5, size * 5)
        return id1, id2

    def _plus(self, c, xc, yc, size = 1, fill = 'black', outline = None,
              fillstyle = ''):
        if outline: fill = outline
        id1 = c.create_line(xc - 0.5, yc, xc + 0.5, yc, fill = fill)
        id2 = c.create_line(xc, yc + 0.5, xc, yc - 0.5, fill = fill)
        c.scale(id1, xc, yc, size * 5, size * 5)
        c.scale(id2, xc, yc, size * 5, size * 5)
        return id1, id2

class GraphBars(GraphPoints):
    def __init__(self, points, **attr):
        GraphPoints.__init__(self, points, attr)

    _attributes = {'color': 'black',
                   'width': 1,
                   'fillcolor': 'black',
                   'size': 3,
                   'fillstyle': '', 
                   'outline': 'black'}

    def draw(self, canvas):
        color     = self.attributes['color']
        width     = self.attributes['width']
        fillstyle = self.attributes['fillstyle']
        outline   = self.attributes['outline']
        spread    = self.attributes['size']
        arguments = (canvas,)
        p1, p2    = self.boundingBox()
        for i in range(len(self.points)):
            x1, y1 = self.scaled[i]
            canvas.create_rectangle(x1 - spread, y1, x1 + spread,
                                    self.anchor, fill = color,
                                    width = width, outline = outline,
                                    stipple = fillstyle)

class GraphObjects:
    def __init__(self, objects):
        self.objects = objects

    def boundingBox(self):
        c1, c2 = self.objects[0].boundingBox()
        for object in self.objects[1:]:
            c1o, c2o = object.boundingBox()
            c1 = minBound([c1, c1o])

            c2 = maxBound([c2, c2o])
        return c1, c2

    def fitToScale(self, scale = (1, 1), shift = (0, 0)):
        for object in self.objects:
            object.fitToScale(scale, shift)

    def draw(self, canvas):
        for object in self.objects:
            object.draw(canvas)

class GraphBase(Frame):
    def __init__(self, master, width, height,
                 background = 'white', title = '', xtitle = '', ytitle = '', **kw):
        apply(Frame.__init__, (self, master), kw)
        self.title = title                                        
        self.xtitle = xtitle
        self.ytitle = ytitle
        self.canvas = Canvas(self, width = width, height = height,
                             background = background)
        self.canvas.pack(fill = BOTH, expand = YES)
        border_w = self.canvas.winfo_reqwidth() - \
                   string.atoi(self.canvas.cget('width'))
        border_h = self.canvas.winfo_reqheight() - \
                   string.atoi(self.canvas.cget('height'))
        self.border = (border_w, border_h)
        self.canvas.bind('<Configure>', self.configure)
        self.plotarea_size = [None, None]
        self._setsize()
        self.last_drawn = None
        self.font = ('Verdana', 10)

    def configure(self, event):
        new_width = event.width - self.border[0]
        new_height = event.height - self.border[1]
        width = string.atoi(self.canvas.cget('width'))
        height = string.atoi(self.canvas.cget('height'))
        if new_width == width and new_height == height:
            return
        self.canvas.configure(width = new_width, height = new_height)
        self._setsize()
        self.clear()
        self.replot()

    def bind(self, *args):
        apply(self.canvas.bind, args)

    def _setsize(self):
        self.width = string.atoi(self.canvas.cget('width'))
        self.height = string.atoi(self.canvas.cget('height'))
        #self.plotarea_size[0] = 0.90 * self.width
        #self.plotarea_size[1] = 0.90 * -self.height
        self.plotarea_size[0] = 0.90 * self.width
        self.plotarea_size[1] = 0.90 * -self.height      
        xo = 0.5 * (self.width - self.plotarea_size[0])
        yo = self.height - 0.5 * (self.height + self.plotarea_size[1])
        self.plotarea_origin = (xo, yo)
        
    def draw(self, graphics, xaxis = 'automatic', yaxis = 'automatic'):
        
        self.last_drawn = (graphics, xaxis, yaxis)
        p1, p2 = graphics.boundingBox()
        xaxis = self._axisInterval(xaxis, p1[0], p2[0])
        yaxis = self._axisInterval(yaxis, p1[1], p2[1])
        text_width = [0., 0.]
        text_height = [0., 0.]
        if xaxis is not None:
            p1 = xaxis[0], p1[1]
            p2 = xaxis[1], p2[1]
            xticks = self._ticks(xaxis[0], xaxis[1])
            bb = self._textBoundingBox(xticks[0][1])
            text_height[1] = bb[3] - bb[1]
            text_width[0] = 0.5 * (bb[2] - bb[0])
            bb = self._textBoundingBox(xticks[-1][1])
            text_width[1] = 0.5 * (bb[2] - bb[0])
        else:
            xticks = None
        if yaxis is not None:
            p1 = p1[0], yaxis[0]
            p2 = p2[0], yaxis[1]
            yticks = self._ticks(yaxis[0], yaxis[1])
            for y in yticks:
                bb = self._textBoundingBox(y[1])
                w = bb[2] - bb[0]
                text_width[0] = max(text_width[0], w)
            h = 0.5 * (bb[3] - bb[1])
            text_height[0] = h
            text_height[1] = max(text_height[1], h)
        else:
            yticks = None
        text1 = [text_width[0], -text_height[1]]
        text2 = [text_width[1], -text_height[0]]
        scale = ((self.plotarea_size[0] - text1[0] - text2[0]) / \
                 (p2[0] - p1[0]),
                 (self.plotarea_size[1] - text1[1] - text2[1]) / \
                 (p2[1] - p1[1]))
        shift = ((-p1[0] * scale[0]) + self.plotarea_origin[0] + \
                 text1[0],
                 (-p1[1] * scale[1]) + self.plotarea_origin[1] + \
                 text1[1])
        self._drawAxes(self.canvas, xaxis, yaxis, p1, p2,
                        scale, shift, xticks, yticks)
        graphics.fitToScale(scale, shift)
        graphics.draw(self.canvas)

    def _axisInterval(self, spec, lower, upper):
        if spec is None:
            return None
        if spec == 'minimal':
            if lower == upper:
                return lower - 0.5, upper + 0.5
            else:
                return lower, upper
        if spec == 'automatic':
            range = upper - lower
            if range == 0.:
                return lower - 0.5, upper + 0.5
            log = math.log10(range)
            power = math.floor(log)
            fraction = log - power
            if fraction <= 0.05:
                power = power - 1
            grid = 10.**power
            lower = lower - lower % grid
            mod = upper % grid
            if mod != 0:
                upper = upper - mod + grid
            return lower, upper
        if type(spec) == type(()):
            lower, upper = spec
            if lower <= upper:
                return lower, upper
            else:
                return upper, lower
        raise ValueError, str(spec) + ': illegal axis specification'

    def _drawAxes(self, canvas, xaxis, yaxis,
                  bb1, bb2, scale, shift, xticks, yticks):
        dict = {'anchor': N, 'fill': 'black'}
        if self.font is not None:
            dict['font'] = self.font
        if xaxis is not None:
        #draw x - axis
            lower, upper = xaxis
            text = 1
            once = 1
            for y, d in [(bb1[1], -3), (bb2[1], 3)]:
            #d=.5 of tick - length
                p1 = (scale[0] * lower) + shift[0], (scale[1] * y) + shift[1]
                if once: pp1 = p1
                p2 = (scale[0] * upper) + shift[0], (scale[1] * y) + shift[1]
                if once: pp2 = p2
                once = 0
                Line(self.canvas, p1[0], p1[1], p2[0], p2[1],
                     fill = 'black', width = 1)
                if xticks:
                    for x, label in xticks:
                        p = (scale[0] * x) + shift[0], \
                            (scale[1] * y) + shift[1]
                        Line(self.canvas, p[0], p[1], p[0], p[1] + d,
                             fill = 'black', width = 1)
                        if text:
                            dict['text'] = label
                            apply(CanvasText, (self.canvas, p[0],
                                               p[1] + 2), dict)    ##KGM 14 Aug 03
                text = 0
            #write x - axis title
            CanvasText(self.canvas,(pp2[0] - pp1[0]) / 2.+pp1[0],pp1[1] + 22, text = self.xtitle)
        #write graph title
        CanvasText(self.canvas,(pp2[0] - pp1[0]) / 2.+pp1[0],7, text = self.title) 
        dict['anchor'] = E
        if yaxis is not None:
            #draw y - axis
            lower, upper = yaxis
            text = 1
            once = 1
            for x, d in [(bb1[0], -3), (bb2[0], 3)]:
                p1 = (scale[0] * x) + shift[0], (scale[1] * lower) + shift[1]
                p2 = (scale[0] * x) + shift[0], (scale[1] * upper) + shift[1]
                if once: pp1 = p1 ;pp2 = p2
                once = 0
                Line(self.canvas, p1[0], p1[1], p2[0], p2[1],
                     fill = 'black', width = 1)
                if yticks:
                    for y, label in yticks:
                        p = (scale[0] * x) + shift[0], \
                            (scale[1] * y) + shift[1]
                        Line(self.canvas, p[0], p[1], p[0] - d, p[1],
                             fill = 'black', width = 1)
                        if text:
                            dict['text'] = label
                            apply(CanvasText,(self.canvas,
                                              p[0] - 4, p[1] + 2), dict)
                text = 0
            #write y - axis title
            CanvasText(self.canvas, pp2[0],pp2[1] - 10, text = self.ytitle)

    def _ticks(self, lower, upper):
        ideal = (upper - lower) / 7.
        log = math.log10(ideal)
        power = math.floor(log)
        fraction = log - power
        factor = 1.
        error = fraction
        for f, lf in self._multiples:
            e = math.fabs(fraction - lf)
            if e < error:
                error = e
                factor = f
        grid = factor * 10.**power
        if power > 3 or power < -3:
            format = '%+7.0e'
        elif power >= 0:
            digits = max(1, int(power))
            format = '%' + `digits`+'.0f'
        else:
            digits = -int(power)
            format = '%'+`digits + 2`+'.'+`digits`+'f'
        ticks = []
        t = -grid * math.floor(-lower / grid)
        while t <= upper and len(ticks) < 200:
            ticks.append((t, format % (t,)))
            t = t + grid
        return ticks

    _multiples = [(2., math.log10(2.)), (5., math.log10(5.))]

    def _textBoundingBox(self, text):
        bg = self.canvas.cget('background')
        dict = {'anchor': NW, 'text': text, 'fill': bg}
        if self.font is not None:
            dict['font'] = self.font
        item = apply(CanvasText, (self.canvas, 0., 0.), dict)
        bb = self.canvas.bbox(item)
        self.canvas.delete(item)
        return bb

    def replot(self):
        if self.last_drawn is not None:
            apply(self.draw, self.last_drawn)

    def clear(self):
        self.canvas.delete('all')

    def postscr(self, filename = None):
        """Write to Postscript file given by 'filename'. If none provided,
        ask user.
        """
        from tkFileDialog import asksaveasfilename
        if not filename:
            filename = asksaveasfilename()
        if filename:
            if not filename[-3:] == '.ps':
                filename += '.ps'
            self.canvas.postscript(width = self.width, height = self.height, file = filename)

class TextBox(Frame):
    def __init__(self, master, width, height,
                 background = 'white', boxtext = '', **kw):
        apply(Frame.__init__, (self, master), kw)
        self.width = width
        self.height = height
        self.canvas = Canvas(self, width = width, height = height,
                           background = background)
        self.canvas.pack(fill = BOTH, expand = YES)
        #CanvasText(self.canvas, text = boxtext)

    def postscr(self):
        #select output file
        #from tkFileDialog import asksaveasfilename
        filename = asksaveasfilename()
        if filename:
            if not filename[-3:] == '.ps':
                filename += '.ps'
            self.canvas.postscript(width = self.width, height = self.height, file = filename)
        
if __name__ == '__main__':
    print 'SimPlot.py %s'%__version__
    root = Tk()
    plt = SimPlot()
    root.title('SimPlot example - First frame')

    root1 = Tk()
    root1.title('SimPlot example - Second frame')
    
    """PARAMETER DEFAULTS:
    GraphBase
    ---------
    background = 'white',
    title = '',
    xtitle = '',
    ytitle = ''

    GraphBase.draw
    --------------
    xaxis = 'automatic',
    yaxis = 'automatic')
    
    GraphLine
    ---------
    color:       'black',
    width:        1,
    smooth:       0,
    splinesteps: 12

    GraphSymbols:
    -------------
    color: 'black',
    width: 1,
    fillcolor: 'black',
    size: 2,
    fillstyle: '',
    outline: 'black',
    marker: 'circle'}

    GraphBars
    ---------
    color: 'black',
    width: 1,
    fillcolor: 'black',
    size: 3,
    fillstyle: '', 
    outline: 'black'
    """
    # Plot 1 -- smooth line + filled bars
    di = 5.0 * pi / 40.
    data = []
    for i in range(40):
        data.append((float(i) * di,
                     (math.sin(float(i) * di) - math.cos(float(i) * di))))
    line1  = plt.makeLine(data, color = 'black', width = 1,
                      smooth = 1)
    line1a = plt.makeBars(data[1:], color = 'blue', fillstyle = 'gray25',
                      anchor = 0.0)
    

    graphObject = plt.makeGraphObjects([line1a, line1])
    #Second panel -- Narrow bars
    line2 = plt.makeBars([(0, 0),(1, 145),(2,-90),(3, 147),(4, 22),(5, 31),
                        (6, 77),(7, 125),(8, 220),(9, 550),(10, 560),(11, 0)],
                       outline = 'green', color = 'red', size = 7)


    graphObject2 = plt.makeGraphObjects([line2])

    # Third plot -- Smooth line and unsmoothed line 
    line3 = plt.makeLine([(1, 145 + 100),(2, 151 + 100),(3, 147 + 100),(4, 22 + 100),(5, 31 + 100),
                        (6, 77 + 100),(7, 125 + 100),(8, 220 + 100),(9, 550 + 100),(10, 560 + 100)],
                       color = 'blue', width = 2, smooth = 1)
    line3a = plt.makeLine([(1, 145),(2, 151),(3, 147),(4, 22),(5, 31),
                        (6, 77),(7, 125),(8, 220),(9, 550),(10, 560)],
                       color = 'green', width = 2, smooth = 0)
    line3b = plt.makeStep([(1, 145 + 100),(2, 151 + 100),(3, 147 + 100),(4, 22 + 100),(5, 31 + 100),
                        (6, 77 + 100),(7, 125 + 100),(8, 220 + 100),(9, 550 + 100),(10, 560 + 100)],
                       color = 'red', width = 2)
    
    graphObject3 = plt.makeGraphObjects([line3, line3a, line3b])
    
    # Fourth plot -- lines with all available symbols with different
    #                outline colors / fill colors / sizes
    
    line4 = plt.makeSymbols([(1, 100),(2, 100),(3, 100),(4, 100),(5, 100),
                        (6, 100),(7, 100),(8, 100),(9, 100),(10, 100)],
                       color = 'black', fillcolor = 'red', width = 2, marker = 'triangle')
    line5 = plt.makeSymbols([(1, 200),(2, 200),(3, 200),(4, 200),(5, 200),
                        (6, 200),(7, 200),(8, 200),(9, 200),(10, 200)],
                       color = 'red', width = 2, marker = 'circle')
    line6 = plt.makeSymbols([(1, 300),(2, 300),(3, 300),(4, 300),(5, 300),
                        (6, 300),(7, 300),(8, 300),(9, 300),(10, 300)],
                       color = 'green', width = 2, marker = 'dot')
    line7 = plt.makeSymbols([(1, 400),(2, 400),(3, 400),(4, 400),(5, 400),
                        (6, 400),(7, 400),(8, 400),(9, 400),(10, 400)],
                       color = 'blue', fillcolor = 'white',
                         size = 2, width = 2, marker = 'square')
    line8 = plt.makeSymbols([(1, 500),(2, 500),(3, 500),(4, 500),(5, 500),
                        (6, 500),(7, 500),(8, 500),(9, 500),(10, 500)],
                       color = 'yellow', width = 2, marker = 'triangle')
    line9 = plt.makeSymbols([(1, 600),(2, 600),(3, 600),(4, 600),(5, 600),
                        (6, 600),(7, 600),(8, 600),(9, 600),(10, 600)],
                       color = 'magenta', width = 2, marker = 'cross')
    line10 = plt.makeSymbols([(1, 700),(2, 700),(3, 700),(4, 700),(5, 700),
                        (6, 700),(7, 700),(8, 700),(9, 700),(10, 700)],
                       color = 'brown', width = 2, marker = 'plus')
    line11 = plt.makeSymbols([(1, 800),(2, 800),(3, 800),(4, 800),(5, 800),
                        (6, 800),(7, 800),(8, 800),(9, 800),(10, 800)],
                       color = 'black', fillcolor = 'orange',
                          width = 2, marker = 'triangle_down')
  

    graphObject4 = GraphObjects([line4, line5, line6, line7, line8,
                                 line9, line10, line11])

    # Two panels
    f1 = Frame(root)
    f2 = Frame(root1)
 
    graph={}
    # Plots 1 and 2 in panel f1, side by side
    graph[1] = plt.makeGraphBase(f1, 500, 300, title = 'Plot 1: 1 makeLine call, 1 makeBars call',
                         xtitle = 'the x-axis', ytitle = 'the y-axis')
    graph[1].pack(side = LEFT, fill = BOTH, expand = YES)
    graph[1].draw(graphObject, xaxis = 'minimal', yaxis = 'minimal')
    
    graph[2]  = plt.makeGraphBase(f1, 500, 300, title = 'Plot 2: 1 makeBars call',
                        xtitle = 'time', ytitle = 'pulse [volt]')
    # Set side - by - side plots
    graph[2].pack(side = LEFT, fill = BOTH, expand = YES)
    graph[2].draw(graphObject2, 'minimal', 'automatic')
       
    # Pack panel 1 to make it visible
    f1.pack()
    
    # Plots 2 and 3 in panel f2, one under the other
    graph[3]  = plt.makeGraphBase(f2, 500, 300,
                        title = 'Plot 3: 2 makeLine call (smooth, not smooth); 1 makeStep call')
    graph[3].pack(side = TOP, fill = BOTH, expand = YES)
    graph[3].draw(graphObject3)
    
    graph[4]  = plt.makeGraphBase(f2, 500, 300, border = 3, title = 'Plot 4: 8 makeSymbols calls')
    # Set one - over - other configuration of plots
    graph[4].pack(side = TOP, fill = BOTH, expand = YES)
    graph[4].draw(graphObject4)

    # Pack panel 2 to make it visible
    f2.pack()

    # Save graph[1] to Postscript file (user selects filename)
    graph[1].postscr()
        
    # end plotting stuff

    #### Very Important -- get Tk going by starting event loop
    plt.mainloop()
