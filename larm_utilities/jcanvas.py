# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"

import sys
from qt import *
from qtcanvas import *
import random


True = 1
False = 0
logo_fn = QString.null
logoimg = []
bouncy_logo = None


class _ImageItem(QCanvasRectangle):
    def __init__(self,color,canvas):
        QCanvasRectangle.__init__(self,canvas)
#        self.image=img
#        self.pixmap=QPixmap()
#        self.setSize(self.image.width(), self.image.height())
        self.setSize(12,12)
        self.setPen(QPen(QColor(color), 2))
        self.setBrush(QBrush(QColor("grey"), Qt.Dense4Pattern))
        #self.pixmap.convertFromImage(self.image, Qt.OrderedAlphaDither);

#    def drawShape(self,p):
#        p.drawPixmap( self.x(), self.y(), self.pixmap )


class _FigureEditor(QCanvasView):
    def __init__(self,c,parent,name,f):
        QCanvasView.__init__(self,c,parent,name,f)
        self.__moving=0
        self.__moving_start= 0
        self.adjustSize()
        self.ResizePolicy(self.AutoOne)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def clear(self):
        ilist = self.canvas().allItems()
        for each_item in ilist:
            if each_item:
                each_item.setCanvas(None)
                del each_item
        self.canvas().update()

    def contentsMouseMoveEvent(self,e):
        if self.__moving:
            point = self.inverseWorldMatrix().map(e.pos());
            self.__moving.moveBy(point.x() - self.__moving_start.x(),point.y() - self.__moving_start.y())
            self.__moving_start = point
            self.canvas().update()


class MarioDots(QHBox):
    """A display-only canvas with 5 dots.
    
    Used for displaying data, represented as 5 x/y points on a 
    canvas. The canvas have sets of dots that can be shown/hidden,
    and each dot is moved independently."""
    def __init__(self,parent,name,f=0):
        QHBox.__init__(self,parent,name,f)
        self.canvas=QCanvas(300,300)
        self.canvas.setUpdatePeriod(40)
        self.editor=_FigureEditor(self.canvas,self,name,f)
        self.canvas.setBackgroundColor(QColor(200, 200, 200))
        self.container = QRect() # the container within
        self.sets = {} #sets of dots
        self.texts = {} #sets of dots
        self.baseX = 0
        self.baseY = 0
        self.addBorder()
        self.baseX = self.container.width() + self.container.left()
        
        pen = QPen(QColor("white"), 1, Qt.DotLine)
        for i in (77,149,221):
            line = QCanvasLine(self.canvas)
            line.setPen(pen)
            line.setPoints(0,i,300,i)
            line.show()
            line = QCanvasLine(self.canvas)
            line.setPen(pen)
            line.setPoints(i,0,i,300)
            line.show()
        self.active = 0
    
    def mousePressEvent(self, e):
        """Mouse press activates canvas"""
        
        self.canvas.setBackgroundColor(QColor(150, 200, 240))
        qApp.setOverrideCursor(QCursor(Qt.BlankCursor))
        self.cpos = self.mapToGlobal(e.pos())
        self.emit(PYSIGNAL("canvasActive"), (True,))
        self.active = 1
        
    def mouseReleaseEvent(self, e):
        """Mouse release deactivates canvas"""
        
        self.canvas.setBackgroundColor(QColor(200, 200, 200))
        qApp.restoreOverrideCursor()
        QCursor.setPos(self.cpos)
        self.set_inactive()
    
    def set_inactive(self):
        """Programatically set canvas inactive"""
        
        self.emit(PYSIGNAL("canvasActive"), (False,))
        self.active = 0
        
    def newset(self, obj):
        """Init a set of dots"""
        label = obj.label
        if not self.sets.has_key(label): 
            dots = self.initSprites(5)
            self.sets[label] = [dots, True]
            texts = self.initText(5)
            self.texts[label] = [texts, True]
            
    def hideset(self, label):
        """Hide a dot set"""
        [item.hide() for item in self.sets[label][0]]
        [item.hide() for item in self.texts[label][0]]
    
    def showset(self, label):
        """Show a dot set"""
        [item.show() for item in self.sets[label][0]]
        self.emit(PYSIGNAL("emitlabel"), (QString(label),))
        [item.show() for item in self.texts[label][0]]
    
    def emitlabel(self, foo):
        """Does nothing. I think."""
        return foo

    def getscale(self):
        """Get current canvas scale"""
        return self.container.width(), self.container.height()

    def movedot(self,label, n, x = 0, y = 0):
        """Moves a dot n for current label to pos x, y
        
        Args:
        label: Unique string for current machine
        n: Which dot? Corresponding to mouse button
        x: current x pos as scaled value (multiply 0-1 w/ value from getscale())
        y: current y pos as scaled value """
        
        self.sets[label][0][n].move(x,y)
        self.texts[label][0][n].move(min((210,x+13)),y-2)
    
    def setlabels(self, obj):
        """Set labels for a dot set."""
        [self.texts[obj.label][0][i].setText(\
            "%s/%s" % n) for i, n in enumerate(obj.label_tuple[1])]
    
    def settext(self, label, n, x, y):
        """Silly name. Sets current dot values instead of labels."""
        if not None in (x, y):
            k = "%.3f/%.3f" % (x, y)
        else:
            k = "%.3f" % y or x
        self.texts[label][0][n].setText(k)
    
    def movedots(self, label, dotlist):
        """Moves all dots for current label
        
        Args:
        label: Unique string for current machine
        dotlist: a list of lists (or None's) with x, y positions (scaled to right size), sorted by index. """
        
        lust = self.sets[label]
        for key, item in enumerate(dotlist):
            if item:
                lust[0][key].move(item[0], item[1])
                self.texts[label][0][key].move(item[0]+13, item[1])
            
    def zoomIn(self): #Currently not in use
        m = self.editor.worldMatrix()
        m.scale( 2.0, 2.0 )
        self.editor.setWorldMatrix( m )

    def zoomOut(self): #Currently not in use
        m = self.editor.worldMatrix()
        m.scale( 0.5, 0.5 )
        self.editor.setWorldMatrix( m )

    def initSprites(self, num):
        colors = ["black", "red", "green", "blue", "yellow"]
        dots = []
        for n in range(num):
            dots.append(_ImageItem(colors[n], self.canvas))
            dots[n].move(0.0,0.0)
        return dots

    def initText(self, num): 
        texts = []
        for n in range(num):
            i = QCanvasText(self.canvas)
            i.setText("0.0")
            i.move(0.0,0.0)
            texts.append(i)
        return texts

    def addBorder(self):
        self.spritesize = 12
        self.topleft = self.spritesize/2
        xy = self.topleft
        w = self.canvas.width() - self.spritesize
        h = self.canvas.height() - self.spritesize
        c = QRect(xy,xy,w,h)
        self.container = c
        i = QCanvasRectangle( c, self.canvas)
        self.container.moveBy(-8, -8)
        i.setPen( QPen(QColor("white"), 2) )
        i.setZ(0)
        i.show()
