# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'popuplist.ui'
#
# Created: mån feb 19 15:33:25 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!


import sys, os
from qt import *
from sqlobject import *
from larmglobals import getgl


class dbSoundFiles(SQLObject):
    fullPath = StringCol()
    hash = StringCol(length=32)
    active = BoolCol(default=True)
    size = IntCol()
    channels = IntCol()
    samplerate = IntCol()
    tags = RelatedJoin('dbTags')

class dbTags(SQLObject):
    name = StringCol()
    dbSoundFiles = RelatedJoin('dbSoundFiles')
    
class SampleList(QWidget):
    """Load tagged soundfile from database and display them in a neat window
    
    It currently loads all tags and soundfile paths into memory. This might be a problem in 
    the future, with many soundfiles.
    """
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("Form3")
        
        audiodb_path = getgl('audiodb_path')
        if audiodb_path[0] != "/" :
            audiodb_path = "".join((sys.path[0], "/", audiodb_path))
        
        db_filename = os.path.abspath(audiodb_path)
        connection_string = 'sqlite://' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
        
        self.destinations = []
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
        textLabel2_font.setFamily("Pigiarniq Heavy")
        textLabel2_font.setPixelSize(12)
        self.label = QLabel(name, self)
        self.label.setPaletteForegroundColor(QColor(255,255,255))
        self.label.setFont(textLabel2_font)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(QRect(0,0,200,20))
        
        self.mainBox = QListBox(self,"mainBox")
        self.mainBox.setGeometry(QRect(0,20,200,200))
        self.mainBox.setFocusPolicy(QWidget.NoFocus)
        
        self.mainBox.setPaletteForegroundColor(QColor(255,200,0))
        self.mainBox.setPaletteBackgroundColor(QColor(0,0,0))
        self.mainBox.setVScrollBarMode(QScrollView.AlwaysOff)
        
    
        self.popupBox = QListBox(self,"popupBox")
        self.popupBox.setGeometry(QRect(20,20,140,190))
        self.popupBox.setPaletteForegroundColor(QColor(255,255,255))
        self.popupBox.setPaletteBackgroundColor(QColor(0,0,0))
    
        self.tag = ''
        self.sample = ''
        self.destination = ''

        self.viewingtags = False
        self.populate()

        self.clearWState(Qt.WState_Polished)

        self.connect(self.mainBox,SIGNAL("mouseButtonClicked(int, QListBoxItem*,const QPoint&)"),self.onClick)
        self.connect(self.popupBox,SIGNAL("mouseButtonClicked(int, QListBoxItem*,const QPoint&)"),self.selectDest)
        self.connect(qApp, PYSIGNAL("new_sampler"), self.new_sampler)
    
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

    def new_sampler(self, name):
        self.destinations.append(name)
        #a bit redundant...
        self.populate()
    
    def addtag(self, tag):
        self.tags.insert(0, tag)
        self.samples[tag] = {}
        self.populate()
        
    def addsample(self, tag, list):
        self.samples[tag][list[0].split("/")[-1].split(".")[0]] = list

    def populate(self):
        self.popupBox.clear()
        for p in self.destinations:
            self.popupBox.insertItem(p)
            self.popupBox.adjustSize()
        self.popupBox.hide()
        self.switchview()
    
    def reset(self):
        self.popupBox.hide()
        self.viewingtags = False
        self.switchview()

    def switchview(self, text = None):
        self.mainBox.clear()
        if text:
            self.viewingtags = False
            self.tag = text
            k = [i[0] for i in sorted(self.samples[text].items())]
        else:
            k = self.tags
            self.viewingtags = True
        for p in k:
            self.mainBox.insertItem(p)

    def onClick(self,i, a0,a1 ):
        if a0:
            if i == 1:
                if self.viewingtags:
                    self.switchview(str(a0.text()))
                else:
                    self.sample = str(a0.text())
                    self.popupBox.move(70, max(self.popupBox.mapFromGlobal(a1).y(), 0))
                    self.popupBox.show()
        if i == 2 and self.viewingtags == False:
            self.reset()

    def selectDest(self, i,  a0, a1):
        if i == 1:
            self.destination = a0.text()
            self.switchview()
            self.popupBox.hide()
            qApp.emit(PYSIGNAL("load_sample"),(self.samples[self.tag][self.sample], self.destination))
        else:
            self.reset()

if __name__ == "__main__":
    def sort_by_filename(paths):
        paths[:] = [(x.split("/")[-1], x) for x in paths]
        paths.sort()
        print paths
        paths[:] = [val for (key, val) in paths]

    path = ["a/e", "e/a", "b/f"]
    sort_by_filename(path)
    print path
    
