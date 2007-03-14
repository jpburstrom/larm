# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/johannes/python/sc/machine.ui'
#
# Created: tis feb 20 21:55:08 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!

import sys
from qt import *
from string import capitalize
import copy

import osc

from saving import Saving
from canvaslabel import Canvasinfo
from larmglobals import getgl, dbp



class SnapButton(QPushButton):
    """Special instance of QPushButton w/ some gui tricks adapted for use with SnapButtonGroup"""
    def __init__(self,parent = None,name = None,fl = 0):
        QPushButton.__init__(self, parent,name)
        self.parent = parent
        self.button = 0
        self.event = 0
        self.saved = False
        #self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        #self.resize(2,2)
        
    def mousePressEvent(self, e):
        QPushButton.mousePressEvent(self, e)
        self.event = e
    def eventState(self):
        return self.event
    def setsaved(self):
        self.setPaletteBackgroundColor(QColor(220,150,150))
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
        self.setInsideMargin(3)
        #self.setFrameStyle(QFrame.NoFrame)
        for i in range (number):
            self.buttons.append(SnapButton(self, "pushButton" + str(i)))
            self.buttons[i].setText(str(i))
            self.buttons[i].setMaximumHeight(15)
            self.buttons[i].setMaximumWidth(20)
            
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
            dbp("Snapshot saved")
            self.parent().save_snapshot(click)
    
    def setsaved(self, button):
        self.buttons[button].setsaved()
        
class PopupLabel(QLabel):
    """A nice label with right-click popup menu for saving presets
    
    Needs two methods, save_preset and load_preset, in parent widget."""
    
    def __init__(self, parent=None,name=None, fl = 0):
        QLabel.__init__(self,parent,name,fl)
        self.setPaletteBackgroundColor(QColor(100,50,0))
        self.setGeometry(QRect(10,10,120,20))
        self.setPaletteForegroundColor(QColor(128,128,128))
        textLabel2_font = QFont(self.font())
        textLabel2_font.setFamily("Pigiarniq Heavy")
        textLabel2_font.setPointSize(10)
        self.setFont(textLabel2_font)
        self.setFixedHeight(20)
        self.setAlignment(Qt.AlignCenter)
        
        self.popupmenu = QPopupMenu(self, "pop")
        self.poppop = QPopupMenu()
        self.newPreset = QLineEdit(self.poppop, "presname")
        self.poppop.insertItem(self.newPreset)
        self.poppop.adjustSize()
        self.popupmenu.insertTearOffHandle()
        self.popupmenu.insertItem(QLabel("Actions",self.popupmenu))
        self.popupmenu.insertItem("Save as Preset", self.poppop)
        parent.get_presets(self)
        self.connect(self.newPreset, SIGNAL("returnPressed()"), self.add_preset)
        self.connect(self.popupmenu, SIGNAL("activated(int)"), self.select_preset)
                
    def contextMenuEvent(self, e):
        self.popupmenu.popup(QCursor.pos())
    
    def add_preset_byname(self, name):
        self.popupmenu.insertItem(name)
        
    def add_preset(self):
        t = self.newPreset.text()
        self.poppop.hide()
        self.popupmenu.hide()
        self.newPreset.clear()
        if t not in self.parent().presets:
            self.popupmenu.insertItem(t)
        self.parent().save_preset(t)
    
    def select_preset(self, i):
        self.parent().load_preset(self.popupmenu.text(i))
    
    def activate(self):
        self.setPaletteBackgroundColor(QColor(255,127,42))
    
    def deactivate(self):
        self.setPaletteBackgroundColor(QColor(100, 50, 0))
        
