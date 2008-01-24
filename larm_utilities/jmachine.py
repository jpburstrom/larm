# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"

#TODO: update preset menu on sibling delete

import sys
from qt import *
from qttable import *
from time import sleep
import copy

import osc

from canvaslabel import Canvasinfo
from larmglobals import getgl, dbp, alert
from xmlsave import XmlSaving

if osc.addressManager is 0:
    osc.init()

OSCDEBUG = 0

class Bang(list):
    """Just an empty list. 
    
    Doesn't override any list methods except __init__, so should be used
    with caution."""

    def __init__(self, *args):
        pass
    
class Param(QObject):
    """Abstract gui element/machine parameter class.
    
    This is the heart of the Larm parameter system. Param inherits QObject, and
    uses its parent->child hierarchy to build parameter trees which are later on
    converted into OSC addresses. 
    
    An instance is created with one or several keyword arguments to define 
    local address, label, type (int, float, bool, str, list, Bang) min/max values and/or
    state. 
    
    The param is pretty useless in itself, but works together with other params and
    specialized GUI classes to create a magnificent network of beautiful things.
    """
    
    _paths = {} # full_address->object dictionary
    
    def __init__(self, **kwargs):
        QObject.__init__(self)
        self.address = kwargs.get('address') or ""
        if self.parent():
            self.full_address = self.parent().full_address + self.address
        else:
            self.full_address = self.address
        self.full_save_address = self.full_address
        self.save_address = self.address
        self.update_paths()
        
        self.label = kwargs.get('label') or ""
        self.type = kwargs.get('type') or float ## int, str, bool, float, Bang
        self.max = kwargs.get('max') or 1.0
        self.min = kwargs.get('min') or 0.0
        

        if self.type is list:
            self.state = [[]]
        elif self.type is str:
            self.state = ['']
        elif self.type is bool:
            self.state = [False]
        else:
            self.state = [0] ##as list, to make it mutable and 
                        ##possible to change from parent.state
        self.dirty = False ##currently unused..
        
        self.UpdateState = 1
        self.UpdateMin = 2
        self.UpdateMax = 4
        
        self._enableosc = True
        self._saveable = True
        if self.type is Bang:
            self.set_saveable(False)
        
        self._connections_send = set()
        self._connections_recv = set()
        osc.bind(self.handle_incoming_osc, "/incoming" + self.full_address)
        
        self.oscSend = osc.sendMsg
        self.osc_host = getgl('osc_address')
        self.osc_port = getgl('osc_port')

    def set_address(self, address):
        """Set new local address.
        
        A Param may be created without address.This method is used
        to set the address and make sure that the network around is updated,
        as well as the OSC bindings."""
        
        if self.address == self.save_address:
            self.set_save_address(address)
        self.address = address
        self.update_paths()
        
    def insertChild(self, child):
        """ Adds child to Param instance.
        
        Param instances are organised in a tree, corresponding with the OSC 
        structure. This method allows for a safe insertion of a child, which
        updates the child's children and grandchildren and so forth to think
        of their new dad and remember his birthday and stuff. 
        
        You'll need to call this method to hook up the Param to the network."""
        
        if not isinstance(child, Param):
            raise TypeError, "Only Param children to Param parents."
        QObject.insertChild(self, child)
        ql = self.queryList("Param")
        for o in ql:
            o.full_address = o.parent().full_address + o.address
            o.set_save_address()    
            o.update_paths()
    
    def removeChild(self, child):
        """Remove Param child.
        
        Unhooks the child from the network."""
        
        QObject.removeChild(self, child)
        #FIXME: why this?
        ql = self.queryList("Param")
        for o in ql:
            o.full_address = o.parent().full_address + o.address
            o.update_paths()
    
    def printTree(self):
        """Prints the full OSC address of children, for debug purposes."""
        ql = self.queryList("Param")
        for o in ql:
            print o.full_address
            
    def printSaveTree(self):
        """Prints the saving address of children, for debug purposes."""
        ql = self.queryList("Param")
        for o in ql:
            print o.full_save_address
    
    def update_paths(self):
        """All things that needs to be done after changing local address."""
        
        osc.bind(None, "/incoming" + self.full_address)
        if self.parent():
            self.full_address = self.parent().full_address + self.address
        else:
            self.full_address = self.address
        self.__class__._paths[self.full_address] = self
        osc.bind(self.handle_incoming_osc, "/incoming" + self.full_address)
        self.set_save_address(None, False)
        ql = self.queryList("Param", None, True, False) #Non-recursive
        [o.update_paths() for o in ql if \
        o.full_address != o.parent().full_address + o.address]
                
        
    def find_param_from_path(self, path):
        """Return param object from full path, None if not existing"""
        
        return self.__class__._paths.get(path)
            
    def set_saveable(self, boo):
        """Set if param is possible to save in presets, bool"""
        self._saveable = boo
    def is_saveable(self):
        """If param is possible to save in preset"""
        return self._saveable
        
    def set_enableosc(self, boo):
        """Enable OSC send, bool"""
        self._enableosc = boo
    
    def set_state(self, v, echo=False):
        """Change current value/string of Param.
        
        Changes value, sends to OSC and emits signals to eg gui, notifying
       of the changes."""
       
        v = self.type(self.within(v))
        self.state[0] = v
        if self._enableosc:
            self._send_to_osc()
        self.emit(PYSIGNAL("paramUpdate"), (self.UpdateState,))
        if echo:
            qApp.emit(PYSIGNAL("paramEcho"), (self.address, v))
            
    def within(self, v):
        """Makes sure the state value is between boundaries, if applicable."""
        
        if self.type not in (float, int) or None in (self.max, self.min):
            return v
        else:
            return max(self.min, min(self.max, v))
    
    def set_max_value(self, v):
        """Set max value, for float and int params."""
        
        self.max = v
        self.emit(PYSIGNAL("paramUpdate"), (self.UpdateMax,))
    
    def set_min_value(self, v):
        """Set min value, for float and int params."""
        
        self.min = v
        self.emit(PYSIGNAL("paramUpdate"), (self.UpdateMin,))
        
    def get_state(self):
        """Get current state.
        
        The state is internally represented as a one-item list. 
        This makes it possible to pass the reference to the value to other methods.
        I don't know why you'd want to do that, but I probably had a reason once.
        This method extracts the value from the list and returns it."""
        
        return self.state[0]
            
    def _send_to_osc(self):
        """Private method for OSC sending"""
        
        if self.type is bool:
            state = [int(self.state[0])]
        elif self.type is list:
            state = self.state[0]
        else:
            state = self.state
        self.oscSend(self.full_address, state, self.osc_host, self.osc_port)
