# Copyright 2007 Johannes Burström, <johannes@ljud.org>
# -*- coding: utf-8 -*-
__version__ = "$Revision$"


import sys
from qt import *
from qttable import *

from xmlsave import *
from jmachine import *
class ParamRoutingPopup(QPopupMenu):
    def __init__(self, *args):
        QPopupMenu.__init__(self, *args)
        
        self.params = {}
        self.menus = {}
        
        qApp.connect(qApp, PYSIGNAL("new_param_recv"), self.add_item)
        self.connect(self, SIGNAL("activated(int)"), self.on_activation)
        
    def add_item(self, p):
        add = p.full_address
        parentadd = p.parent().full_address
        if parentadd in self.params:
            if parentadd not in self.menus:
                grandpa = self
                for add, menu in self.menus.items():
                    if add == p.parent().parent().full_address:
                        grandpa = menu
                        break
                self.menus[parentadd] = QPopupMenu(grandpa)
                self.connect(self.menus[parentadd], 
                    SIGNAL("activated(int)"), self.on_activation)
                grandpa.insertItem(parentadd, self.menus[parentadd])
            self.menus[parentadd].insertItem(add)
            self.params[add] = p
            return
        self.insertItem(add)
        self.params[add] = p
        
    def on_activation(self, id):
        print self.text(id)
        
class _RoutingRow(Param):
    def __init__(self, sources, **kwargs):
        Param.__init__(self, **kwargs)
        
        self.controller = ParamController()
        
        self.type = bool
        self.check_active = ParamCheckBox(self, self.parent())
        self.check_active.setText(QString("Active"))
        self.set_state(0)
        
        self.sender_select_param = Param(address="/sender", type=str)
        self.insertChild(self.sender_select_param)
        self.sender_select = ParamComboBox(self.sender_select_param)
        self.sender_select.append(sources)
        if sources:
            first_item = list(sources)[0]
            self.sender_select_param.set_state(first_item)
            self.receiver_select_param = Param(address="/receiver", type=str)
            self.insertChild(self.receiver_select_param)
            self.receiver_select = ParamComboBox(self.receiver_select_param)
            self.receiver_select.append(sources)
            self.receiver_select_param.set_state(first_item)
            #Init a first routing, according to s/r above
            p = self.find_param_from_path(str(first_item))
            self.param_sender = p
            self.param_reciever = p
            self.controller.set_sender(p)
            self.controller.set_reciever(p)
        
        self.min_value_param = Param(address="/min_value", type=float)
        self.min_value = ParamSpinBox(self.min_value_param)
        self.insertChild(self.min_value_param)
        self.max_value_param = Param(address="/max_value", type=float)
        self.max_value = ParamSpinBox(self.max_value_param)
        self.insertChild(self.max_value_param)
        
        self.connect(self, PYSIGNAL("paramUpdate"), self.handle_check)
        self.connect(self.min_value, SIGNAL("valueChanged(int)"), self.set_values)
        self.connect(self.max_value, SIGNAL("valueChanged(int)"), self.set_values)
        self.connect(self.sender_select_param, PYSIGNAL("paramUpdate"), self.handle_select)
        self.connect(self.receiver_select_param, PYSIGNAL("paramUpdate"), self.handle_select)
        
    def handle_select(self, add):
        # first disconnect current controller
        self.controller.set_enabled(0)
        if self.sender() is self.sender_select_param:
            self.param_sender = self.find_param_from_path(self.sender_select_param.get_state())
            self.controller.set_sender(self.param_sender)
        elif self.sender() is self.receiver_select_param:
            self.param_reciever = self.find_param_from_path(self.receiver_select_param.get_state())
            self.controller.set_reciever(self.param_reciever)
        p = self.param_reciever
        if self.param_sender.type in (float, int) and self.param_reciever.type in (float, int):
            #FIXME: converting issues...
            min, max = p.min or 0, p.max or 0 #for those cases where float is not set
            self.min_value.setRange(min, max)
            self.min_value_param.set_state(min)
            self.max_value.setRange(min, max)
            self.max_value_param.set_state(max)
        f = self.param_sender.check_connection(self.param_reciever)
        # if it was enabled and connection is ok, enable it again, which also
        # connects it
        if self.get_state():
            self.set_state(f)
        #if connection is not ok, show it by graying out the checkbox  
        self.check_active.setEnabled(f)
            
    def handle_check(self, i):
        if i == self.UpdateState:
            f = self.controller.set_enabled(self.get_state())
        #Disable if not able to activate
    
    def set_values(self, v):
        if self.sender() is self.min_value:
            self.controller.min_value = v
        elif self.sender() is self.max_value:
            self.controller.max_value = v

