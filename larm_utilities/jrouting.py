# -*- coding: utf-8 -*-

import sys
from qt import *
from qttable import QTable, QTableItem

class RoutingProgress(QProgressBar):
    def __init__(self, totalsteps, progress, parent = None, name=None, fl = 0):
        QProgressBar.__init__(self,totalsteps, parent,name,fl)
        
        self.setProgress(progress)
        self.setPercentageVisible(False)

class RoutingSlider(QSlider):
    def __init__(self, v, p):
        QSlider.__init__(self, 0,1000,1,v,Qt.Horizontal,p, "slider")


class Routing(QWidget):
    """A variable-sized table with sliders, ideal for signal routing purposes."""
    def __init__(self, row, col, routeToSelf = True, parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)
        if not name:
            self.setName("Form4")
        self.routeToSelf = routeToSelf
        self.empty_cells = [] 
        self.sliderat = (0 , 0)
        self.currentvalue = None #holds current slider value

        self.table1 = QTable(self,"table1")
        self.table1.setPaletteBackgroundColor(QColor(0,0,0))
        self.table1.viewport().setPaletteBackgroundColor(QColor(0,0,0))
        self.table1.setResizePolicy(QTable.AutoOne)
        self.table1.setVScrollBarMode(QTable.AlwaysOff)
        self.table1.setHScrollBarMode(QTable.AlwaysOff)
        self.table1.setShowGrid(0)
        self.table1.setReadOnly(1)
        self.table1.setSelectionMode(QTable.Single)
        self.table1.setFocusPolicy(QWidget.NoFocus)
        self.values = [] #holds all items
        self.columnwidth = 50
        self.setsize(row, col)
        self.adjustSize()
        self.ptimer = QTimer()        
        QObject.connect(self.ptimer, SIGNAL("timeout()"), self.grab)

        
        self.connect(self.table1, SIGNAL("pressed(int,int,int,const QPoint&)"),self.click)
    
    def updatesliders(self):
        """update drawing of all sliders"""
        for r in range(self.table1.numRows()):
            for c in range(self.table1.numCols()):
                if not (self.routeToSelf is False and r == c):
                    self.table1.cellWidget(r, c).setProgress(self.values[r][c])
                
    
    def setsize(self, row, col):
        """set size of table: row, col"""
        self.table1.setNumRows(row)
        self.table1.setNumCols(col)
        self.setUpdatesEnabled(False)
        for r in range(self.table1.numRows()):
            self.table1.setRowHeight(r, 18)
            self.table1.setRowStretchable(r, False)
            self.values.append(list())
            for c in range(self.table1.numCols()):
                if r == 0:
                    self.table1.setColumnWidth(c, self.columnwidth)
                if not (self.routeToSelf is False and r == c):
                    self.table1.setCellWidget(r, c, RoutingProgress(1000, 0, self.table1))
                    self.values[r].append(0)
                else: 
                    self.values[r].append(-1)
                    self.empty_cells.append((r, c))
        self.table1.viewport().adjustSize()
        self.table1.adjustSize()
        self.setUpdatesEnabled(True)
    
    def set_row_labels(self, lust):
        self.table1.setRowLabels(lust)
        #self.table1.viewport().adjustSize()
        self.table1.adjustSize()

    def set_col_labels(self, lust):
        self.table1.setColumnLabels(lust)
        self.table1.setTopMargin(18)
        #self.table1.viewport().adjustSize()
        self.table1.adjustSize()

    
    def set_column_width(self, i):
        for c in range(self.table1.numCols()):
            self.table1.setColumnWidth(c, i)
        self.table1.adjustSize()
        self.table1.viewport().adjustSize()
        self.columnwidth = i
    
    def setlabels(self, row, col):
        """set labels for headers: row(list), col(list)"""
        for i, item in enumerate(row):
            self.table1.verticalHeader().setLabel(i, QString(item))
        for i, item in enumerate(col):
            self.table1.horizontalHeader().setLabel(i, QString(item))
    
    def setvalue(self, row, col, v):
        """set value for specific slider, and update view."""
        if not (self.routeToSelf is False and row == col):
            try:
                self.values[row][col] = v
                self.table1.cellWidget(row, col).setProgress(self.values[row][col])
            except:
                print "No such item"
    
    def clear_cell(self, r, c):
        self.table1.clearCellWidget(r, c)
        self.table1.setCellWidget(r, c, QFrame())
        self.table1.cellWidget(r, c).setPaletteBackgroundColor(QColor(50, 50, 50))
        self.empty_cells.append((r, c))
    
    def grab(self):
        self.slider.grabMouse()
        
    def click(self,r,c,i,point):
        """action when clicked on certain cell"""
        if (r, c) in self.empty_cells:
            return 0
        #reset previous justin case
        if self.currentvalue != None:
            self.table1.setColumnWidth(self.sliderat[1], self.columnwidth)
            self.table1.setCellWidget(self.sliderat[0], self.sliderat[1], RoutingProgress(1000, self.currentvalue, self.table1))
             
        v = self.values[r][c]
        self.table1.setColumnWidth(c, 200)
        self.slider = RoutingSlider(v, self)
        self.currentvalue = v 
        self.table1.setCellWidget(r,c,self.slider)
        self.oldpos = QCursor.pos()
        self.table1.ensureCellVisible(r,c)
        p = QPoint(self.slider.sliderRect().x() +5, self.slider.sliderRect().y()+5)
        QCursor.setPos(self.slider.mapToGlobal(p))
        mevent = QMouseEvent(QEvent.MouseButtonPress, p, Qt.LeftButton,Qt.LeftButton) 
        self.slider.mousePressEvent(mevent)
        self.ptimer.start(0, 1) # wait for events to be processed.
        self.sliderat = r, c
        self.connect(self.slider, SIGNAL("sliderReleased()"),self.release)
        self.connect(self.slider,SIGNAL("valueChanged(int)"), self.processoutput)

    def release(self):
        """action when mouse is released"""
        QCursor.setPos(self.oldpos)
        self.table1.setColumnWidth(self.sliderat[1], self.columnwidth)
        self.table1.setCellWidget(self.sliderat[0], self.sliderat[1], RoutingProgress(1000, self.currentvalue, self.table1))
        self.currentvalue = None

    def processoutput(self, i):
        """get signal from slider and pass it on"""
        self.values[self.sliderat[0]][self.sliderat[1]] = i
        self.currentvalue = i
        self.output(self.sliderat[0], self.sliderat[1])
    
    def output(self, row, col):
        if not (self.routeToSelf is False and row == col):
            o = ((row, col), self.values[row][col])
            self.emit(PYSIGNAL("output"), (o,))
            #print o
    
    def flush(self):
        for r in range(self.table1.numRows()):
            for c in range(self.table1.numCols()):
                self.output(r, c)
                
    def newSlot(self):
        print "Form4.newSlot(): Not implemented yet"

    def __tr(self,s,c = None):
        return qApp.translate("Form4",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = Routing(4, 4, False)
    f = ["really long one", "6", "7", "8"]
    fk = ["Jag", "Ar", "Bast", ""]
    w.setlabels(f, fk)
    w.flush()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
