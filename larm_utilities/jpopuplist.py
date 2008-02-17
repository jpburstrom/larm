# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"


import sys, os
from qt import *
from sqlobject import *
from larmglobals import getgl

from tag_editor import dbSoundFiles, dbTags, DB_PATH

class _MyListBox(QListBox):
    def __init__(self, *args):
        QListBox.__init__(self, *args)
        self.dragging = False
        self.viewingtags = True
        self.current = False
        
    def mousePressEvent(self, ev):
        QListBox.mousePressEvent(self, ev)
        if ev.button() == 1:
            if self.viewingtags:
                self.viewingtags = self.parent().switchview(str(self.currentText()))
            else:
                self.dragging = True
        elif ev.button() == 2:
            self.viewingtags = self.parent().switchview()
    
    def mouseReleaseEvent(self, ev):
        QListBox.mouseReleaseEvent(self, ev)
        self.dragging = False

    def mouseMoveEvent(self, ev):
        p = self.parent()
        if self.dragging and not p.viewingtags:
            self.current = p.samples[p.tag][str(self.currentText())]
            d = QTextDrag(self.current[0].split("/")[-1].split(".wav")[0], self)
            d.dragCopy()
            self.dragging = False

class SampleList(QVBox):
    """Load tagged soundfile from database and display them in a neat window
    
    It currently loads all tags and soundfile paths into memory. This might be a problem in 
    the future, with many soundfiles.
    """
    def __init__(self,parent = None,name = None,fl = 0):
        QVBox.__init__(self,parent,name,fl)

        if not name:
            self.setName("Form3")
        
        db_filename = os.path.abspath(DB_PATH)
        connection_string = 'sqlite://' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
        
        self.tags = self.alltags()
        self.tags.append('@ALL')
        self.tags.sort()
        self.samples = {}
        
        for tag in self.tags:
            self.samples[tag] = {}
            if tag == '@ALL':
                paths = self.findfilesfromtag()
            else:
                paths = self.findfilesfromtag(tag)
            self.sort_by_filename(paths)
            for i in paths:
                self.samples[tag][i[0].split("/")[-1].split(".")[0]] = i
        
        textLabel2_font = QFont(self.font())
        textLabel2_font.setPixelSize(9)
        
        icon_path = "/home/johannes/myprojects/larm/trunk/icons/"
        self.icon_dn = QPixmap(icon_path+"arrow_down.png")
        self.icon_up = QPixmap(icon_path+"arrow_up.png")
        self.icon_star = QPixmap(icon_path+"star.png")
        self.icon_vector = QPixmap(icon_path+"vector.png")
        
        grp = QHButtonGroup(self)
        grp.setInsideMargin(0)
        grp.setInsideSpacing(1)
        b = QPushButton(grp)
        b.setPixmap(self.icon_star)
        b = QPushButton(grp)
        b.setPixmap(self.icon_vector)
        b = QPushButton(grp)
        b.setPixmap(self.icon_dn)
        
        self.connect(grp, SIGNAL("pressed(int)"), self.resort)
        
        self.mainBox = _MyListBox(self,"mainBox")
        self.mainBox.setAcceptDrops(1)
        self.mainBox.setGeometry(QRect(0,20,200,200))
        self.mainBox.setFocusPolicy(QWidget.NoFocus)
        self.mainBox.setFont(textLabel2_font)
        
        self.mainBox.setPaletteForegroundColor(QColor(255,200,0))
        self.mainBox.setPaletteBackgroundColor(QColor(0,0,0))
        self.mainBox.setVScrollBarMode(QScrollView.AlwaysOff)
    
        self.tag = ''
        self.sample = ''
        self.destination = ''

        self.viewingtags = False
        self.populate()

        self.clearWState(Qt.WState_Polished)
        
    def findfilesfromtag(self, tag = None):
        if tag:
            tagObj = dbTags.selectBy(name=tag)
        else:
            tagObj = dbTags.select()
        fl = []
        for tag in tagObj:
            [fl.append([t.fullPath, str(t.size), t.samplerate, t.channels]) \
            for t in tag.dbSoundFiles if t.active is True]
        return fl
    
    def alltags(self):
        tagObj = dbTags.select()
        tl = []
        for tag in tagObj:
            tl.append(tag.name)
        return tl
    
    def sort_by_filename(self, paths):
        paths[:] = [(x[0].split("/")[-1], x) for x in paths]
        paths.sort()
        paths[:] = [val for (key, val) in paths]

    def addtag(self, tag):
        self.tags.insert(0, tag)
        self.samples[tag] = {}
        self.populate()
        
    def addsample(self, tag, list):
        self.samples[tag][list[0].split("/")[-1].split(".")[0]] = list

    def populate(self):
        self.switchview()
    
    def reset(self):
        self.viewingtags = False
        self.switchview()

    def switchview(self, text = None):
        self.mainBox.clear()
        if text:
            self.viewingtags = False
            self.tag = text
            k = [i[0] for i in self.sort(self.samples[text].items())]
        else:
            k = self.tags
            self.viewingtags = True
        [self.mainBox.insertItem(p) for p in k]
        return self.viewingtags

    def onClick(self,i, a0,a1 ):
        if a0:
            if i == 1:
                if self.viewingtags:
                    self.switchview(str(a0.text()))
                else:
                    self.sample = str(a0.text())
                    self.popupBox.show()
        if i == 2 and self.viewingtags == False:
            self.reset()

    def selectDest(self, i,  a0, a1):
        if i == 1:
            self.destination = a0.text()
            self.switchview()
            qApp.emit(PYSIGNAL("load_sample"),(self.samples[self.tag][self.sample], self.destination))
        else:
            self.reset()
    
    def sort(self, it):
        return sorted(it)
        
            
    def resort(self, i):
        if i is 0:
            pass
        if i is 1:
            pass
        if i is 2:
            pass

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = SampleList(None)
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