##        if OSCDEBUG:
##            print "OSC: " ,self.full_address,  self.state
##    
    def typecheck(self, p):
        """Compares type with another param.
        
        For one param to control another param, it has to be of the same type.
        An exception is floats and ints, which can control each other. This 
        might be changed - there's maybe reasonable for bools to control ints and
        floats as well, setting min and max values..."""
        
        fi = (float, int)
        return self.type is p.type or (self.type in fi and p.type in fi)
        
    def check_connection(self, o):
        """Looking for feedback loops in param connections
        
        Before connecting this param to another, this method checks that the
        other param isn't currently controlling this one, to avoid feedback 
        control loops. Works recursively through the connection tree."""
        
        if self is o:
            return False
        clist = self._connections_recv #sic!
        if o in clist:
            return False
        for connection in clist:
            f = connection.check_connection(o)
            if f is False:
                return False
        return True

    def add_connection(self, o):
        """Adds a connection from this Param to another one. 
        
        Returns True if connection was successful, otherwise False."""
        
        if (not self.check_connection(o)) or self is o:
            return False

        self._connections_send.add(o)
        o._connections_recv.add(self)
        return True
        
    def remove_connection(self, o):
        """Remove connection between self and another."""
        
        self._connections_send.discard(o)
        o._connections_recv.discard(self)
        return True
    
    def handle_incoming_osc(self, *msg):
        """Takes care of incoming osc messages.
        
        Updates state, sends to OSC (sic) and emits signals for GUI updates."""
        
        v = self.type(msg[0][2])
        self.state[0] = self.within(v)
        if self._enableosc:
            self._send_to_osc()
        self.emit(PYSIGNAL("paramUpdate"), (self.UpdateState,))
    
    def set_save_address(self, add=None, updatechildren = True):
        """Update or set the current preset save address.
        
        The save address is the path in the xml preset file. It's most
        often the same as the (OSC) address, but sometimes you want many
        instances of the same class to share presets. Then you can set them
        to share the save address, and everything will be wonderful.
        
        If argument 1 is None, the method updates the current save path. Otherwise
        (if str) it sets it. Arg 2: If True (default), runs recursively through all
        children. Otherwise only updates this instance."""
        
        if isinstance(add, str):
            self.save_address = add
        if self.parent():
            self.full_save_address = self.parent().full_save_address + self.save_address
        else:
            self.full_save_address = self.save_address
        if updatechildren:
            [o.set_save_address(None, True) for o in self.queryList("Param", None, True, False)]

class ParamController(QObject):
    def __init__(self, *args):
        QSlider.__init__(self, *args)
        
        self.send_param = None
        self.recv_param = None
        
        self.min_value = 0
        self.max_value = 0
        
        self.enabled = False
        self.typecheck()
        
    def set_sender(self, send):
        if not isinstance(send, Param):
            raise TypeError, "Has to be Param instance"
        self.send_param = send
        self.typecheck()
        
    def set_reciever(self, recv):
        if not isinstance(recv, Param):
            raise TypeError, "Has to be Param instance"
        self.recv_param = recv
        self.typecheck()
        
    def typecheck(self):
        fi = (float, int)
        try:
            s = self.send_param.type
            r = self.recv_param.type
        except AttributeError:
            pass
        else:
            if not (s is r or s in fi and r in fi):
                ##alert("ParamController can't convert between %s and %s."\
                ##% (str(self.send_param.type), str(self.recv_param.type)))
                self.enabled = 0
            else:
                self.enabled = 1

    def handle_update(self, p):
        if p is self.recv_param.UpdateMax:
            self.recv_param.max = self.send_param.max
        elif p is self.recv_param.UpdateMin:
            self.recv_param.min = self.send_param.min
        elif p is self.recv_param.UpdateState:
            if self.send_param.type in (bool, str):
                self.recv_param.set_state(self.send_param.get_state())
                return
            v = (((self.send_param.get_state() - float(self.send_param.min)) / \
                float(self.send_param.max)) * \
                float(self.max_value - self.min_value)) + float(self.min_value)
            self.recv_param.set_state(v)
    
    def param_connect(self):
        self.enabled = self.send_param.add_connection(self.recv_param)
        if self.enabled:
            self.connect(self.send_param, PYSIGNAL("paramUpdate"),
                self.handle_update)
        else:
            pass
            ##alert("%s->%s: Can't connect" % (self.send_param.full_address, 
            ##                    self.recv_param.full_address))
        return self.enabled
        
    def param_disconnect(self):
        if self.send_param and self.recv_param:
            self.enabled = False
            self.disconnect(self.send_param, PYSIGNAL("paramUpdate"),
                    self.handle_update)
            self.send_param.remove_connection(self.recv_param)
    
    def set_enabled(self, boo):
        if boo:
            return self.param_connect()
        else:
            self.param_disconnect()
            
class ParamSlider(QSlider):
    """ A slider made for hooking up w/ a PAram object.
    
    This needs a Param instance as the first argument. The slider only acts as an
    UI input, and after creation you should interface w/ the param object if you
    want to change values programmatically. 
    If the slider is vertical, the output is inverted (top=max)
    before passing it to Param. This makes the QSlider.setValue() output
    inverted: use Param.set_value() instead. It will update the slider as well."""
    
    def __init__(self, param, *args):
        QSlider.__init__(self, *args)
        
        if param.type not in (int, float):
            raise TypeError, "ParamSlider needs Param.type int or float"
        
        
        self.param = param
        self.popup = _ParamRoutingPopup(self.param, self)
        self.setFocusPolicy(QWidget.NoFocus)
        
        if param.min:
            QSlider.setMinValue(self, param.min)
        if param.max:
            QSlider.setMaxValue(self, param.max)
        self.setValue(self.invert(param.get_state()))
        self.setName(param.label)
        
        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
    
    def contextMenuEvent(self, e):
        self.popup.popup(QCursor.pos())
        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        
        if p is self.param.UpdateMax:
            QSlider.setMaxValue(self, self.param.max)
        elif p is self.param.UpdateMin:
            QSlider.setMinValue(self, self.param.min)
        elif p is self.param.UpdateState: 
            QSlider.setValue(self, self.invert(self.param.get_state()))
            
    def valueChange(self):
        QSlider.valueChange(self)
        if self.invert(self.value()) != self.param.get_state():
            self.param.set_state(self.invert(self.value()), 1)

    
    def rangeChange(self):
        QSlider.rangeChange(self)
        if self.minValue() != self.param.min:
            self.param.set_min_value(self.minValue())
        if self.maxValue() != self.param.max:
            self.param.set_max_value(self.maxValue())
    
    def invert(self, v):
        if self.orientation() == self.Vertical and not None in (self.param.max, self.param.min):
            return self.param.max - v + self.param.min
        return v

