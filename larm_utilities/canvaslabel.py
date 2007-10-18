# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/johannes/python/sc/canvaslabel.ui'
#
# Created: tis feb 20 14:15:29 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *
from qttable import QTable

from larmglobals import getgl

class Canvasinfo(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("Canvasinfo")

        self.canvaslabels = QTable(self,"canvaslabels")
        self.canvaslabels.setNumCols(2)
        self.canvaslabels.horizontalHeader().setLabel(0,"X")
        self.canvaslabels.horizontalHeader().setLabel(1,"Y")
        
        self.canvaslabels.setNumRows(5)
        for i in range (5):
            #FIXME:pahts....
            self.canvaslabels.verticalHeader().setLabel(i,
                QIconSet(QPixmap("larm_utilities/sprite%d.png" % (i + 1))),QString.null)
        self.canvaslabels.setGeometry(QRect(0,20,300,128))

        self.canvaslabels.setCursor(QCursor(13))
        self.canvaslabels.setFocusPolicy(QTable.NoFocus)
        self.canvaslabels.setFrameShape(QTable.StyledPanel)
        self.canvaslabels.setResizePolicy(QTable.AutoOne)
        self.canvaslabels.setReadOnly(1)
        self.canvaslabels.setSelectionMode(QTable.NoSelection)
        self.canvaslabels.setFocusStyle(QTable.FollowStyle)

        self.label = QLabel(self,"label")
        self.label.setGeometry(QRect(0,0,300,20))
        self.label.setPaletteForegroundColor(QColor('gold'))
        label_font = QFont(self.label.font())
        label_font.setFamily("Pigiarniq Heavy")
        self.label.setFont(label_font)
        self.label.setAlignment(Qt.AlignCenter)
        
        self.canvaslabels.setPaletteBackgroundColor(QColor(50, 50, 50))
        self.canvaslabels.setPaletteForegroundColor(QColor('gold'))
        self.canvaslabels.setColumnWidth(0, 132)
        self.canvaslabels.setColumnWidth(1, 132)
        self.canvaslabels.setShowGrid(False)

        self.clearWState(Qt.WState_Polished)
        
        self.connect(self,PYSIGNAL("showMachineLabel"),self.updateLabels)
        self.connect(self,PYSIGNAL("hideMachineLabel"),self.deleteLabels)

    def deleteLabels(self):
        self.label.setText(QString())
        for r in range(5):
            for c in range(2):
                self.canvaslabels.setText(r, c, QString())
    
    def updateLabels(self,d):
        #set label[0] as main label
            self.label.setText(d[0])
        #recurse through label[1] and set them
            for r in range(len(d[1])):
                for c in range(len(d[1][r])):
                    self.canvaslabels.setText(r, c, QString(d[1][r][c]))
        

    def __tr(self,s,c = None):
        return qApp.translate("Canvasinfo",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = Canvasinfo()
    a.setMainWidget(w)
    d = ('This is a label', [
        ['label1x', 'label1y'],
        ['label2x', 'label2y'],
        ['label3x', 'label3y'],
        ['label4x', 'label4y'],
        ['label5x', 'label5y']
        ] )
    w.updateLabels(d)
    w.updateLabels(d)
    w.show()
    a.exec_loop()