class MiniMachine(QVBox):
    """a Machine without MarioDots connection"""
    
    def __init__(self,label, parent = None, name = None,fl = 0):
        QVBox.__init__(self,parent,name,fl)
        
        self.parent = parent
        self.label = label
        self.slashedlabel = '/'+label.replace(' ', '_').lower()
        #different instances of same machine can share save data if they append #[n]
        #to the instances' labels. This (anything after hash) will be removed.
        self.savelabel = self.slashedlabel.split("#")[0]
        #self.slashedlabel = self.slashedlabel.replace('#', '_')
        self.state = {} #all saveable values
        self.presets = [] #list of current preset names
        self.globalsnap = []
        self.localsnap = []
        self.active = False
        self.osc_host = getgl("osc_address")
        self.osc_port = getgl("osc_port")
        
        if not name:
            self.setName(label)

        self.setMargin(3)
        self.setPaletteBackgroundColor(QColor(50,50,50))
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.tek = PopupLabel(self, label)
        self.tek.setText(capitalize(label))
        self.clearWState(Qt.WState_Polished)
        self.numberofbuttons = 4
        self.snapbuttons = SnapButtonGroup(self, self.numberofbuttons)
        self.max = 0
        
        self.onoff = False
        
        #all instances with the same parent gets a signal when a new preset is born
        self.connect(self.parent, PYSIGNAL("new_preset"), self.update_presets)
        
    def init_controls(self):
        self.load_preset("init")
    
    def update_presets(self, obj, label):
        if obj is not self and label not in self.presets \
            and self.__class__ == obj.__class__:
            self.tek.add_preset_byname(label)
        
    def save_snapshot(self, snap, local=True):
        if local: 
            lis = self.localsnap
            self.snapbuttons.setsaved(snap)
        else: 
            lis = self.globalsnap
        statecopy = self.state.copy()
        try:
            lis[snap] = statecopy
        except IndexError:
            while len(lis) < snap:
                lis.append({})
            lis.append(statecopy)

    def recall_snapshot(self, snap, local=True):
        if local: 
            lis = self.localsnap
        else: 
            lis = self.globalsnap
        try:
            for k, v in lis[snap].items():
                self.state[k] = v
                osc.sendMsg("".join([i for i in [self.slashedlabel, k]]), 
                    [v], self.osc_host, self.osc_port)
        except IndexError:
            pass
        else:
            self.update_controls()
            try:
                self.call_for_canvas_update()
            except AttributeError:
                pass
            self.emit(PYSIGNAL("snapshot_loaded"), ())
       
    def get_presets(self, dest):
        s = Saving(self.savelabel + "/presets")
        ls = s.getdirs()
        for i in ls:
            if i not in self.presets:
                dest.popupmenu.insertItem(i)
                self.presets.append(i)

    def save_preset(self, preset, local=True):
        if local:
            #this signal is for the siblings of the same class to know about a new preset
            self.parent.emit(PYSIGNAL("new_preset"), (self, preset,))
            preset = "/presets/"+preset
        else:
            preset = "/globalpresets/"+preset
        s = Saving(self.savelabel + preset)
        s.save(self.state)
        del s

    def load_preset(self, preset, local=True):
        if local:
            preset = "/presets/"+preset
        else:
            preset = "/globalpresets/"+preset
        u = Saving(self.savelabel + preset)
        keys = u.ls()
        for k, v in u.getvalues(keys).items():
            k = str(k.replace("+", "/"))
            self.state[k] = v
            osc.sendMsg("".join([i for i in [self.slashedlabel, k]]), 
                [v], self.osc_host, self.osc_port)
        self.update_controls()
        try:
            self.call_for_canvas_update()
        except AttributeError:
            pass
        self.emit(PYSIGNAL("preset_loaded"), (preset,))
    
    def store_and_send(self, k, v):
        """Convenient method to store and send (via osc) values
        Args: Key, Value"""
        dbp(k, v)
        self.state[k] = v
        osc.sendMsg("".join([i for i in [self.slashedlabel, k]]), [v], self.osc_host, self.osc_port)
    
    def send_to_osc(self, k, v):
        """Method to send (via osc) values
        Args: Key, Value"""
        osc.sendMsg("".join([i for i in [self.slashedlabel, k]]), [v], self.osc_host, self.osc_port)
    
    def update_controls(self):
        """A method to update all gui controls to match current state.
        
        This has to be redefined in every subclass. Here it doesn't do anything."""
        pass
    
    def on_off(self, arg = None):
        """Turn the bastard on and off. Toggle or set.
        
        The argument can be 0 or 1 for off and on, or None for toggle."""
        if not self.onoff or arg == 1:
            self.tek.setPaletteForegroundColor(QColor("gold"))
            self.onoff = True
            osc.sendMsg("".join([i for i in [self.slashedlabel, "/onoff"]]), [1], self.osc_host, self.osc_port)
        elif self.onoff or arg == 0:
            self.tek.setPaletteForegroundColor(QColor(128,128,128))
            self.onoff = False
            osc.sendMsg("".join([i for i in [self.slashedlabel, "/onoff"]]), [0], self.osc_host, self.osc_port)
    def activate(self):
        if not self.active:
            self.active = True
            self.tek.activate()
        
    def deactivate(self):
        self.active = False
        self.tek.deactivate()
        
    def tgl_active(self):
        if not self.active:
            self.activate()
        else:
            self.deactivate()

