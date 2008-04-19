# -*- coding: utf-8 -*-

import sys
from qt import *
from qttable import QTable, QTableItem
from jmachine import Param, ParamProgress

        

class Routing(QWidget):
    """A variable-sized table with sliders, ideal for signal routing purposes.
    
    Args: rows (int), columns (int), route to self (bool), Parent (obj) (None),"""
    def __init__(self, row, col, routeToSelf = True, parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)
        if not name:
            self.setName("Form4")
        self.routeToSelf = routeToSelf
        self.empty_cells = [] 
        self.currentvalue = None #holds current slider value

        self.table1 = QTable(self,"table1")
        self.table1.setPaletteBackgroundColor(QColor(0,0,0))
        self.table1.viewport().setPaletteBackgroundColor(QColor(0,0,0))
        self.table1.setResizePolicy(QTable.AutoOne)
        self.table1.setVScrollBarMode(QTable.AlwaysOff)
        for r in range(self.table1.numRows()):
            self.table1.setRowHeight(r, 18)
            self.table1.setRowStretchable(r, False)
            pr = Param()#Holding param
            self.root_param.insertChild(pr)
            self.params.append(pr) 
            for c in range(self.table1.numCols()):
                if r == 0:
                    self.table1.setColumnWidth(c, self.columnwidth)
                if self.routeToSelf is True or r is not c:
                    p = Param(type=float)
                    pr.insertChild(p)
                    self.table1.setCellWidget(r, c, ParamProgress(p, self.table1))
                else:
                    #do nothing
                    #self.params[r].append(-1)
                    self.empty_cells.append((r, c))
        self.table1.setHScrollBarMode(QTable.AlwaysOff)
        self.table1.setShowGrid(0)
        self.table1.setReadOnly(1)
        self.table1.setSelectionMode(QTable.NoSelection)
        self.table1.setFocusPolicy(QWidget.NoFocus)
        self.root_param = Param()
        self.params = [] #holds all parent Params
        self.columnwidth = 50
        self.setsize(row, col)
        self.adjustSize()
        
    def setsize(self, row, col):
        """set size of table: row, col
        
        Creates a parent Param for every row, with child params for every col.
        No other adjustments, namings or range settings are done here, but has
        to be done in the subclass, preferrably after the init of this class."""
        self.table1.setNumRows(row)
        self.table1.setNumCols(col)
        self.setUpdatesEnabled(False)
        for r in range(self.table1.numRows()):
            self.table1.setRowHeight(r, 18)
            self.table1.setRowStretchable(r, False)
            pr = Param()#Holding param
            self.root_param.insertChild(pr)
            self.params.append(pr) 
            for c in range(self.table1.numCols()):
                if r == 0:
                    self.table1.setColumnWidth(c, self.columnwidth)
                if self.routeToSelf is True or r is not c:
                    p = Param(type=float)
                    pr.insertChild(p)
                    self.table1.setCellWidget(r, c, ParamProgress(p, self.table1))
                else:
                    #do nothing
                    #self.params[r].append(-1)
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

    def params_reparent(self, parent):
        for p in self.params:
            parent.insertChild(p)
    
    def set_column_width(self, i):
        for c in range(self.table1.numCols()):
            self.table1.setColumnWidth(c, i)
        self.table1.adjustSize()
        self.table1.viewport().adjustSize()
        self.columnwidth = i
        
    def set_row_height(self, i):
        for c in range(self.table1.numRows()):
            self.table1.setRowHeight(c, i)
        self.table1.adjustSize()
        self.table1.viewport().adjustSize()
        
    def setlabels(self, row, col):
        """set labels for headers: row(list), col(list)"""
        for i, item in enumerate(row):
            self.table1.verticalHeader().setLabel(i, QString(item))
        for i, item in enumerate(col):
            self.table1.horizontalHeader().setLabel(i, QString(item))
    
    def clear_cell(self, r, c):
        self.table1.clearCellWidget(r, c)
        self.table1.setCellWidget(r, c, QFrame())
        self.table1.cellWidget(r, c).setPaletteBackgroundColor(QColor(50, 50, 50))
        self.empty_cells.append((r, c))
        
if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    b = QVBox(None)
    w = RoutingView(4, b)
    z = MiniMachine("Flesh", b)
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