class ParamSpinBox(QSpinBox):
    """ A slider made for hooking up w/ a PAram object.
    
    This needs a Param instance as the first argument. The slider only acts as an
    UI input, and after creation you should interface w/ the param object if you
    want to change values programmatically."""
    def __init__(self, param, *args):
        QSpinBox.__init__(self, *args)
        self.param = param
        if param.type not in (float, int):
            raise TypeError, "ParamSpinBox needs a float or int Param.type"
        ##Sync with param, for the very first time.
        if self.param.min:
            QSpinBox.setMinValue(self, param.min)
        if self.param.max:
            QSpinBox.setMaxValue(self, param.max)
        self.setValue(param.get_state())
        self.setName(param.label)
        self.setFocusPolicy(QWidget.NoFocus)
        
        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
                        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        
        if p is self.param.UpdateMax:
            QSpinBox.setMaxValue(self, self.param.max)
        elif p is self.param.UpdateMin:
            QSpinBox.setMinValue(self, self.param.min)
        elif p is self.param.UpdateState:
            QSpinBox.setValue(self, self.param.get_state())
    
    def valueChange(self):
        QSpinBox.valueChange(self)
        ##This prevents recursion, methinks.
        if self.value() != self.param.get_state():
            self.param.set_state(self.value(), 1)
    
    def rangeChange(self):
        QSpinBox.rangeChange(self)
        if self.minValue() != self.param.min:
            self.param.set_min_value(self.minValue())
        if self.maxValue() != self.param.max:
            self.param.set_max_value(self.maxValue())

class ParamPushButton(QPushButton):
    def __init__(self, param, *args):
        QPushButton.__init__(self, *args)
        self.param = param
        ##Sync with param, for the very first time.
        self.setDown(param.get_state())
        self.setName(param.label)
        self.setText(param.label)
        if param.type not in (bool, Bang):
            raise TypeError, "ParamRadioButton needs a Param.type of class bool or Bang"
        if param.type is bool:
            self.setToggleButton(True)
        
        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
        self.setFocusPolicy(QWidget.NoFocus)
                        
        self.connect(self, SIGNAL("clicked()"), self.handle_button)
                        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        if p is self.param.UpdateState and self.param.type is not Bang:
            QPushButton.setOn(self, self.param.get_state())
    
    def handle_button(self):
        self.param.set_state(self.isOn())

class ParamThreeStateButton(QPushButton):
    def __init__(self, param, *args):
        QPushButton.__init__(self, *args)
        self.param = param
        ##Sync with param, for the very first time.
        self.color = self.paletteBackgroundColor()
        self.state = 0
        self.set_state(param.get_state())
        self.setName(param.label)
        self.setText(param.label)
        if param.type is not int :
            raise TypeError, "ParamThreeStateButton needs an int Param.type"

        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
        self.setFocusPolicy(QWidget.NoFocus)
                        
    def mousePressEvent(self, ev):
        if ev.button() == 1 and self.state is not 1:
            s = 1
        elif ev.button() == 2 and self.state is not 2:
            s = 2
        elif ev.button() in (1,2):
            s = 0
        self.set_state(s)
        self.param.set_state(s)
    
    def set_state(self, state):
        self.state = state
        if state is 0:
            self.setPaletteBackgroundColor(self.color)
        elif state is 1:
            self.setPaletteBackgroundColor(QColor("green"))
        elif state is 2:
            self.setPaletteBackgroundColor(QColor("red"))
    
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        if p is self.param.UpdateState and self.param.type is not Bang:
            self.set_state(self.param.get_state())
 
class ParamRadioButton(QRadioButton):
    def __init__(self, param, *args):
        QRadioButton.__init__(self, *args)
        self.param = param
        ##Sync with param, for the very first time.
        self.setDown(param.get_state())
        self.setName(param.label)
        self.setText(param.label)
        if param.type is not bool:
            raise TypeError, "ParamRadioButton needs a boolean Param.type"
        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
        self.connect(self, SIGNAL("clicked()"), self.handle_button)
        self.setFocusPolicy(QWidget.NoFocus)
                        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        if p is self.param.UpdateState:
            QRadioButton.setOn(self, self.param.get_state())
    
    def handle_button(self):
        self.param.set_state(self.isOn())
        
class ParamCheckBox(QCheckBox):
    def __init__(self, param, *args):
        QCheckBox.__init__(self, *args)
        self.param = param
        ##Sync with param, for the very first time.
        self.setDown(param.get_state())
        self.setName(param.label)
        self.setText(param.label)
        if param.type is not bool:
            raise TypeError, "ParamRadioButton needs a boolean Param.type"
        self.connect(self.param, PYSIGNAL("paramUpdate"),
                        self.handle_update)
        self.connect(self, SIGNAL("clicked()"), self.handle_button)
        self.setFocusPolicy(QWidget.NoFocus)
        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        if p is self.param.UpdateState:
            QCheckBox.setOn(self, self.param.get_state())
    
    def handle_button(self):
        self.param.set_state(self.isOn())

class ParamProgress(QProgressBar):
    def __init__(self, param, *args):
        QFrame.__init__(self, *args)
        self.param = param
        
        
        if param.type not in (float, int):
            raise TypeError, "ParamProgress needs a float or int Param.type"
        ##Sync with param, for the very first time.
        if not None in (self.param.max, self.param.min):
            self.setProgress(self.param.get_state() / 
                (self.param.max - self.param.min) * 100)
        self.setName(param.label)
        
        self.connect(self.param, PYSIGNAL("paramUpdate"), self.handle_update)
        self.setFocusPolicy(QWidget.NoFocus)
        
        self.setPaletteForegroundColor(QColor("gray"))
        
        self.setPercentageVisible(True)
        
        self.dblclick_value = self.param.min
        
    def mouseDoubleClickEvent(self, e):
        s = self.param.get_state()
        if s == self.param.min:
            self.param.set_state(self.dblclick_value)
        else:
            self.dblclick_value = s 
            self.param.set_state(self.param.min)
            
        
    def mousePressEvent(self, e):
        self.origo = self.mapToGlobal(e.pos())
        self.offset = e.pos().y()
        self.setCursor(QCursor(Qt.BlankCursor))
        #print self.origo.y()
    def mouseMoveEvent(self, e):
        f = self.param.max - self.param.min
        s = (self.param.get_state() + \
            ((self.offset - e.y()) * f / 1000.0 ))
        if self.param.within(s) != self.param.get_state():
            self.param.set_state(s, 1)
            try:
                self.setProgress((self.param.get_state() - self.param.min)/ 
                (self.param.max - self.param.min) * 100.0)
            except ZeroDivisionError:
                pass
            self.offset = self.mapFromGlobal(self.origo).y()
        elif self.param.get_state() not in (self.param.max, self.param.min):
            self.offset = (self.offset * 2) - e.y()
        QCursor.setPos(self.origo)
    def mouseReleaseEvent(self, e):
        self.setCursor(QCursor(Qt.ArrowCursor))
        
    def handle_update(self, p):
        """Recieves signal from the Param, updates Gui.
        """
        try:
            self.setProgress((self.param.get_state() - self.param.min)/ 
            (self.param.max - self.param.min) * 100.0)
        except ZeroDivisionError:
            pass
        