class Machine(MiniMachine):
    activeMachines = []
    shownumbers = 0
    mouse_pos = None

    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        MiniMachine.__init__(self,label,parent,name,fl)

        self.label = label
        self.canvas = canvas
        self.canvas.newset(self.label)
        self.canvaslabel = canvaslabel
        self.globalsnap = []
        self.localsnap = []
        #change order or labels if needed
        self.mouseButtons = ['BTN_LEFT', 'BTN_RIGHT', 'BTN_MIDDLE', 'BTN_SIDE', 'BTN_EXTRA']
        self.updateable = [] #list of mouse buttons that's been in use since last gui update
        self.mouse_parameters = {}
        self.y_only = 0
        self.x_only = 0
        
        self.shownumbers = self.__class__.shownumbers
        
        self.timer = QTimer() #this is called when activated
        QObject.connect(self.timer, SIGNAL("timeout()"), self.update_canvas)
        self.scaleto = canvas.getscale()
        
        self.set_mouse_parameters()
        self.init_mouse_parameters()
        self.generate_label_tuple()
        
        if not name:
            self.setName(label)
        
        #self.init_controls()
    
    def init_controls(self):
        self.load_preset("init")
        self.updateable = copy.copy(self.mouseButtons)
    
    def call_for_canvas_update(self):
        self.updateable = copy.copy(self.mouseButtons)
        
    def generate_label_tuple(self):
        """ Set current labels
        
        The only thing this does is to set the self.label_tuple variable.
        The method then gets called when initing the object. To be useful, this method 
        (and the corresponding variable) has to be redefined in each Machine subclass. 
        These labels are for screen use only, so spaces can be used as you wish."""
        
        self.label_tuple = (self.label, [
        ['label1xkkk', 'label1y'],
        ['label2x', 'label2y'],
        ['label3x', 'label3y'],
        ['label4x', 'label4y'],
        ['label5x', 'label5y']
        ] )
        
    def set_mouse_parameters(self):
        """ Set current mouse parameters
        
        The only thing this does is to set the self.mouse_parameters variable.
        The method then gets called when initing the object. To be useful, this method 
        (and the corresponding variable) has to be redefined in each Machine subclass. """
        
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/oscroute0", [0.0, 100.0]),
                'REL_Y' : ("/another_route0", [0.0, 100.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/oscroute1", [0.0, 100.0]),
                'REL_Y' : ("/another_route1", [0.0, 500.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("/oscroute2", [0.0, 100.0]),
                'REL_Y' : ("/another_route2", [44.0, 100.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("/oscroute3", [0.0, 100.0]),
                'REL_Y' : ("/another_route3", [0.0, 100.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("/oscroute4", [0.0, 100.0]),
                'REL_Y' : ("/another_route4", [0.0, 10.0]) },
        }
    
    def init_mouse_parameters(self):
        """Change min/max values to values used for scaling incoming mouse events
        
        A factor is appended to the current min/max lists in mouse_parameters dict, 
        used for scaling the incoming values according to current mouse_resolution
        setting (defined in larmglobals). Another value is added to help calculate values for 
        gui uses."""
        
        b = copy.copy(self.mouse_parameters)
        mr = getgl('mouse_resolution')
        for k, v in b.items():
            for j, u in v.items():
                if u[0] != "":
                    self.state[u[0]] = 0
                    u[1].append( mr / (u[1][1] - u[1][0])) #calculate factor
                    if j == 'REL_X':
                        u[1].append((u[1][1] - u[1][0]) / self.scaleto[0]) # X value for canvas
                    elif j == 'REL_Y':
                        u[1].append((u[1][1] - u[1][0] )/ - self.scaleto[1]) # and Y, inverse
        self.mouse_parameters = b
    
    def activate(self):
        if not self.active:
            self.active = True
            self.__class__.activeMachines.append(self)
            self.update_canvas()
            self.canvas.showset(self.label)
            if self.__class__.shownumbers:
                self.canvas.showtext(self.label)
            self.timer.start(40)
            self.canvaslabel.emit(PYSIGNAL("showMachineLabel"), ((self.label_tuple),))
            self.canvas.grabMouse()
            qApp.setOverrideCursor(QCursor(Qt.BlankCursor))
            if not self.__class__.mouse_pos:
                self.__class__.mouse_pos = QCursor.pos()
            self.tek.activate()
        
    def deactivate(self):
        self.active = False
        try:
            self.__class__.activeMachines.remove(self)
        except ValueError:
            pass
        else:
            self.canvas.hideset(self.label)
            if self.__class__.shownumbers:
                self.canvas.hidetext(self.label)
            self.timer.stop()
            self.canvaslabel.emit(PYSIGNAL("hideMachineLabel"), (self.label,))
            self.canvas.releaseMouse()
            qApp.restoreOverrideCursor()
            if not qApp.overrideCursor() :
                QCursor.setPos(self.__class__.mouse_pos)
                self.__class__.mouse_pos = None
            self.tek.deactivate()
    
    def do_show_numbers(self):
        self.canvas.showtext(self.label)
        for key in self.mouseButtons:
            d = self.mouse_parameters[key]
            try:
                label1 = self.state[d['REL_X'][0]]
            except KeyError:
                label1 = 0.0
            try:
                label2 = self.state[d['REL_Y'][0]]
            except KeyError:
                label2 = 0.0
            self.canvas.settext(self.label, self.mouseButtons.index(key), label1, label2)
        
    def do_hide_numbers(self):
        self.canvas.hidetext(self.label)
    
    def handle_mouse(self, ev, host, port): 
        """Routing incoming mouse events to machine parameters
        
        Called from mouse event polling thread, updating machine parameters
        and passing them on to the OSC sending function."""
        cnv = self.state
        for k, v in ev.buttons.items():
            if v == 1:
                self.updateable.append(k)
                #Turn mouse delta into usable data according to current mouse_parameters
                #The 2 code chunks are for handling x and y differently (to invert y data)
                x = self.mouse_parameters[k]['REL_X']
                y = self.mouse_parameters[k]['REL_Y']
                if not self.x_only:
                    try:
                        test = cnv[x[0]]
                    except KeyError:
                        pass
                    else:
                        cnv[x[0]] = max(x[1][0], 
                            min(x[1][1], cnv[x[0]] + (ev.axes['REL_X'] / x[1][2])))
                        if test != cnv[x[0]]: #if updated
                            osc.sendMsg("".join([i for i in [self.slashedlabel, x[0]]]), 
                                [cnv[x[0]]], host, port)
                if not self.y_only:
                    try:
                        test2 = cnv[y[0]]
                    except KeyError:
                        pass
                    else:
                        cnv[y[0]] = max(y[1][0], 
                            min(y[1][1], cnv[y[0]] - (ev.axes['REL_Y'] / y[1][2])))
                        if test2 != cnv[y[0]]: #if updated
                            osc.sendMsg("".join([i for i in [self.slashedlabel, y[0]]]), 
                                [cnv[y[0]]], host, port)
    
    def update_canvas(self):
        lust = []
        for key in self.updateable:
            d = self.mouse_parameters[key]
            try:
                label1 = self.state[d['REL_X'][0]]
                x = (self.state[d['REL_X'][0]] - d['REL_X'][1][0] ) / d['REL_X'][1][3]
            except KeyError:
                x = 3.0
                label1 = None
            try:
                label2 = self.state[d['REL_Y'][0]]
                y = ((self.state[d['REL_Y'][0]] - 
                d['REL_Y'][1][0] ) / d['REL_Y'][1][3]) + self.scaleto[1] 
            except KeyError:
                y = -20.0
                label2 = None
            self.canvas.movedot(self.label, self.mouseButtons.index(key), x, y)
            if self.__class__.shownumbers:
                self.canvas.settext(self.label, self.mouseButtons.index(key), label1, label2)
        self.updateable = []
        
    
if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = Machine(None, "label")
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
