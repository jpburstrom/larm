# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision: 51 $"

import os, sys
from qt import *
from qtcanvas import *
from sqlobject import *
from numpy import *
import random
import string
from tag_editor import dbSoundFiles, dbTags, DB_PATH

class _SampleItem(QCanvasRectangle):
    def __init__(self,canvas, path, params, widget):
        QCanvasRectangle.__init__(self, canvas)
        self.setSize(8,8)
#        self.setPen(QPen(QColor(color), 2))
        self.setBrush(QBrush(QColor("black"), Qt.SolidPattern))
        self.path = path
        self.name = path.split("/")[-1]
        self.data = params
        self.show()
        
        self.canvas_size = widget.container.size();
        
    def my_move(self, x = None, y = None):
        """Move w/ args relative to canvas size (0-1)
        """
        s = self.canvas_size
        if x and y:
            self.move(x * s.width(), ((-1 * y) + 1 )* s.height())
        elif x and not y:
            self.setX(x * s.width())
        elif y and not x:
            self.setY(((-1 * y) + 1 )* s.height())
            
    def flash(self):
        """Flash when selected.
        """
        self.setBrush(QBrush(QColor("white"), Qt.SolidPattern))
        QTimer.singleShot(400, self.unflash)
    
    def unflash(self):
        self.setBrush(QBrush(QColor("black"), Qt.SolidPattern))

class _FigureEditor(QCanvasView):
    def __init__(self,c,parent,name,f):
        QCanvasView.__init__(self,c,parent,name,f)
        self.adjustSize()
        self.ResizePolicy(self.AutoOne)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        self.viewport().setMouseTracking(1)

    def clear(self):
        ilist = self.canvas().allItems()
        for each_item in ilist:
            if each_item:
                each_item.setCanvas(None)
                del each_item
        self.canvas().update()

    def contentsMouseMoveEvent(self,e):
        [self.parent().hoverSample(samp) for samp in self.canvas().collisions(e.pos()) 
            if isinstance(samp, _SampleItem)]

class SampleViewer(QVBox):
    """Shows samples in a canvas. 
    """
    def __init__(self,parent,name=None,f=0):
        QVBox.__init__(self,parent,name,f)
        font = QFont()
        font.setBold(1)
        self.ylabel = QLabel("", self)
        self.ylabel.setFont(font)
        
        self.canvas=QCanvas(700,700)
        self.canvas.setUpdatePeriod(40)
        self.editor=_FigureEditor(self.canvas,self,name,f)
        self.canvas.setBackgroundColor(QColor(100, 100, 100))
        self.container = QRect() # the container within
        
        self.xlabel = QLabel("", self)
        self.xlabel.setAlignment(Qt.AlignRight)
        self.xlabel.setFont(font)
        
        self.addBorder()
        self.baseX = self.container.width() + self.container.left()
        
        self.text = QCanvasText(self.canvas)
        self.text.setColor(QColor("white"))
        self.text.setZ(10000)
        
        
        self.popup = QPopupMenu(self)
        self.parampopup_x = QPopupMenu(self.popup)
        self.popup.insertItem(QString("Change X"), self.parampopup_x)
        self.parampopup_y = QPopupMenu(self.popup)
        self.popup.insertItem(QString("Change Y"), self.parampopup_y)
        
        self.popup.insertSeparator()
        self.popup.insertItem(QLabel("Send current to:", None))
        
      #  self.setup_data()
        
        self.connect(self.popup, SIGNAL('activated(int)'), self.select_sample)
        self.connect(self.parampopup_x, SIGNAL('activated(int)'), self.change_x)
        self.connect(self.parampopup_y, SIGNAL('activated(int)'), self.change_y)
        
        
        self.active = 0
        self.playprocess = 0
    
    def mousePressEvent(self, e):
        """Detects if a sample is pressed"""