class ParamComboBox(QComboBox):
    """A subclass of QComboBox
    
    NB: we only support a few insert methods: append, prepend, clear. This
    is due to a lazy programmer. Use other methods at your own risk."""
    def __init__(self, param, *args):
        QComboBox.__init__(self, *args)
        self.param = param
        
        self._qslist = []
        
        if param.type is not str:
            raise TypeError, "QComboBox needs a str Param.type"
        self.setName(param.label)
        self.connect(self.param, PYSIGNAL("paramUpdate"), self.handle_update)
        self.connect(self, 
            SIGNAL("activated(const QString&)"), self.handle_select)
            
    def append(self, strl):
        if isinstance(strl, str):
            self._qslist.append(strl)
            self.insertItem(QString(strl), -1)
        elif isinstance(strl, list) or isinstance(strl, set):
            self.insertStringList(QStringList.fromStrList(list(strl)), -1)
            self._qslist.extend(strl)
        else:
            raise TypeError, "We need a str or list for this operation"
    
    def prepend(self, strl):
        if isinstance(strl, str):
            self._qslist.prepend(strl)
            self.insertItem(QString(strl), 0)
        elif isinstance(strl, list):
            self.insertStringList(QStringList.fromStrList(strl), 0)
            strl.extend(self._qslist)
            self._qslist = strl
        else:
            raise TypeError, "We need a str or list for this operation"
    
    def clear(self):
        self._qslist = []
        QComboBox.clear(self)
    
    def handle_update(self, p):
        if p == self.param.UpdateState:
            try:
                i = self._qslist.index(self.param.get_state())
            except ValueError:
                pass
            else:
                self.setCurrentItem(i)

    def handle_select(self, text):
        self.param.set_state(str(text))

class ParamLabel(QLabel):
    def __init__(self, param, *args):
        QLabel.__init__(self, *args)
        self.param = param
        
        self.setName(param.label)
        
        if self.param.get_state() and self.param.type is list:
            self.setText(self.param.get_state()[0])
        elif self.param.get_state():
            self.setText(self.param.get_state())

        self.connect(self.param, PYSIGNAL("paramUpdate"), self.handle_update)
    
    def handle_update(self, p):
        if p != self.param.UpdateState:
            return
        try:
            if self.param.type is list:
                s = self.param.get_state()[0]
            else:
                s = self.param.get_state()
            self.setText(str(s))
        except ValueError:
            pass
                
    def handle_select(self, text):
        self.param.set_state(str(text))

class PresetComboBox(QHBox):
    def __init__(self, root_param, parent, *args):
        QHBox.__init__(self, parent, *args)
        
        self.dirty = 0
        
        self._s = self.parent().saving
        
        self.root_param = root_param
        self.presets = []
        self.load_preset_list()
        self.current_preset = None        

        self.cb = QComboBox(self)
        self.cb.setEditable(0)
        self.cb.setDuplicatesEnabled(0)
        self.cb.insertStringList(QStringList.fromStrList(self.presets))
        self.cb.setFocusPolicy(self.NoFocus)
        
        self.hide()
        
        self.bb = QHBox(self)
        self.sb = QPushButton(self.bb)
        self.sb.setText("S")
        self.sab = QPushButton(self.bb)
        self.sab.setText("S...")
        self.b = QPushButton(self.bb)
        self.b.setText("X")
        
        for p in self.root_param.queryList("Param"):
            self.connect(p, PYSIGNAL("paramUpdate"), self.set_dirty)
        self.connect(self.parent(), PYSIGNAL("setDirty"), self.set_dirty)
        
        self.connect(self.b, SIGNAL("clicked()"), self.delete_preset)
        self.connect(self.sb, SIGNAL("clicked()"), self.save_preset)
        self.connect(self.sab, SIGNAL("clicked()"), self.save_preset_as)
        #self.connect(self.cb, SIGNAL("textChanged(const QString&)"), self.set_dirty)
        self.connect(self.cb, SIGNAL("activated(int)"), self.select_preset)
    
    def reload_preset_list(self):
        self.load_preset_list()
        self.cb.clear()
        self.cb.insertStringList(QStringList.fromStrList(self.presets))
    
    def save_preset_as(self):
        self.cb.setEditable(1)
        self.cb.setFocus()
        self.cb.lineEdit().clear()
        self.show()
        
    def my_hide(self):
        self.cb.setEditable(False)
        self.cb.setFocusPolicy(self.NoFocus)
        QTimer.singleShot(200, self.really_hide)
    
    def really_hide(self):
        self.hide()
    
    def delete_preset(self):
        if self.cb.currentItem():
            item = self.current_preset
            self.cb.removeItem(self.cb.currentItem())
            self._s.delete_preset(item, self.root_param)
            qApp.emit(PYSIGNAL('deleted_preset'), (self.parent(), self.root_param.full_save_address, item))
            self.current_preset = None
            self.my_hide()
    
    def insert_item(self, txt):
        self.presets.append(txt)
        self.cb.insertItem(txt)
    
    def select_preset(self, i):
        item = str(self.cb.text(i))
        self.current_preset = item
        if item not in self.presets:
            self.presets.append(item)
            self.current_preset = item
            self.save_preset()
            self.cb.setEditable(0)
            self.parent().append_preset_to_label()
            qApp.emit(PYSIGNAL('new_preset'), (self.parent(), self.root_param.full_save_address, item))
        else:
            self.load_preset()
        self.my_hide()

    def save_preset(self):
        if self.current_preset:
            self._s.save_preset(self.current_preset, self.root_param)
        #connect all children again
        [self.connect(p, PYSIGNAL("paramUpdate"), self.set_dirty) \
            for p in self.root_param.queryList("Param") if p.is_saveable()]
        self.sb.setEnabled(0)
        self.dirty = 0
        self.my_hide()
        
    def load_preset(self):
        self.parent().load_preset(self.current_preset, self.after_loading)

    def after_loading(self):
        for p in self.root_param.queryList("Param"):
            self.connect(p, PYSIGNAL("paramUpdate"), self.set_dirty)
        self.dirty = 0
        self.sb.setEnabled(0)
        self.emit(PYSIGNAL("preset_loaded"), ())
    
    def set_dirty(self, v):
        if  (v == self.root_param.UpdateState or\
                isinstance(v, QString)):
            self.dirty = 1
            self.sb.setEnabled(1)
            self.parent().append_preset_to_label()
            for p in self.root_param.queryList("Param"):
                self.disconnect(p, PYSIGNAL("paramUpdate"), self.set_dirty)
    
    def load_preset_list(self):
        pl = self._s.list_presets(self.root_param)
        if pl:
            self.presets = pl
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.my_hide()
        else:
            e.ignore()
            
        
