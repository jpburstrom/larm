#!/usr/bin/env python

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

    def contentsMouseMoveEvent(self,e):pass
      #  if  self.__moving :
      #      point = self.inverseWorldMatrix().map(e.pos());
      #      self.__moving.moveBy(point.x() - self.__moving_start.x(),point.y() - self.__moving_start.y())
      #      self.__moving_start = point
      #  self.canvas().update()


class MarioDots(QFrame):
    
    def __init__(self,parent,name,f=0):
        QMainWindow.__init__(self,parent,name,f)
        self.canvas=QCanvas(300,300)
        self.canvas.setUpdatePeriod(40)
        self.editor=_FigureEditor(self.canvas,self,name,f)
        self.container = QRect() # the container within
        self.sets = {} #sets of dots
        self.texts = {} #sets of dots
        self.baseX = 0
        self.baseY = 0
        self.canvas.setBackgroundColor(QColor(150, 200, 240))
        self.canvas.oldbackground = self.canvas.backgroundColor()
        self.addBorder()
        self.baseX = self.container.width() + self.container.left()
        
        self.active = 0
    
    def mousePressEvent(self, e):
        self.canvas.oldbackground = self.canvas.backgroundColor()
        self.canvas.setBackgroundColor(QColor(240, 240, 240))
        qApp.setOverrideCursor(QCursor(Qt.BlankCursor))
        self.cpos = self.mapToGlobal(e.pos())
        self.emit(PYSIGNAL("canvasActive"), (True,))
        self.active = 1
        
    def mouseReleaseEvent(self, e):
        self.canvas.setBackgroundColor(self.canvas.oldbackground)
        qApp.restoreOverrideCursor()
        QCursor.setPos(self.cpos)
        self.set_inactive()
    
    def set_inactive(self):
        self.emit(PYSIGNAL("canvasActive"), (False,))
        self.active = 0
        
    def newset(self, label):
        """Init a set of dots"""        
        if not self.sets.has_key(label): 
            dots = self.initSprites(5)
            self.sets[label] = [dots, True]
            texts = self.initText(5)
            self.texts[label] = [texts, True]

            
    def hideset(self, label):
        """Hide a dot set"""
        for item in self.sets[label][0]:
            item.hide()
    
    def hidetext(self, label):
        """Hide a dot set"""
        for item in self.texts[label][0]:
            item.hide()
    
    def showset(self, label):
        """Show a dot set"""
        for item in self.sets[label][0]:
            item.show()
        self.emit(PYSIGNAL("emitlabel"), (QString(label),))
    
    def showtext(self, label):
        """Show a dot set"""
        for item in self.texts[label][0]:
            item.show()
    
    def emitlabel(self, foo):
        return foo

    def getscale(self):
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
    
    
    def settext(self, label, n, x, y):
        
        if x is not None and y is not None:
            k = "%.3f/%.3f" % (x, y)
        elif y is not None:
            k = "%.3f" % y
        elif x is not None:
            k = "%.3f" % x
        else:
            k = ''
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
        i.setPen( QPen(QColor(0,0,0), 2) )
        i.setZ(0)
        i.show()


if __name__=='__main__':
    app=QApplication(sys.argv)

    m=MarioDots(None,"pyqt canvas example")

    qApp.setMainWidget(m)
    m.setCaption("Qt Canvas Example ported to PyQt")
    if QApplication.desktop().width() > m.width() + 10 and QApplication.desktop().height() > m.height() + 30:
        m.show()
    else:
        m.showMaximized()

    m.show();
    m.newset("test")
    m.showset("test")
    m.showtext("test")
    m.movedots("test", [(0,0), (30,30), (50,50), (70,70), (90,90)])
    
    QObject.connect( qApp, SIGNAL("lastWindowClosed()"), qApp, SLOT("quit()") )
    app.exec_loop()