##        [self.selectSample(samp) for samp in self.canvas.collisions(e.pos()) 
##            if isinstance(samp, _SampleItem)]
    
    def contextMenuEvent(self, e):
        self.popup.popup(self.mapToGlobal(e.pos()))
    
    def new_receiver(self, name):
        """Adds a new receiver (for sample selection) to the canvas.
        """
        self.popup.insertItem(name)
    
    def change_x(self, i):
        """Change X display parameter.
        """
        t = str(self.sender().text(i))
        self.xlabel.setText(t)
        self.changeParams(t, None)
    
    def change_y(self, i):
        """Change Y display parameter.
        """
        t = str(self.sender().text(i))
        self.ylabel.setText(t)
        self.changeParams(None, t)
    
    def add_sample(self, path, params):
        """Add samples to the canvas.
        
        Arg is list of dictionaries.
        """
        l = _SampleItem(self.canvas, path, params, self)
    
    def changeParams(self, x = None, y = None):
        if x and not y:
            [l.my_move(l.data[x], None) for l in self.canvas.allItems() \
                if isinstance(l, _SampleItem)]
        elif y and not x: 
            [l.my_move(None, l.data[y]) for l in self.canvas.allItems() \
                if isinstance(l, _SampleItem)]
        else:
            [l.my_move(l.data[x], l.data[y]) for l in self.canvas.allItems() \
                if isinstance(l, _SampleItem)]
    
    def hoverSample(self, samp):
        """Called when moving the pointer over the sample.
        
        Updates and moves text label, and selects the sample to be current.
        """
        
        self.text.setText(samp.name)
        self.text.move(min(self.canvas.width()-self.text.boundingRect().width(), \
            samp.x()+8), samp.y()-4)
        self.text.show()
        self.current_sample = samp
    
    def select_sample(self, i):
        """Select and send current sample.
        """
        recv = str(self.sender().text(i))
        samp = self.current_sample
        samp.flash()
        self.emit(PYSIGNAL("selected_sample"), (recv, samp.path))
        self.soundplayer(1, samp.path)
            
    def addBorder(self):
        """Add border to canvas."""
        self.spritesize = 8
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
    
    def setup_db(self):
        """Make initial db connection"""
        
        db_filename = os.path.abspath(DB_PATH)
        connection_string = 'sqlite://' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
    
    def setup_data(self):
        """Get data from db and extract usable features for display.
        """
        
        self.setup_db()
        samples = dbSoundFiles.selectBy(active=True)
        n = samples.count()
        paths = []
        f = {"centroid" : zeros(n),
            "flatness" : zeros(n),
            "power" : zeros(n),
            "length" : zeros(n),
            "onsets" : zeros(n)
            }
        for sample in samples:
            paths.append(sample.fullPath)
            n = paths.index(sample.fullPath)
            f["centroid"][n] = sample.spectral_centroid
            f["flatness"][n] = sample.spectral_flatness
            f["onsets"][n] = float(sample.onsets) / sample.size
            f["power"][n] = sample.power
            f["length"][n] = sample.size
        c = 20./log(10)
        for k, v in f.items():
            f[k] = (v - min(v)) / (max(v) - min(v))
            self.parampopup_x.insertItem(k)
            self.parampopup_y.insertItem(k)
        for p in paths:
            self.add_sample(p, dict([(parm, f[parm][paths.index(p)]) for parm in f]))
    
    def soundplayer(self, play, file=None):
        if self.playprocess and play:
            self.soundplayer(False)
        if play and file:
            self.playprocess = os.spawnvp(os.P_NOWAIT, 'aplay',  ('aplay', '-q', file))
        elif not play:
            os.kill(self.playprocess, 15)
            self.playprocess = None
            
if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    j = [
        {'path' : '/path', 'name' : 'foo', 'param1' : 0.0, 'param2' : 0.0},
        {'path' : '/pathk', 'name' : 'goo', 'param1' : 1.0, 'param2' : 1.0}
        ]
    items = []
    for i in range(100):
        n = "".join(random.choice(string.letters) for i in range(5))
        p = "/"+"".join(random.choice(string.letters) for i in range(5))
        x = random.random()
        y = random.random()
        items.append({'path': p, 'name': n, 'param1': x, 'param2': y})
    params = ["param1", "param2"]
    w = SampleViewer(None)
    w.new_receiver("Fussball")
    w.setup_data()
    w.changeParams('onsets', 'power')
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