class SnapButton(QPushButton):
    """Special instance of QPushButton w/ some gui tricks adapted for use with SnapButtonGroup"""
    def __init__(self,parent = None,name = None,fl = 0):
        QPushButton.__init__(self, parent,name)
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
            self.parent().parent().recall_snapshot(click)
        elif p == 3: #if rightclick-leftclick
            dbp("Snapshot saved")
            self.parent().parent().save_snapshot(click)
    
    def setsaved(self, button):
        self.buttons[button].setsaved()
        
class PopupLabel(QLabel):
    """A nice label with interactive surprises
    
    Used in combination with MiniMachine to display the machine name, activate the
    machine on left click, show the preset thing on rightclick and show a menu of
    available param routings on middle click (not used now).
    """
    
    def __init__(self, parent=None,name=None, fl = 0):
        QLabel.__init__(self,parent,name,fl)
        
        self.setPaletteBackgroundColor(QColor(100,50,0))
        font = QFont()
        font.setWeight(font.Bold)
        self.setFont(font)
        self.setGeometry(QRect(10,10,120,20))
        self.setPaletteForegroundColor(QColor(Qt.white))
        self.setFixedHeight(20)
        self.setAlignment(Qt.AlignRight)
        
        self.lmb = 0
        self.rmb = 0
        self.gesture_done = 1
        
    def mousePressEvent(self, e):
        """Activate (show canvas) on label middle-click"""
        if e.button() == 1 and not self.rmb:
            self.parent().tgl_active()
        elif e.button() == 1 and self.rmb:
            self.gesture_done = 0
            self.parent().on_off()
        elif e.button() == 2:
            self.rmb = 1
        elif e.button() == 4:
            pass
    def mouseReleaseEvent(self, e):
        if e.button() == 1:
            self.lmb = 0
        if e.button() == 2 and not self.lmb:
            self.rmb = 0
            if not self.gesture_done:
                self.gesture_done = 1
                return
            if not self.parent().preset_menu.isShown():
                self.parent().preset_menu.show()
            else:
                self.parent().preset_menu.hide()
                
##            try:
##                self.parent().routing_menu.popup(QCursor.pos())
##            except AttributeError:
##                self.parent().create_routing_menu()
##                self.parent().routing_menu.popup(QCursor.pos())
            
            
    def mouseDoubleClickEvent(self, e):
        if self.rmb:
            QLabel.mouseDoubleClickEvent(self, e)
        elif e.button() == 1:
            qApp.mainwindow.deactivate_all()
            self.parent().activate()
            #here we go
            try:
                cnv = self.parent().canvas
            except AttributeError:
                return
            else:
                QCursor.setPos(cnv.parent().mapToGlobal(
                    QPoint(cnv.x() + (cnv.width() / 2), cnv.y() + 
                    cnv.height() / 2)))
    
    def activate(self):
        self.setPaletteBackgroundColor(QColor(255,127,42))
    
    def deactivate(self):
        self.setPaletteBackgroundColor(QColor(100, 50, 0))
    