class ParamRouting(QVBox):
    sources = set()
    def __init__(self, *args):
        QVBox.__init__(self, *args)
        
        self.parentbox = self.parent()
        
        self.saving = MiniMachine("ParamRouting",self)
        
        self.saving.setGeometry(20,20,400,400)
        self.table = QTable(self)
        self.table.setSelectionMode(QTable.NoSelection)
        self.root_param = self.saving.root_param
        
        self.hide_table()
    
    def init_controls(self, parent):
        for p in parent.queryList("Param"):
            self.__class__.sources.add(p.full_address)
            qApp.emit(PYSIGNAL("new_param_recv"), (p,))
         
        self.routers = []
        
        self.table.setNumCols(7)
        self.table.setColumnReadOnly(5, 1)
        self.table.setColumnReadOnly(6, 1)
        self.insert_router()
        
        #self.viewport().adjustSize()
        
        self.connect(self.table, SIGNAL("clicked(int,int,int,const QPoint&)"), self.handle_clicks)
        
        self.old_geometry = self.geometry()
        
        self.saving.init_controls()
    
    def toggle_show(self):
        print "FOOO"
        if not self.table.isShown():
            self.old_geometry = self.geometry()
            self.setGeometry(QRect(200, 200, 708, 500))
            self.show_table()
            self.table.adjustSize()
        else:
            self.setUpdatesEnabled(0)
            self.setGeometry(self.old_geometry)
            self.hide_table()
            self.setUpdatesEnabled(1)
    
    def hide_table(self):
        self.table.hide()
        
    def show_table(self):
        self.table.show()

    def insert_router(self):
        row = self.table.numRows()
        self.table.insertRows(row, 1)
        
        address="/rule" + str(self.table.numRows())
        rr = _RoutingRow(self.__class__.sources)
        rr.address = address
        self.root_param.insertChild(rr)
 
        self.table.setCellWidget(row, 0, rr.sender_select)
        self.table.setCellWidget(row, 1, rr.receiver_select)
        self.table.setCellWidget(row, 2, rr.min_value)
        self.table.setCellWidget(row, 3, rr.max_value)
        self.table.setCellWidget(row, 4, rr.check_active)
        self.table.setText(row, 5, QString("Delete"))
        self.table.setText(row, 6, QString("New rule"))
        self.table.horizontalHeader().setLabel(0, "Sender")
        self.table.horizontalHeader().setLabel(1, "Receiver")
        self.table.horizontalHeader().setLabel(2, "Min")
        self.table.horizontalHeader().setLabel(3, "Max")
        self.table.horizontalHeader().setLabel(4, "Enable")
        self.table.horizontalHeader().setLabel(5, "")
        self.table.horizontalHeader().setLabel(6, "")
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 55)
        self.table.setColumnWidth(5, 45)
        self.table.setColumnWidth(6, 55)
        self.routers.append(rr)
    
    def handle_clicks(self, row, col, mb, qp):
        if col is 5 and self.table.numRows() > 1:
            self.remove_router(row)
            for r in self.routers:
                r.address = "/rule" + str(self.routers.index(r) + 1)
        if col is 6:
            self.insert_router()
            
    def remove_router(self, row):
        self.root_param.removeChild(self.routers[row])
        QTable.removeRow(self.table, row)
        del self.routers[row]
    
def save():
    pre = s.check_preset("THis preset", f.param)
    while len(pre.getchildren()) != len(f.routers):
        if len(f.routers) > len(pre.getchildren()):
            f.remove_router()
        else:
            f.insert_router()

    s.load_preset(pre, f.param)

def popup():
    prp.popup(QCursor.pos())

if __name__ == "__main__":
    a = QApplication(sys.argv)
    w = QHBox()
    #w.setFixedWidth(800)
    p = Param(address="/parent")
    p1 = Param(address="/p1")
    p2 = Param(address="/p2")
    p3 = Param(address="/p3")
    p4 = Param(address="/p4")
    p5 = Param(address="/p5")
    
    p.insertChild(p1)
    p.insertChild(p2)
    p.insertChild(p3)
    p3.insertChild(p4)
    p4.insertChild(p5)
    
    slider = ParamSlider(p3, w)
    
    prp = ParamRoutingPopup(w)
    b = QPushButton("KUK", w)
    pr = ParamRouting(w)
    w.connect(b, SIGNAL("clicked()"), popup)
    
    pr.init_controls(p)
    
    w.show()
    
    a.setMainWidget(w)

    a.exec_loop()
