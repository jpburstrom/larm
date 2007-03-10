# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/johannes/python/sc/snapbuttons.ui'
#
# Created: fre feb 23 13:11:34 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *

#THIS BASTARD HAS MOVED TO jmachine.py

class SnapButton(QPushButton):
    """Special instance of QPushButton w/ some gui tricks adapted for use with SnapButtonGroup"""
    def __init__(self,parent = None,name = None,fl = 0):
        self.parent = parent
        self.button = 0
        self.event = 0
        self.saved = False
        QPushButton.__init__(self, parent,name)
    def mousePressEvent(self, e):
        QPushButton.mousePressEvent(self, e)
        self.event = e
    def eventState(self):
        return self.event
    def setsaved(self):
        self.setPaletteBackgroundColor(QColor(200,200,200))
        self.saved = True
    def issaved(self):
        return self.saved
            
class SnapButtonGroup(QHButtonGroup):
    """A group with buttons to select and save snapshots of settings. 
        Calls parent methods saveSnapshot and recallSnapshot.
        Right-Left-click to save, Left-click to recall. """
    def __init__(self,parent,number=4,name = None,fl = 0):
        QHButtonGroup.__init__(self,parent,name)

        if not name:
            self.setName("Form")
        self.backgroundColor = (100,100,100)
        self.buttons = []
        for i in range (number):
            self.buttons.append(SnapButton(self, "pushButton" + str(i)))
            self.buttons[i].setText(str(i))
        self.clearWState(Qt.WState_Polished)
        self.connect(self, SIGNAL("clicked(int)"), self.handleclick)
        self.adjustSize()
    
    def handleclick(self, click):
        k = self.buttons[click]
        try:
            p = k.eventState().state()
        except AttributeError:
            p = 1
        if  p == 1 and k.issaved(): # if normal click
            dbp( "Snapshot recalled")
            self.parent().recall_snapshot(click)
        elif p == 3: #if rightclick-leftclick
            k.setsaved()
            dbp("Snapshot saved")
            self.parent().save_snapshot(click)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = SnapButtonGroup(None)
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