class MiniMachine(QVBox):
    """a Machine without Canvas connection
    
    Whenever you subclass this, you have to run init_controls after the param
    paths are set, to load the current presets."""
    
    def __init__(self,label, parent = None, name = None, fl = 0):
        QVBox.__init__(self,parent,name, fl)
        
        self.label = label
        self.address = '/'+label.replace(' ', '_').lower()
        
        try:
            qApp.splash.message("Loading %s" % self.label.title())
        except AttributeError:
            pass
        
        #parent of everything.
        self.root_param = Param(address=self.address)
        
        self.saving = XmlSaving()
        
        #different instances of same machine can share save data if they append #[n]
        #to the instances' labels. This (anything after hash) will be removed.
        #TODO: this is not used, and needs to be fixed eventually.
        #self.savelabel = self.address.split("#")[0]
        #self.slashedlabel = self.slashedlabel.replace('#', '_')
        self.state = {} # dict of param.address param.state pairs
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
        self.tek.setText(label.title())
        self.clearWState(Qt.WState_Polished)
        
        self.preset_menu = PresetComboBox(self.root_param, self)
        self.buttonrow = QHBox(self)
        self.buttonrow.setSpacing(2)
        self.snapbuttons = SnapButtonGroup(self.buttonrow, 4)
        self.seqparam = Param(address="/seq")
        self.root_param.insertChild(self.seqparam)
        self.seqparam.set_saveable(0)
        self.seqparam.set_enableosc(0)
        self.seqparams = []
        for i in range(4):
            self.seqparams.append(Param(address="/n%d" % i, type=int, min=0, max=2))
            self.seqparam.insertChild(self.seqparams[i])
            button = ParamThreeStateButton(self.seqparams[i], self.buttonrow)
            button.setMaximumHeight(15)
            button.setMaximumWidth(20)
            button.setText("s%d" % i)
            QToolTip.add(button, "Seq slot %d" % i)
        self.max = 0
        
        self.onoff = Param(address="/onoff", type=bool)
        self.onoff.set_saveable(0)
        self.root_param.insertChild(self.onoff)
        
        #all instances with the same parent gets a signal when a new preset is born
        self.connect(qApp, PYSIGNAL("new_preset"), self.add_preset)

        self.connect(self.preset_menu, PYSIGNAL("preset_loaded"), self.update_controls)
        self.connect(self.preset_menu, PYSIGNAL("preset_loaded"), self.append_preset_to_label)
    
    def create_routing_menu(self):
        self.routing_menu = _ParamRoutingPopup2(self.root_param, self)
        self.routing_menu.create_menu()
    
    def add_small_toggles(self, *args):
        font = QFont()
        font.setBold(1)
        for btn in args:
            param = Param(type=bool, address=btn)
            self.root_param.insertChild(param)
            button = ParamPushButton(param, self.buttonrow)
            button.setMaximumHeight(20)
            button.setMaximumWidth(20)
            button.setText(btn[1:3])
            button.setFont(font)
            QToolTip.add(button, btn)
            self.connect(button, SIGNAL("toggled(bool)"), self.small_tgl_change_color)
    
    def small_tgl_change_color(self, boo):
        color = ("black", "red")
        self.sender().setPaletteForegroundColor(QColor(color[int(boo)]))
    
    def init_controls(self):
        self.preset_menu.reload_preset_list()
        self.saving.load_preset("init", self.root_param)
        self.preset_menu.current_preset = "init"
        self.append_preset_to_label()
    
    def load_preset(self, current_preset, callback):
        self.saving.load_preset(current_preset, self.root_param)
        callback()
    
    def add_preset(self, o, add, label):
        if add == self.root_param.full_save_address and o is not self:
            self.preset_menu.insert_item(label)
    
    def save_snapshot(self, snap):
        """ Save snapshot
        Copies current state to a list of states"""
        statecopy = {}
        lis = self.localsnap
        self.snapbuttons.setsaved(snap)
        plist = self.root_param.queryList("Param")
        [statecopy.__setitem__(p.full_address, p.get_state()) for p in plist if p.is_saveable()]
        try:
            lis[snap] = statecopy
        except IndexError:
            while len(lis) < snap:
                lis.append({})
            lis.append(statecopy)

    def recall_snapshot(self, snap, local=True):
        lis = self.localsnap
        try:
            [p.set_state(lis[snap][p.full_address]) for p in \
                self.root_param.queryList("Param") if lis[snap].get(p.full_address) is not None]
        except IndexError, KeyError:
            pass
        self.emit(PYSIGNAL("snapshot_loaded"), ())

    def update_controls(self):
        pass
   
    
    def append_preset_to_label(self):
        if not self.preset_menu.current_preset:
            return
        dirty = ""
        if self.preset_menu.dirty == 1:
            dirty = " *"
        self.tek.setText("".join([self.label.title()," [%s]" % self.preset_menu.current_preset, dirty]))
    
    def on_off(self, arg = None):
        """Turn the bastard on and off. Toggle or set.
        The argument can be 0 or 1 for off and on, or None for toggle."""
        if not self.onoff.get_state() and arg != 0:
            self.tek.setPaletteForegroundColor(QColor("Green"))
            self.onoff.set_state(1)
        elif self.onoff.get_state() and arg != 1:
            self.tek.setPaletteForegroundColor(QColor("beige"))
            self.onoff.set_state(0)
            
    def activate(self):
        if not self.active:
            self.active = True
            self.tek.activate()
        
    def deactivate(self):
        self.active = False
        self.tek.deactivate()
        
    def tgl_active(self, arg=None):
        if (not self.active) and arg != 0 :
            self.activate()
        else:
            self.deactivate()
    
    def set_x_only(self, boo):
        self.x_only = boo
        
    def set_y_only(self, boo):
        self.y_only = boo    

class Machine(MiniMachine):
    activeMachines = set()
    shownumbers = 0
    mouse_pos = None

    def __init__(self,label,canvas, parent = None, name = None):
        MiniMachine.__init__(self,label,parent,name)

        self.canvas = canvas
        ## make a new canvas set of dots - this could also be done w/ signals...
        self.canvas.newset(self)
        #change order or labels if needed
        self.mouseButtons = ['BTN_LEFT', 'BTN_RIGHT', 'BTN_MIDDLE', 'BTN_SIDE', 'BTN_EXTRA']
        self.updateable = [] #list of mouse buttons that's been in use since last gui update
        self.mouse_parameters = {}
        #This is a address->param dictionary used for canvas updates...
        self._canvasparams = {} 
        
        ## if only to move x or y axis... invoked by hotkey
        self.y_only = 0
        self.x_only = 0
        
        self.shownumbers = self.__class__.shownumbers
        
        self.timer = QTimer() #this is called when activated
        QObject.connect(self.timer, SIGNAL("timeout()"), self.update_canvas)
        self.scaleto = canvas.getscale()
        
        self.set_mouse_parameters()
        self.init_mouse_parameters()
        self.generate_label_tuple()
        self.canvas.setlabels(self)

        
        if not name:
            self.setName(label)
        
        self.connect(self, PYSIGNAL("rawMouseEvents"), self.rawMouseEvents)
        #self.init_controls()
    
    def init_controls(self):
        MiniMachine.init_controls(self)
        self.updateable = copy.copy(self.mouseButtons)
        
    def update_controls(self):
        self.call_for_canvas_update()
    
    def call_for_canvas_update(self):
        self.updateable = copy.copy(self.mouseButtons)
        
    def generate_label_tuple(self):
        """ Set current labels
        
        The only thing this does is to set the self.label_tuple variable.
        The method then gets called when initing the object. To be useful, this method 
        (and the corresponding variable) has to be redefined in each Machine subclass. 
        These labels are for screen use only, so spaces can be used as you wish."""
        
        self.label_tuple = (self.label, (
        ('label1xkkk', 'label1y'),
        ('label2x', 'label2y'),
        ('label3x', 'label3y'),
        ('label4x', 'label4y'),
        ('label5x', 'label5y')
        ) )
        
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
        for k, v in b.items(): ##extract each button
            for j, u in v.items(): ## and the two axes: address, [max, min]
                if u[0] != "":
                    #here we create a new Param
                    p = Param(address=u[0], min=u[1][0], max=u[1][1], type=float)
                    self.root_param.insertChild(p)
                    self.state[u[0]] = p.state
                    self._canvasparams[u[0]] = p
                    u[1].append( mr / (u[1][1] - u[1][0])) #calculate factor
                    if j == 'REL_X':
                        u[1].append((u[1][1] - u[1][0]) / self.scaleto[0]) # X value for canvas
                    elif j == 'REL_Y':
                        u[1].append((u[1][1] - u[1][0] )/ - self.scaleto[1]) # and Y, inverse
        self.mouse_parameters = b
    
    def activate(self):
        if not self.active:
            self.active = True
            self.__class__.activeMachines.add(self)
            self.update_canvas()
            self.canvas.showset(self.label)
            self.timer.start(40)
            #elf.canvaslabel.emit(PYSIGNAL("showMachineLabel"), ((self.label_tuple),))
            qApp.emit(PYSIGNAL("addRemoveMachine"), (self, 1))
            self.tek.activate()
        
    def deactivate(self):
        self.active = False
        self.__class__.activeMachines.discard(self)
        self.canvas.hideset(self.label)
        self.timer.stop()
        self.tek.deactivate()
        qApp.emit(PYSIGNAL("addRemoveMachine"), (self, 0))
    
    def do_show_numbers(self):
        """Show Canvas dot values"""
        for key in self.mouseButtons:
            d = self.mouse_parameters[key]
            try:
                label1 = self.state[d['REL_X'][0]][0]
            except KeyError:
                label1 = 0.0
            try:
                label2 = self.state[d['REL_Y'][0]][0]
            except KeyError:
                label2 = 0.0
            self.canvas.settext(self.label, self.mouseButtons.index(key), label1, label2)
        
    def do_hide_numbers(self):
        self.canvas.setlabels(self)
    
    def rawMouseEvents(self, ev): 
        """Routing incoming mouse events to machine parameters
        
        Called from mouse event polling thread, updating machine parameters
        and passing them on to the OSC sending function. This doesn't deal with
        Param.set_value, but does all osc sending and graphic stuff by itself."""
