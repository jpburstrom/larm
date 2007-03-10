#!/usr/bin/env python


import  os
import sys
from qt import *

from copy import copy
from time import sleep
from threading import Thread
from Queue import Queue

import osc
import evdev

from larm_utilities import *


class MouseLooper(Machine):
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label, canvas, parent, canvaslabel,name,fl)
        
        self.smplabel = QLabel(self)
        f = QFont("Pigiarniq Heavy", 9)
        self.smplabel.setFont(f)
        self.smplabel.setAlignment(QLabel.AlignRight)
        self.sample_loaded = None
        
        self.chkbox = QCheckBox(self.tek, "savesample")
        self.chkbox.setGeometry(0, 0, 12,12)
        QToolTip.add(self.chkbox, "Save with sample")
        
        self.slb = QHBox(self)
        self.slb.adjustSize()
        
        self.qslider = QSlider(0, 48, 4, 16, Qt.Horizontal, 
            self.slb, "Quantize Slider")
        self.qslider.setTickmarks(QSlider.Below)
        self.qslider.setTickInterval(4)
        self.state["/quantizestep"] = 0
        
        self.qslabel = QLabel("16", self.slb)
        self.qslabel.setAlignment(Qt.AlignCenter)
        self.qslabel.setMinimumWidth(20)
        
        
        self.connect(self.chkbox, SIGNAL("toggled(bool)"), 
            self.set_sample_save)
        
        self.connect(self.qslider, SIGNAL("valueChanged(int)"), 
            self.qslabel, SLOT("setNum(int)"))
        self.connect(self.qslider, SIGNAL("valueChanged(int)"), self.send_qstep)
        self.connect(qApp, PYSIGNAL("load_sample"), self.load_sample)
        
        #for samplelist (destinations)
        qApp.emit(PYSIGNAL("new_sampler"), (label,))

        self.host = getgl('osc_address')
        self.port = getgl('osc_port')
        
        #Bind the returning ping when sample is loaded to the readysignal method
        qApp.osc.bind(self.readysignal, "".join((self.slashedlabel, "/sample_loaded"))) 
        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
        self.init_controls()
        
    def update_controls(self, preset = None):
        self.qslider.setValue(self.state["/quantizestep"])
        try: 
            self.smplabel.setText(self.state["/buffer"])
        except KeyError:
            pass
            
    def readysignal(self, *s):
        if s[0][2] == 0:
            self.smplabel.setPaletteForegroundColor(QColor(255, 0, 0))
        else:
            self.smplabel.setPaletteForegroundColor(QColor('gold'))
    
    def load_sample(self, sample, path, dest):
        if dest == self.label and self.sample_loaded != sample:
            osc.sendMsg("".join([i for i in [self.slashedlabel, "/buffer"]]), [path], self.host, self.port)
            self.smplabel.setText(sample)
            self.sample_loaded = sample
            if self.chkbox.isOn():
                self.state["/buffer"] = sample
    
    def set_sample_save(self, boo):
        if boo and self.sample_loaded:
            self.state["/buffer"] = self.sample_loaded
        elif not boo and self.sample_loaded:
            self.state.pop("/buffer")
    
    def send_qstep(self, int):
        self.state["/quantizestep"] = int
        osc.sendMsg("".join([i for i in [self.slashedlabel, "/quantizestep"]]), [int], self.host, self.port)
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Pan', 'Volume'],
        ['Pitch deviation', 'Pitch'],
        ['Skip', 'Grain length'],
        ['Offset', 'Size'],
        ['Quantize amount', 'Quantize speed']
        ] )
        
    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/pan", [0.0, 1.0]),
                'REL_Y' : ("/vol", [0.0, 1.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/pitchdev", [0.0, 1.0]),
                'REL_Y' : ("/pitch", [-2.0, 2.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("/skip", [0.0, 1.0]),
                'REL_Y' : ("/grainlen", [10.0, 800.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("/offset", [0.0, 1.0]),
                'REL_Y' : ("/size", [0.0, 1.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("/quantizeamt", [0.0, 1.0]),
                'REL_Y' : ("/qspeed", [-1.0, 1.0]) },
        }

class LabelSlider(QHBox):
    def __init__(self, label, parent = None, name = None,fl = 0):
        QHBox.__init__(self, parent, name)
        self.slider = MySlider(Qt.Horizontal, 
            self, name)
        self.slider.setMinValue(0)
        self.slider.setMaxValue(1000)
        self.label = QLabel("16", self)
        self.label.setGeometry(0, 20, 20, 20)
        self.label.setText(name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(50)
            
class Grandel(Machine):
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        
        self.sliderbox = QVBox(self)
        self.controls = []
        self.slider_labels = ["/voldev", "/pandev", "/window"] #osc labels
        for i in range(3):
            self.state[self.slider_labels[i]] = 0
            slider = LabelSlider(self.slider_labels[i], self.sliderbox, self.slider_labels[i])
            self.connect(slider.slider, PYSIGNAL("valueChanged"), self.store_and_send)
            self.controls.append(slider)
        self.controls[2].slider.setMaxValue(9)
        self.controls[2].slider.setPageStep(1)

        self.windows = []
        for n in range(10):
            qp = QPixmap(QString((sys.path[0]+"/larm_utilities/wave%d.png") % (n + 1)))
            if not qp.isNull():
                self.windows.append(qp)
            else:
                raise IOError("Can't open image. What's wrong with you?")
        self.connect(self.controls[2].slider, PYSIGNAL("valueChanged"), self.on_window_change)
        self.controls[2].label.setPixmap(self.windows[0])
                
        self.freezebtn = QPushButton("Freeze", self, "/freeze")
        self.freezebtn.setMaximumHeight(16)
        self.freezebtn.setToggleButton(1)
        self.freezebtn.setFlat(1)
        self.state["/freeze"] = 0
        self.connect(self.freezebtn, SIGNAL("toggled(bool)"), self.on_freeze)
        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
        
        self.init_controls()
    
    def on_freeze(self, boo):
        self.store_and_send(self.freezebtn.name(), boo)
        if boo:
            self.freezebtn.setPaletteForegroundColor(QColor(255,0,0))
        else:
            self.freezebtn.setPaletteForegroundColor(QColor(0,0,0))
            
    def on_window_change(self, k, v):
        self.controls[2].label.setPixmap(self.windows[v])
    
    def update_controls(self, preset = None):
        for i in range(3):
            self.controls[i].slider.setValue(self.state[self.slider_labels[i]])
        self.freezebtn.setDown(self.state[self.freezebtn.name()])
        if self.state[self.freezebtn.name()]:
            self.freezebtn.setPaletteForegroundColor(QColor(255,0,0))
        else:
            self.freezebtn.setPaletteForegroundColor(QColor(0,0,0))
            
        
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Speed jitter', 'Speed'],
        ['Size jitter', 'Size'],
        ['Transp jitter', 'Transp'],
        ['Delay jitter', 'Delay'],
        ['Pan', 'Vol']
        ] )
        
    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_Y' : ("/speed", [1.5, 1000.0]),
                'REL_X' : ("/speeddev", [0.0, 100.0]) },
        self.mouseButtons[1]:
            {'REL_Y' : ("/size", [5.0, 800.0]),
                'REL_X' : ("/sizedev", [0.0, 100.0]) },
        self.mouseButtons[2] :
            {'REL_Y' : ("/transp", [-12.0, 12.0]),
                'REL_X' : ("/transpdev", [0.0, 12.0]) },
        self.mouseButtons[3]:
            {'REL_Y' : ("/delay", [0.0, 500.0]),
                'REL_X' : ("/delaydev", [0.0, 100.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("/pan", [0.0, 100.0]),
                'REL_Y' : ("/vol", [0.0, 100.0]) },
        }

class Delay(Machine):
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        self.init_controls()
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Right time', 'Left time'],
        ['Right fb', 'Left fb'],
        ['Dropout size', 'Dropout prob'],
        ['', 'Volume'],
        ['', '']
        ] )

    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/rtime", [1.5, 2000.0]),
                'REL_Y' : ("/ltime", [1.5, 2000.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/rfb", [0.0, 99.0]),
                'REL_Y' : ("/lfb", [0.0, 99.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("/gapper-size", [0.0, 100.0]),
                'REL_Y' : ("/gapper-prob", [5.0, 200.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("/vol", [0.0, 100.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("", [0.0, 100.0]) },
        }

class Room(Machine):
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)

    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Liveness', 'Distance'],
        ['Slope', 'Xfreq'],
        ['', 'Volume'],
        ['', ''],
        ['', '']
        ] )

    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/liveness", [0.0, 99.0]),
                'REL_Y' : ("/distance", [0.0, 99.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/slope", [0.0, 127.0]),
                'REL_Y' : ("/xfreq", [0.0, 99.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("/vol", [0.0, 100.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("", [0.0, 100.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("", [0.0, 100.0]) },
        }

class Combo(Machine):
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        
        self.sliderbox = QVBox(self)
        self.controls = []
        self.slider_labels = ["/lpf", "/fbk"] #osc labels
        for i in range(2):
            self.state[self.slider_labels[i]] = 0
            slider = LabelSlider(self.slider_labels[i], self.sliderbox, self.slider_labels[i])
            self.connect(slider.slider, PYSIGNAL("valueChanged"), self.store_and_send)
            self.controls.append(slider)

        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
        self.init_controls()
        
    def update_controls(self, preset = None):
        for i in range(2):
            self.controls[i].slider.setValue(self.state[self.slider_labels[i]])
        
    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Pitch 1', 'Vol 1'],
        ['Pitch 2', 'Vol 2'],
        ['Pitch 3', 'Vol 3'],
        ['Pitch 4', 'Vol 4'],
        ['Pitch 5', 'Vol 5']
        ])
        
    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/pitch-1", [27.0, 95.0]),
                'REL_Y' : ("/vol-1", [0.0, 1.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/pitch-2", [27.0, 95.0]),
                'REL_Y' : ("/vol-2", [0.0, 1.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("/pitch-3", [27.0, 95.0]),
                'REL_Y' : ("/vol-3", [0.0, 1.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("/pitch-4", [27.0, 95.0]),
                'REL_Y' : ("/vol-4", [0.0, 1.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("/pitch-5", [27.0, 95.0]),
                'REL_Y' : ("/vol-5", [0.0, 1.0]) },
        }

class MainMachine(MiniMachine):
    def init(self, *args):
        MiniMachine.__init__(self, *args)
    
    def save_snapshot(self, snap, local=True):
        """Calls save method of every machine and saves to their global snapshot thing"""
        for ma in self.parent.machines:
            print ma
            ma.save_snapshot(snap, False)
    
    def recall_snapshot(self, snap, local=True):
        for ma in self.parent.machines:
            ma.recall_snapshot(snap, False)

    def save_preset(self, preset):
        for ma in self.parent.machines:
            ma.save_preset(preset, False)

    def load_preset(self, preset):
        for ma in self.parent.machines:
            ma.load_preset(preset, False)

class RecordToDisk(QHBox):
    def __init__(self, parent):
        QHBox.__init__(self, parent)
        
        self.osc_host = getgl('osc_address')
        self.osc_port = getgl('osc_port')
        self.path = "/tmp/larm_recording"
        self.recording_number = 0
        
        self.rec_button = QPushButton(self, "rec")
        self.rec_button.setToggleButton(1)
        self.rec_button.setPaletteBackgroundColor(QColor("pink"))
        self.rec_button.setText("rec")
        self.rec_button.setFixedSize(22, 18)
        self.connect(self.rec_button, SIGNAL("toggled(bool)"), 
            self.toggle_rec)
        self.label = QLabel(self.path, self)
        #self.label.setMinimumWidth(180)
        
        self.file_dialog = QFileDialog("/home", "*.wav", self)
        self.file_dialog.setMode(QFileDialog.AnyFile)
        self.file_dialog.setCaption("Choose the base path and name for your file to record, please")
        self.connect(self.file_dialog, SIGNAL("fileSelected(const QString&)"), 
            self.set_path)
    
    def choose_recpath(self):
        self.file_dialog.show()
    
    def set_path(self, file):
        file = str(file)
        if file[-4:] == '.wav':
            file = file[-4:]
        exists = 0
        for i in range(100):
            filename = "".join((file, "%02d.wav" % i))
            if QFile.exists(QString(filename)):
                exists = 1
                break
        if not exists:
            self.change_path(file)
        else:
            f = QMessageBox.question(
                    self,
                    "Overwrite File?",
                    "A file called %s already exists, and autonumbering is on..."
                        "You may overwrite it. Continue?"
                         % filename,
                    "&Yes", "&No",
                    QString.null, 0, 1)
            if not f:
                self.change_path(file)
            else:
                QTimer.singleShot(0, self.file_dialog, SLOT("exec()"))
                
    def change_path(self, path):
        self.recording_number = 0
        self.path = path
        self.label.setText(path)
    
    def toggle_rec(self, boo):
        if boo:
            pass
            self.recording_number += 1
            file = "".join((self.path, "%02d.wav" % self.recording_number))
            self.label.setText(file)
            osc.sendMsg("/diskrec/path", [file], self.osc_host, self.osc_port)
            osc.sendMsg("/diskrec/rec", [1], self.osc_host, self.osc_port)
            self.rec_button.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg("/diskrec/rec", [0], self.osc_host, self.osc_port)
            self.rec_button.setPaletteBackgroundColor(QColor("pink"))

class ArrayRecorder(QVBox):
    def __init__(self, samplelist, parent):
        QVBox.__init__(self, parent)
        self.setMargin(3)
        self.setSpacing(2)
        self.setPaletteBackgroundColor(QColor(50,50,50))
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        textLabel2_font = QFont(self.font())
        textLabel2_font.setFamily("Pigiarniq Heavy")
        textLabel2_font.setPointSize(10)
        self.label = QLabel("Recording", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setPaletteBackgroundColor(QColor(100,50,0))
        self.label.setPaletteForegroundColor(QColor(255,255,255))
        self.label.setFont(textLabel2_font)
        self.label.setFixedHeight(20)
        self.arrays = {}
        self.arraysizes = {}
        self.buttons = {}
        self.samplelist = samplelist
        self.sltag_added = 0
        self.osc_host = getgl('osc_address')
        self.osc_port = getgl('osc_port')
        
        self.buttongroup = QButtonGroup(1, Qt.Horizontal, self)
        self.buttongroup.setExclusive(0)
        self.buttongroup.setInsideMargin(2)
        #hardcoded upper limit
        for i in range(99):
            qApp.osc.bind(self.handle_incoming, "/rick/no%d/array" % i)
            qApp.osc.bind(self.handle_incoming, "/rick/no%d/arraysize" % i)
            
        self.connect(self.buttongroup, SIGNAL("clicked(int)"), 
            self.toggle_rec)
     
    def handle_incoming(self, *oscmsg):
        add = oscmsg[0][0].split("/")
        if add[-1] == "array":
            self.arrays[add[2]] = oscmsg[0][2]
        elif add[-1] == "arraysize":
            self.arraysizes[add[2]] = oscmsg[0][2]
        if self.arraysizes.has_key(add[2]) and self.arrays.has_key(add[2]):
            if not self.sltag_added:
                self.samplelist.addtag(".:recordings")
                self.sltag_added = 1
            self.samplelist.addsample(".:recordings", self.arrays[add[2]])
            self.add_button(add[2])
            osc.sendMsg("".join(("/rick/", add[2], "/pong")), [1], 
                self.osc_host, self.osc_port)
        
    
    def add_button(self, rec):
        label = "".join((self.arrays[rec], ": %d s")) % (self.arraysizes[rec] / getgl('samplerate'))
        name = "".join(("/", rec))
        self.buttons[name] = QPushButton(label, self.buttongroup, name)
        self.buttons[name].setPaletteBackgroundColor(QColor("pink"))
        self.buttons[name].setToggleButton(1)
        self.buttons[name].show()
    
    def toggle_rec(self, boo):
        button = self.buttongroup.find(boo)
        msg = "".join(("/rick", button.name(), "/onoff"))
        if button.isOn():
            osc.sendMsg(msg, [1], self.osc_host, self.osc_port)
            button.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg(msg, [0], self.osc_host, self.osc_port)
            button.setPaletteBackgroundColor(QColor("pink"))
            
class MyDevice(evdev.Device):
    def __init__(self, filename):
        evdev.Device.__init__(self, filename)
    def resetRel(self):
        self.axes['REL_X'] = 0
        self.axes['REL_Y'] = 0

class MyMenuBar(QPushButton):

    def __init__(self, parent, name):
        QPushButton.__init__(self, parent, name)

class MyRouting(Routing):
    def __init__(self, row, col, routeToSelf = True, parent = None,name = None,fl = 0):
        Routing.__init__(self, row, col, routeToSelf = True, parent = parent,name = name,fl = 0)
        
        self.osc_labels = ["/a4loop-1", "/a4loop-2", "/a4loop-3", "/a4loop-4", 
            "/grandel-1", "/delay-1", "/combo-1", "/pm7", 
            "/adc12", "/adc3"]
        
        labels = ["Loop 1", "Loop 2", "Loop 3", "Loop 4", 
            "Grandel", "Delay", "Combo", "pm7", "adc12", "adc3"]
        self.set_row_labels(QStringList.fromStrList(labels))
        labels = ["Room", "Grandel", "Delay", "Combo", "dac3"]
        self.set_col_labels(QStringList.fromStrList(labels))
        for cl in range(1, 4):
            self.clear_cell(cl+3, cl)
        
        self.saving = MiniMachine("routing",self,"routingsave")
        self.saving.setGeometry(QRect(0,0,314,48))
        self.table1.move(QPoint(0, 50))
        
        self.connect(self, PYSIGNAL("output"), self.get_routing_data)
        self.connect(self.saving, PYSIGNAL("preset_loaded"), self.update_controls)
        self.connect(self.saving, PYSIGNAL("snapshot_loaded"), self.update_controls)
    
    def get_routing_data(self, data):
        self.saving.store_and_send(
            "".join((self.osc_labels[data[0][0]], "/send" , str(data[0][1]))) , data[1])
    
    def update_controls(self):
        for k, v in self.saving.state.items():
                o = k.split("/")
                self.setvalue(self.osc_labels.index("".join(("/", o[1]))), 
                    int(o[2][-1:]), v)
            

class GuiThread(QMainWindow):

    def __init__(self, endcommand, *args):
        QMainWindow.__init__(self, *args)
        
        self.setCaption("LARM")
        
        self.actions = {}
        
        #not used?
        self.mouse_finetune = [0]
        
        self.setFixedSize(1024, 768)
        self.setPaletteBackgroundColor(QColor(10, 10, 10))
        self.setPaletteForegroundColor(QColor('gold'))
        
        self.machines = [] #list of machine objects
        
        self.menu = QPushButton(self, "Menu")
        self.larmmenu = QPopupMenu(self, "larmmenu")
        self.menu.setPaletteForegroundColor(QColor('gold'))
        self.menu.setGeometry(2,2,40, 20)
        self.menu.setText("_/ _")
        self.menu.setPaletteBackgroundColor(QColor(50,50,50))
        self.larmmenu.setGeometry(0, 30, 200, 200)
        self.connect(self.menu, SIGNAL("clicked()"), self.larmmenu, SLOT("show()"))
        
        
        self.larmmenu.dspAction = QAction(self, "dspAction")
        self.larmmenu.dspAction.setToggleAction(1)
        self.larmmenu.dspAction.setText("DSP")
        self.larmmenu.dspAction.addTo(self.larmmenu)
        self.larmmenu.insertSeparator()
        self.larmmenu.recPathAction = QAction("Set rec path", 
            QKeySequence("F12"), self, "recPathAction")
        self.larmmenu.recPathAction.addTo(self.larmmenu)
        self.larmmenu.startTimerAction = QAction("Start timer",
            QKeySequence("F11"), self, "startTimerAction")
        self.larmmenu.startTimerAction.addTo(self.larmmenu)
        
        self.larmmenu.focusText = QAction("Edit text",
            QKeySequence("F10"), self, "focusText")
        self.larmmenu.focusText.addTo(self.larmmenu)
        self.larmmenu.focusText.setToggleAction(1)
        
        self.larmmenu.insertItem(".")
        self.larmmenu.insertItem("..")
        self.larmmenu.insertItem("...")
        self.larmmenu.quitAction = QAction(self, "quitAction")
        self.larmmenu.quitAction.setText("Quit")
        self.larmmenu.quitAction.addTo(self.larmmenu)
        
#        self.menu.insertItem("_/ _", self.larmmenu)
        
        
        self.recording = RecordToDisk(self)
        self.recording.setGeometry(50, 0, 200, 24)
        
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(0)
        
        self.timertimer = QTimer(self)
        self.timer = QLabel("00:00", self)
        self.cpulabel = QLabel("0.0%", self)
        self.cpulabel.setMinimumWidth(100)
        self.status.addWidget(self.cpulabel,0)
        self.status.addWidget(self.timer,0 )
        qApp.osc.bind(self.cpu_report, "/pd/cpu") 
        
        
        self.canvascon = QVBox(self)
        self.canvascon.setGeometry(345, 5, 305, 470)
        self.canvaslabels = Canvasinfo(self.canvascon)
        self.canvaslabels.setFixedSize(300, 148)
        self.canvas = MarioDots(self.canvascon, "Hej hej")
        self.canvas.setFixedHeight(302)
        
        #this should be before samplers(?)
        self.urack = QVBox(self)
        self.urack.setGeometry(800, 5, 200, 664)
        self.samplelist = SampleList(self.urack, "Samplelist")
        
        self.urack2 = QVBox(self.urack)
        self.urack2.setSpacing(10)
        self.mlp1 = MouseLooper("MouseLooper#1", self.canvas, self.urack2, self.canvaslabels )
        self.mlp2 = MouseLooper("MouseLooper#2", self.canvas, self.urack2, self.canvaslabels )
        self.mlp3 = MouseLooper("MouseLooper#3", self.canvas, self.urack2, self.canvaslabels )
        self.mlp4 = MouseLooper("MouseLooper#4", self.canvas, self.urack2, self.canvaslabels )
        
        self.machines.append(self.mlp1)
        self.machines.append(self.mlp2)
        self.machines.append(self.mlp3)
        self.machines.append(self.mlp4)
        
        #self.setCentralWidget(self.canvascon)
        
        #self.logoimg = QPixmap("larm_utilities/logo.png")
        #self.logo = QLabel(self)
        #self.logo.setPixmap(self.logoimg)    
        #self.logo.setGeometry(5, 40, 186,70)
        
        self.narrowbox = QVBox(self)
        self.narrowbox.setGeometry(670, 5, 110, 700)
        self.saving = MainMachine("Main", self.narrowbox, "mainsave")
        self.saving.setMaximumHeight(50)
        
        self.textedit = QTextEdit(self.narrowbox)
        self.textedit.setPaletteBackgroundColor(QColor(50,50,50))
        self.textedit.setPaletteForegroundColor(QColor("orange"))
        self.textedit.setTextFormat(Qt.PlainText)
        self.textedit.setFocusPolicy(QWidget.NoFocus)
        self.textedit.setFixedHeight(250)
        self.textedit.setHScrollBarMode(QScrollView.AlwaysOff)
        self.textedit.setVScrollBarMode(QScrollView.AlwaysOff)
        self.txtfilename = getgl("txtfile")
        if self.txtfilename[0] != "/" :
            self.txtfilename = "".join((sys.path[0], "/", self.txtfilename))
        txtfile = QFile(self.txtfilename)
        if (txtfile.open(IO_ReadOnly)):
            stream = QTextStream(txtfile)
            self.textedit.setText(stream.read())


        self.rec = ArrayRecorder(self.samplelist, self.narrowbox)
        self.rec.setMinimumHeight(200)
        self.rec.setMaximumHeight(300)

        self.routing = MyRouting(10, 5, True, self)
        self.routing.setGeometry(340, 475, 325, 250)
        self.machines.append(self.routing.saving)

        self.rack1 = QFrame(self)
        self.rack1.setGeometry(20, 30, 300, 716)
        self.pm7 =  pm7(self.rack1, "pm7")
        self.pm7.setGeometry(0, 0, 300, 325)
        self.machines.append(self.pm7.saving)
        
        self.grandel = Grandel("Grandel", self.canvas, self.rack1, self.canvaslabels)
        self.grandel.setGeometry(0, 335, 300, 150)
        self.machines.append(self.grandel)
        
        self.delay = Delay("Delay", self.canvas, self.rack1, self.canvaslabels)
        self.delay.setGeometry(0, 495, 300, 50)
        self.machines.append(self.delay)
        
        self.combo = Combo("Combo", self.canvas, self.rack1, self.canvaslabels)
        self.combo.setGeometry(0, 555, 300, 100)
        self.machines.append(self.combo)

        self.room = Room("Room", self.canvas, self.rack1, self.canvaslabels)
        self.room.setGeometry(0, 663, 300, 50)
        self.machines.append(self.room)
        
        self.setFocusPolicy(QWidget.StrongFocus)
        self.endcommand = endcommand  
        
        #This is the main mode. It's about how we treat key presses.
        #we also have the piano mode (2)
        self.current_mode = 1
        self.piano_keys = [90, 83, 88, 68, 67, 86, 71, 66, 72, 78, 74, 77,
            81, 50, 87, 51, 69, 82, 53, 84, 54, 89, 55, 85, 
            73, 57, 79, 48, 80]
        self.host = getgl('osc_address')
        self.port = getgl('osc_port')
        
        self.initActions()
        #self.disableAltAction = QAction(self, "disableAltAction")
        #self.disableAltAction.setAccel(QKeySequence("ALT"))
        
        
        self.osc_host = getgl('osc_address')
        self.osc_port = getgl('osc_port')
        
        self.connect(self.larmmenu.dspAction, SIGNAL("toggled(bool)"), self.turn_on_dsp)
        self.connect(self.larmmenu.recPathAction, 
            SIGNAL("activated()"), self.recording.choose_recpath)
        self.connect(self.larmmenu.startTimerAction, 
            SIGNAL("activated()"), self.action_start_timer)
        self.connect(self.timertimer, 
            SIGNAL("timeout()"), self.action_count_timer)
        self.connect(self.larmmenu.quitAction, SIGNAL("activated()"), self.endcommand)
        self.connect(self.larmmenu.focusText, SIGNAL("toggled(bool)"), 
            self.toggle_textedit_focus)
    
    
    def initActions(self):
        # First start with "keyPress->on, keyRelease->off" type toggles. 
        # these can't be handled by QActions, methinks.
        # they are dealed with in the keyPressEvent/keyReleaseEvent methods
        
        self.modifiers = set([4129, 4131, 4179, 4139, 4180, 4181, 4128])
        self.active_modifiers = set()
        self.stgl_keys = {
            "pressed" : {
                "q" : self.mlp1.activate,
                "w" : self.mlp2.activate,
                "e" : self.mlp3.activate,
                "r" : self.mlp4.activate,
                "a" : self.pm7.activate,
                "s" : self.grandel.activate,
                "d" : self.delay.activate,
                "f" : self.combo.activate,
                "g" : self.room.activate,
                "m" : self.ac_x_only,
                "n" : self.ac_y_only,
                "b" : self.ac_finetune,
                }, 
            "released" : {
                "q" : self.mlp1.deactivate,
                "w" : self.mlp2.deactivate,
                "e" : self.mlp3.deactivate,
                "r" : self.mlp4.deactivate,
                "a" : self.pm7.deactivate,
                "s" : self.grandel.deactivate,
                "d" : self.delay.deactivate,
                "f" : self.combo.deactivate,
                "g" : self.room.deactivate,
                "m" : self.deac_x_only,
                "n" : self.deac_y_only,
                "b" : self.deac_finetune,
            },
            "Alt_pressed" : {
                "q" : self.mlp1.on_off,
                "w" : self.mlp2.on_off,
                "e" : self.mlp3.on_off,
                "r" : self.mlp4.on_off,
                "a" : self.pm7.on_off,
                "s" : self.grandel.on_off,
                "d" : self.delay.on_off,
                "f" : self.combo.on_off,
                "g" : self.room.on_off,
             }, 
            "Alt_released" : {
                "q" : self.mlp1.on_off,
                "w" : self.mlp2.on_off,
                "e" : self.mlp3.on_off,
                "r" : self.mlp4.on_off,
                "a" : self.pm7.on_off,
                "s" : self.grandel.on_off,
                "d" : self.delay.on_off,
                "f" : self.combo.on_off,
                "g" : self.room.on_off,
             }
        }
        
        #just a silly mapping game
        self.key_mapping_list = [None for i in range(0, 91)] #->z
        for i in "abcdefghijklmnopqrstuvwxyz":
            o = eval("".join(["Qt.Key_", i.upper()]))
            self.key_mapping_list[eval("".join(["Qt.Key_", i.upper()]))] = i
        
        # then for some real actions
        
        #
        # Mouseloopers
        #
        self.actions["mlp1_tgl_active"] = QAction("mlp1 active", QKeySequence("SHIFT+Q"), self)
        self.connect(self.actions["mlp1_tgl_active"], SIGNAL("activated()"), self.mlp1.tgl_active) 
        self.actions["mlp2_tgl_active"] = QAction("mlp2 active", QKeySequence("SHIFT+W"), self)
        self.connect(self.actions["mlp2_tgl_active"], SIGNAL("activated()"), self.mlp2.tgl_active) 
        self.actions["mlp3_tgl_active"] = QAction("mlp3 active", QKeySequence("SHIFT+E"), self)
        self.connect(self.actions["mlp3_tgl_active"], SIGNAL("activated()"), self.mlp3.tgl_active) 
        self.actions["mlp4_tgl_active"] = QAction("mlp4 active", QKeySequence("SHIFT+R"), self)
        self.connect(self.actions["mlp4_tgl_active"], SIGNAL("activated()"), self.mlp4.tgl_active) 
        
        self.actions["mlp1_tgl_onoff"] = QAction("mlp1 onoff", QKeySequence("CTRL+Q"), self)
        self.connect(self.actions["mlp1_tgl_onoff"], SIGNAL("activated()"), self.mlp1.on_off) 
        self.actions["mlp2_tgl_onoff"] = QAction("mlp2 onoff", QKeySequence("CTRL+W"), self)
        self.connect(self.actions["mlp2_tgl_onoff"], SIGNAL("activated()"), self.mlp2.on_off) 
        self.actions["mlp3_tgl_onoff"] = QAction("mlp3 onoff", QKeySequence("CTRL+E"), self)
        self.connect(self.actions["mlp3_tgl_onoff"], SIGNAL("activated()"), self.mlp3.on_off) 
        self.actions["mlp4_tgl_onoff"] = QAction("mlp4 onoff", QKeySequence("CTRL+R"), self)
        self.connect(self.actions["mlp4_tgl_onoff"], SIGNAL("activated()"), self.mlp4.on_off)
        
        #
        # fx and pm7
        #
        self.actions["pm7_tgl_page"] = QAction("pm7 tglpage", QKeySequence("<"), self)
        self.connect(self.actions["pm7_tgl_page"], SIGNAL("activated()"), self.pm7.toggle_page) 
        self.actions["pm7_tgl_active"] = QAction("pm7 active", QKeySequence("SHIFT+A"), self)
        self.connect(self.actions["pm7_tgl_active"], SIGNAL("activated()"), self.pm7.tgl_active) 
        self.actions["grandel_tgl_active"] = QAction("grandel active", QKeySequence("SHIFT+S"), self)
        self.connect(self.actions["grandel_tgl_active"], SIGNAL("activated()"), 
            self.grandel.tgl_active) 
        self.actions["delay_tgl_active"] = QAction("delay active", QKeySequence("SHIFT+D"), self)
        self.connect(self.actions["delay_tgl_active"], SIGNAL("activated()"), self.delay.tgl_active) 
        self.actions["combo_tgl_active"] = QAction("combo active", QKeySequence("SHIFT+F"), self)
        self.connect(self.actions["combo_tgl_active"], SIGNAL("activated()"), self.combo.tgl_active) 
        self.actions["room_tgl_active"] = QAction("room active", QKeySequence("SHIFT+G"), self)
        self.connect(self.actions["room_tgl_active"], SIGNAL("activated()"), self.room.tgl_active) 
        
        self.actions["pm7_tgl_onoff"] = QAction("pm7 onoff", QKeySequence("CTRL+A"), self)
        self.connect(self.actions["pm7_tgl_onoff"], SIGNAL("activated()"), self.pm7.on_off) 
        self.actions["grandel_tgl_onoff"] = QAction("grandel onoff", QKeySequence("CTRL+S"), self)
        self.connect(self.actions["grandel_tgl_onoff"], SIGNAL("activated()"), self.grandel.on_off) 
        self.actions["delay_tgl_onoff"] = QAction("delay onoff", QKeySequence("CTRL+D"), self)
        self.connect(self.actions["delay_tgl_onoff"], SIGNAL("activated()"), self.delay.on_off) 
        self.actions["combo_tgl_onoff"] = QAction("combo onoff", QKeySequence("CTRL+F"), self)
        self.connect(self.actions["combo_tgl_onoff"], SIGNAL("activated()"), self.combo.on_off)
        self.actions["room_tgl_onoff"] = QAction("room onoff", QKeySequence("CTRL+G"), self)
        self.connect(self.actions["room_tgl_onoff"], SIGNAL("activated()"), self.room.on_off)
        
        #
        #misc
        #
        self.actions["sel_mode"] = QAction("pianomode", QKeySequence("Esc"), self)
        self.connect(self.actions["sel_mode"], SIGNAL("activated()"), self.tgl_modes)
        self.actions["show_numbers"] = QAction("show_numbers", QKeySequence("CapsLock"), self)
        self.connect(self.actions["show_numbers"], SIGNAL("activated()"), self.action_show_numbers)
        self.actions["machine_onoff"] = QAction("machine_onoff", QKeySequence("Space"), self)
        self.connect(self.actions["machine_onoff"], SIGNAL("activated()"), self.action_machine_onoff)
        
        self.actions["snapshot_recall"] = []
        self.actions["snapshot_save"] = []
        for i in range(4):
            self.actions["snapshot_recall"].append(QAction("snap_rc_%d" % i, 
                QKeySequence("F%d" % (i + 1)), self))
            self.connect(self.actions["snapshot_recall"][i], SIGNAL("activated()"),
                self.actionSnapshotRecall)
        for i in range(4):
            self.actions["snapshot_save"].append(QAction("snap_sv_%d" % i, 
                QKeySequence("SHIFT+F%d" % (i + 1)), self))
            self.connect(self.actions["snapshot_save"][i], SIGNAL("activated()"),
                self.actionSnapshotSave)
    
    def cpu_report(self, *msg):
        self.cpulabel.setText("%.1f" % msg[0][2])
    
    def toggle_textedit_focus(self, boo):
        if boo:
            self.textedit.setFocus()
        else:
            self.textedit.clearFocus()
    
    def turn_on_dsp(self, boo):
        if boo:
            osc.sendMsg("/pd/dsp", [1], self.osc_host, self.osc_port)
            self.menu.setText("____")
            self.menu.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg("/pd/dsp", [0], self.osc_host, self.osc_port)
            self.menu.setText("_/ _")
            self.menu.setPaletteBackgroundColor(QColor(50,50,50))
    
    def tgl_modes(self):
        self.current_mode = self.current_mode % 2 + 1
        if self.current_mode == 2:
            self.canvas.canvas.setBackgroundColor(QColor(255, 150, 150))
        else:
            self.canvas.canvas.setBackgroundColor(QColor(150, 200, 240))
    
    def action_start_timer(self):
        if self.timertimer.isActive():
            self.timertimer.stop()
            self.timer.setPaletteForegroundColor(QColor("gold"))
        else:
            self.timercount = 0
            self.timer.setText('00:00')
            self.timertimer.start(5000)
            self.timer.setPaletteForegroundColor(QColor("red"))
    
    def action_count_timer(self):
        self.timercount += 5
        print self.timercount
        min = self.timercount // 60
        sec = self.timercount % 60
        self.timer.setText('%02d:%02d' % (min, sec))
        
        
    def actionSnapshotRecall(self):
        ac = self.sender()
        i = self.actions["snapshot_recall"].index(ac)
        for ma in self.machines:
            if ma.active:
                ma.recall_snapshot(i)
    
    def actionSnapshotSave(self):
        ac = self.sender()
        i = self.actions["snapshot_save"].index(ac)
        for ma in self.machines:
            if ma.active:
                ma.save_snapshot(i)
    
    def ac_x_only(self):
        for ma in self.machines:
            ma.x_only = 1
    def ac_y_only(self):
        for ma in self.machines:
            ma.y_only = 1
    def deac_x_only(self):
        for ma in self.machines:
            ma.x_only = 0
    def deac_y_only(self):
        for ma in self.machines:
            ma.y_only = 0
    def ac_finetune(self):
        self.mouse_finetune[0] = 1
    def deac_finetune(self):
        self.mouse_finetune[0] = 0
        

    def action_machine_onoff(self):
        for ma in Machine.activeMachines:
            ma.on_off()
    
    def action_show_numbers(self):
        if Machine.shownumbers:
            Machine.shownumbers = 0
            for ma in Machine.activeMachines:
                ma.do_hide_numbers()
        else:
            Machine.shownumbers = 1
            for ma in Machine.activeMachines:
                ma.do_show_numbers()
        
            
    #filter autorepeat, ignore modified keys (except shift) and pass on as pysignals
    def keyPressEvent(self, e):
        if e.isAutoRepeat():
            e.ignore()
            return
        # Ctrl_L = 4129; Alt_L = 4131; Shift_L = 4128
        if e.key() in self.modifiers:
            self.active_modifiers.add(e.key())
        else:
            if not self.active_modifiers:
                if self.current_mode == 2:
                    try:
                        osc.sendMsg("/keyboard", [self.piano_keys.index(e.key()), 1], 
                            self.host, self.port)
                    except ValueError:
                        pass
                else:
                    try:
                        self.stgl_keys["pressed"][self.key_mapping_list[e.key()]]()
                    except KeyError:
                        pass
                    except IndexError:
                        pass
            
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt_pressed"][self.key_mapping_list[e.key()]]()
                except KeyError:
                    pass
                except IndexError:
                    pass
            

    def keyReleaseEvent(self, e):
        if e.isAutoRepeat():
            e.ignore()
            return
        if e.key() in  self.modifiers:
            self.active_modifiers.remove(e.key())
        else:
            if not self.active_modifiers:
                if self.current_mode == 2:
                    try:
                        osc.sendMsg("/keyboard", [self.piano_keys.index(e.key()), 1], 
                            self.host, self.port)
                    except ValueError:
                        pass
                else:
                    try:
                        self.stgl_keys["released"][self.key_mapping_list[e.key()]]()
                    except KeyError:
                        pass
                    except IndexError:
                        pass
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt_released"][self.key_mapping_list[e.key()]]()
                except KeyError:
                    pass
                except IndexError:
                    pass

      
    def closeEvent(self, ev):
        """
        We do nothing when window is closed...
        to prevent from disasters.
        """
        pass
        #self.endcommand()
          
class PollingThread:   
    """
    Launch the main part of the GUI and the worker thread. 
    """
    def __init__(self):
        qApp.osc = osc
        qApp.osc.init()
        qApp.inSocket = osc.createListener(getgl('osc_address'), getgl('osc_listen_port'))
        
        # Set up the GUI part
        self.gui=GuiThread(self.endApplication)
        self.gui.show()
        
        self.running = 1
        self.thread1 = Thread(target=self.workerThread1)
        self.thread1.start()
          
    def endApplication(self):
        #save notes text
        if isinstance(self.gui.txtfilename, QString):
            self.gui.txtfilename = str(self.gui.txtfilename)

        s=str(self.gui.textedit.text())

        f = open(self.gui.txtfilename, "w")
        f.write(s)
        if s[-1:] != "\n":
            f.write("\n")
        f.flush()
        
        #end
        self.running = 0
    
    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be a 'select()'.
        One important thing to remember is that the thread has to 
        yield control.
        """
        d = MyDevice(getgl("mouse_device"))
        d.axes['REL_X'], d.axes['REL_Y'] = 0, 0
        poll = d.poll
        resetRel = d.resetRel
        finetune = self.gui.mouse_finetune
        machines = Machine.activeMachines
        polltime = getgl('polltime')
        host = getgl('osc_address')
        port = getgl('osc_port')
        while self.running:
            qApp.osc.getOSC(qApp.inSocket) 
            if machines:
                poll()
                if finetune[0]:
                    d.axes['REL_X'] /= 20.0
                    d.axes['REL_Y'] /= 20.0
                for m in machines:
                    m.handle_mouse(d, host, port)
                resetRel()
            sleep( polltime)
        print "Closing..."
        a.quit()
try:
    import psyco
    psyco.bind(PollingThread)
    psyco.bind(Machine.handle_mouse)
    psyco.bind(Machine.update_canvas)
except ImportError:
    "Can't import psyco. What do we do?"


a = QApplication(sys.argv)
QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
client = PollingThread()
a.setMainWidget(client.gui)
a.exec_loop()
                