##        if ev.type() != ev.Type(9999):
##            return 0
        cnv = self.state
        params = self._canvasparams
        for k, v in ev.buttons.items():
            if v == 1:
                self.updateable.append(k)
                #Turn mouse delta into usable data according to current mouse_parameters
                #The 2 code chunks are for handling x and y differently (to invert y data)
                x = self.mouse_parameters[k]['REL_X']
                y = self.mouse_parameters[k]['REL_Y']
                if not self.y_only:
                    try:
                        test = cnv[x[0]][0]
                    except KeyError:
                        pass
                    else:
                        cnv[x[0]][0] = max(x[1][0], 
                            min(x[1][1], cnv[x[0]][0] + (ev.axes['REL_X'] / x[1][2])))
                        if test != cnv[x[0]][0]: #if updated
                            params[x[0]].set_state(cnv[x[0]][0])
                if not self.x_only:
                    try:
                        test2 = cnv[y[0]][0]
                    except KeyError:
                        pass
                    else:
                        cnv[y[0]][0] = max(y[1][0], 
                            min(y[1][1], cnv[y[0]][0] - (ev.axes['REL_Y'] / y[1][2])))
                        if test2 != cnv[y[0]][0]: #if updated
                            cnv[y[0]][0]
                            params[y[0]]
                            params[y[0]].set_state(cnv[y[0]][0])
                
    def update_canvas(self):
        """Graphic update, done by ticking clock"""
        
        lust = []
        for key in self.updateable:
            d = self.mouse_parameters[key]
            try:
                label1 = self.state[d['REL_X'][0]][0]
                x = (label1 - d['REL_X'][1][0] ) / d['REL_X'][1][3]
            except KeyError:
                x = 3.0
                label1 = None
            try:
                label2 = self.state[d['REL_Y'][0]][0]
                y = ((label2 - d['REL_Y'][1][0] ) / d['REL_Y'][1][3]) + self.scaleto[1] 
            except KeyError:
                y = -20.0
                label2 = None
            self.canvas.movedot(self.label, self.mouseButtons.index(key), x, y)
            if self.__class__.shownumbers:
                self.canvas.settext(self.label, self.mouseButtons.index(key), label1, label2)
        self.updateable = []
    
    def load_preset(self, current_preset, callback):
        """redefine this to make something before loading presets"""
        MiniMachine.load_preset(self, current_preset, callback)
        self.call_for_canvas_update()

    def recall_snapshot(self, snap, local=True):
        MiniMachine.recall_snapshot(self, snap, local)
        self.call_for_canvas_update()


##############################
##PARAM ROUTING
##############################

class _ParamRoutingPopup(QPopupMenu):
    def __init__(self, param, *args):
        QPopupMenu.__init__(self, *args)
        self.insertItem(QLabel("Get input from:", self))
        self._param = param
        self.params = {}
        self.menus = {}
        self.setCheckable(1)
        
        qApp.connect(qApp, PYSIGNAL("new_param_recv"), self.add_item)
        self.connect(qApp, PYSIGNAL("updateParamRouting"), self.handle_update_signal)
        
        [self.add_item(self._param.find_param_from_path(p)) for p in sorted(ParamRouting.sources)]
        
        
    def add_item(self, p):
        if p is self._param or p in self.params: ##and p.typecheck(self._param):
            return
        add = p.full_address
        parentadd = p.parent().full_address
        ##if parent param already is added
        if parentadd in self.params:
            ##and if isn't added as a submenu
            if parentadd not in self.menus:
                grandpa = self.menus.get(p.parent().parent().full_address) or self
                self.menus[parentadd] = QPopupMenu(grandpa)
                self.menus[parentadd].setCheckable(1)
                grandpa.insertItem(parentadd, self.menus[parentadd])
            i = self.menus[parentadd].insertItem(add, self.on_activation)
            self.params[add] = (i, p)
            return
        i = self.insertItem(add, self.on_activation)
        self.params[add] = (i, p)
        
    def on_activation(self, id):
        self.setItemChecked(id, not self.isItemChecked(id))
        sender = self._param
        if sender:
            qApp.emit(PYSIGNAL("updateParamRouting"), \
                (sender, self._param, \
                    self.isItemChecked(id)))
    
    def handle_update_signal(self, send, recv, active):
        if self.sender() is self:
            return
        if recv is self:
            self.setItemChecked(self.params[send.address], active)
    def set_sender(self, sender):
        self._sender = sender

class _ParamRoutingPopup2(QPopupMenu):
    def __init__(self, param, *args):
        #FIXME: A fast and proper version of this menu would be nice.
        QPopupMenu.__init__(self, *args)
        
        self.root_param = param
        #self.submenu = _ParamRoutingPopup(param, self)
        
        self._param = param
        self.params = {}
        self.menus = {}
        self.setCheckable(1)
                    
    def create_menu(self):
        self.clear()
        self.insertItem(QLabel("Receiver:", self))
        for p in self.root_param.queryList("Param"):
            menu = _ParamRoutingPopup(p, self)
            self.insertItem(p.full_address, menu) 
            menu.set_sender(p)

class _RoutingRow(Param):
    def __init__(self, sources, **kwargs):
        Param.__init__(self, **kwargs)
        
        self.controller = ParamController()
        
        self.type = bool
        self.check_active = ParamCheckBox(self, self.parent())
        self.check_active.setText(QString("Active"))
        ##self.set_state(0)
        self.set_enableosc(0)
        
        self.sender_select_param = Param(address="/sender", type=str)
        self.sender_select_param.set_enableosc(0)
        self.insertChild(self.sender_select_param)
        self.sender_select = ParamComboBox(self.sender_select_param)
        self.sender_select.append(sources)
        if sources:
            first_item = list(sources)[0]
            self.sender_select_param.set_state(first_item)
            self.receiver_select_param = Param(address="/receiver", type=str)
            self.receiver_select_param.set_enableosc(0)
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
        self.min_value = ParamProgress(self.min_value_param)
        self.insertChild(self.min_value_param)
        self.max_value_param = Param(address="/max_value", type=float)
        self.max_value = ParamProgress(self.max_value_param)
        self.insertChild(self.max_value_param)
        
        [child.set_enableosc(0) for child in self.queryList("Param")]
            
        
        self.connect(self, PYSIGNAL("paramUpdate"), self.handle_check)
        self.connect(self.min_value_param, PYSIGNAL("paramUpdate"), self.set_values)
        self.connect(self.max_value_param, PYSIGNAL("paramUpdate"), self.set_values)
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
            min, max = p.min, p.max 
            self.min_value_param.set_max_value(max)
            self.min_value_param.set_min_value(min)
            self.min_value_param.set_state(min)
            self.max_value_param.set_max_value(max)
            self.max_value_param.set_min_value(min)
            self.max_value_param.set_state(max)
        f = self.param_sender.check_connection(self.param_reciever)
        # if it was enabled and connection is ok, enable it again, which also
        # connects it
        if self.get_state():
            self.controller.set_enabled(f)
        #if connection is not ok, show it by graying out the checkbox  
        self.check_active.setEnabled(f)
            
    def handle_check(self, i):
        if i == self.UpdateState:
            f = self.controller.set_enabled(self.get_state())
    
    def set_values(self, msg):
        if msg is not self.UpdateState:
            return
        if self.sender() is self.min_value_param:
            self.controller.min_value = self.min_value_param.get_state()
        elif self.sender() is self.max_value_param:
            self.controller.max_value = self.max_value_param.get_state()
    
    def disconnect(self):
        self.controller.set_enabled(0)
        #del self

class ParamRouting(QVBox):
    sources = set()
    def __init__(self, *args):
        QVBox.__init__(self, *args)
        
        
        self.parentbox = self.parent()
        
        self.saving = MiniMachine("ParamRouting",self)
        self.saving.load_preset = self.load_preset
        
        self.saving.setGeometry(20,20,400,400)
        self.table = QTable(self)
        self.table.setPaletteBackgroundColor(QColor("white"))
        self.table.setSelectionMode(QTable.NoSelection)
        self.root_param = self.saving.root_param
        
        self.hide_table()
        
        self.connect(qApp, PYSIGNAL("updateParamRouting"), self.handle_update_signal)
    
    def init_controls(self, parent):
        for p in parent.queryList("Param"):
            self.__class__.sources.add(p.full_address)
            #qApp.emit(PYSIGNAL("new_param_recv"), (p,))
         
        self.routers = []
        
        self.table.setNumCols(7)
        self.table.setColumnReadOnly(5, 1)
        self.table.setColumnReadOnly(6, 1)
        self.insert_router()
        
        #self.viewport().adjustSize()
        
        self.connect(self.table, SIGNAL("clicked(int,int,int,const QPoint&)"), self.handle_clicks)
        
        self.saving.init_controls()
    
    def handle_update_signal(self, send, recv, active):
        if self.sender() is self:
            return
        for r in self.routers:
            if r.param_sender is send and r.param_reciever is recv:
                r.set_state(active)
                return
        r = self.insert_router()
        r.sender_select_param.set_state(send.full_address)
        r.receiver_select_param.set_state(recv.full_address)
        r.set_state(active)
        
                
    
    def load_preset(self, preset, callback):
        pre = self.saving.saving.check_preset(preset, self.saving.root_param)
        while len(pre.getchildren()) != len(self.routers):
            if len(self.routers) > len(pre.getchildren()):
                self.remove_router(len(self.routers) - 1)
            else:
                self.insert_router()
        self.saving.saving.load_preset(preset, self.root_param)
        callback()
    
    def toggle_show(self):
        if not self.table.isShown():
            self.old_geometry = self.geometry().normalize()
            self.raiseW()
            self.setGeometry(QRect(200, 200, 708, 500))
            self.show_table()
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
        
        this_address="/rule" + str(self.table.numRows())
        rr = _RoutingRow(sorted(self.__class__.sources), address=this_address)
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
        self.saving.emit(PYSIGNAL("setDirty"), (self.root_param.UpdateState,))
        return rr

    def handle_clicks(self, row, col, mb, qp):
        if col is 5 and self.table.numRows() > 1:
            self.remove_router(row)
            for r in self.routers:
                r.address = "/rule" + str(self.routers.index(r) + 1)
        if col is 6:
            self.insert_router()
            
    def remove_router(self, row):
        self.root_param.removeChild(self.routers[row])
        self.routers.pop(row).disconnect()
        QTable.removeRow(self.table, row)
        self.saving.emit(PYSIGNAL("setDirty"), (self.root_param.UpdateState,))
    
def popup():
    prp.popup(QCursor.pos())

if __name__ == "__main__":
    a = QApplication(sys.argv)
    w = QHBox()
    #w.setFixedWidth(800)
    p = Param(address="/parent")
    p1 = Param(address="/p1")
    p2 = Param(address="/p2", type=bool)
    p3 = Param(address="/p3")
    p4 = Param(address="/p4")
    p5 = Param(address="/p5")
    
    p.insertChild(p1)
    p.insertChild(p2)
    p.insertChild(p3)
    p3.insertChild(p4)
    p4.insertChild(p5)
    checkbox = ParamCheckBox(p2, w)
    slider = ParamSlider(p3, w)
    
    kuk = MiniMachine("kok", w)
    pkuk = Param(address="/pkuk")
    slider2 = ParamSlider(pkuk, kuk)
    
    kuk.root_param.insertChild(pkuk)
    kuk.add_small_toggles("/foo")
    kuk.init_controls()
    
    pp = Param(type=list, address="/foo")
    ppb = ParamLabel(pp, kuk)
    pp.set_state(["hoho"])
    
    #prp = _ParamRoutingPopup(w)
    #b = QPushButton("KUK", w)
    #pr = ParamRouting(w)
    #pr.show_table()
    #w.connect(b, SIGNAL("clicked()"), popup)
    
    #pr.init_controls(p)
    
    w.show()
    
    a.setMainWidget(w)

    a.exec_loop()
