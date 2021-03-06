#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
#TODO: Perhaps move all osc sending functions to param or similar
#TODO: Large window with all ~ routing

import  os
import sys
from qt import *

from copy import copy
from time import sleep
import evdev

from larm_utilities import *

class MouseLooper(Machine):
    """GUI for the looping machine. """
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label, canvas, parent, name)
                
        self.buffer_param = Param(type=list, address="/buffer")
        self.buffer_param.set_saveable(0)
        self.root_param.insertChild(self.buffer_param)
        
        self.smplabel = ParamLabel(self.buffer_param, self)
        self.smplabel.setAlignment(QLabel.AlignRight)
        self.setAcceptDrops(1)
        self.sample_loaded = None
        self.sample_path = None
        
        self.qslider_param = Param(address="/quantizestep", type=int, max=48, min=0)
        self.root_param.insertChild(self.qslider_param)
        self.qslider = LabelSlider(self.qslider_param, "Quantize Slider", self)
        self.qslider.setTickInterval(4)
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self)
        self.mastertempo_sl.setTickInterval(4)
        self.root_param.insertChild(self.mastertempo)

        self.connect(qApp, PYSIGNAL("load_sample"), self.load_sample)
        
        #for samplelist (destinations)
        qApp.emit(PYSIGNAL("new_sampler"), (label,))

        self.host = getgl('osc_address')
        self.port = getgl('osc_port')
        
        self.add_small_toggles("/snap_to_onsets", "/lfskip", "/invert_pitch", "/pquant", "/quantizeamt")
        
        #Bind the returning ping when sample is loaded to the readysignal method
        qApp.osc.bind(self.readysignal, "".join((self.address, "/sample_loaded"))) 
        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
        
    def update_controls(self, preset = None):
        #FIXME: this is crazy.
        try: 
            self.smplabel.setText(self.state["/buffer"].split("/")[-1].split(".")[0])
        except KeyError:
            pass
            
    def readysignal(self, *s):
        if s[0][2] == 0:
            self.smplabel.setPaletteForegroundColor(QColor(255, 0, 0))
        else:
            self.smplabel.setPaletteForegroundColor(QColor('gold'))
    
    def load_sample(self, lst):
        self.sample_path = path
        if self.sample_loaded != lst:
            self.buffer_param.set_state(lst)
            self.sample_loaded = lst
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Pan', 'Volume'),
        ('Pitch deviation', 'Pitch'),
        ('Skip', 'Grain length'),
        ('Offset', 'Size'),
        ('Grain interpolation', 'Quantize speed')
        ) )
        
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
            {'REL_X' : ("/interpolation", [0.0, 1.0]),
                'REL_Y' : ("/qspeed", [-1.0, 1.0]) },
        }
    def dragEnterEvent(self, ev):
        try:
            ev.source().current
        except AttributeError:
            pass
        else:
            self.highlight(1)
            ev.accept()
    def dragLeaveEvent(self, ev):
        self.highlight(0)
        
    def dropEvent(self, ev):
        li = ev.source().current
        self.highlight(0)
        self.load_sample(li)
    def highlight(self,boo):
        if boo:
            self.setPaletteBackgroundColor(QColor(75,50,50))
        else:
            self.setPaletteBackgroundColor(QColor(50,50,50))

class LabelSlider(QHBox):
    """Just a slider with a label beside it."""
    def __init__(self, param, label, parent = None, name = None):
        QHBox.__init__(self, parent, name)
        if name is None:
            name = label
        self.slider = ParamSlider(param, Qt.Horizontal, 
            self, name)
        ##self.slider.setTickmarks(QSlider.Below)
        self.slider.setTickInterval(50)
        self.slider.setPageStep(4)
        self.label = QLabel("16", self)
        self.label.setGeometry(0, 20, 20, 20)
        self.label.setText(name)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumWidth(50)
    
    def setPageStep(self, v):
        self.slider.setPageStep(v)
    
    def setTickInterval(self, v):
        self.slider.setTickInterval(v)
            
class Grandel(Machine):
    """GUI for the granulator"""
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label,canvas, parent,name)
        
        self.is_receiver(1)
        
        self.container = QHBox(self)
        self.sliderbox = QVBox(self.container)
        self.controls = []
        self.params = []
        self.slider_labels = ["/voldev", "/pandev", "/transpdevq", "/window"] #osc labels
        for i in range(3):
            self.params.append(Param(type=float, address=self.slider_labels[i], max=100, min=0))
            self.root_param.insertChild(self.params[i])
            slider = ParamProgress(self.params[i], self.sliderbox)
            self.controls.append(slider)
            QToolTip.add(slider, self.slider_labels[i])
        self.params[2].set_max_value(48)
        ##window chooser
        self.windowchooser = QVBox(self.container)
        self.windowchooser.setSpacing(1)
        self.params.append(Param(type=int, address=self.slider_labels[3], max=9, min=0))
        self.root_param.insertChild(self.params[3])
        slider = ParamSlider(self.params[3], self.windowchooser)
        self.controls.append(slider)
        slider.setMinimumWidth(50)
        self.windowlabel = QLabel("", self.windowchooser)
        self.windowlabel.setMinimumWidth(50)
        self.controls[3].setPageStep(1)
        self.windows = []
        for n in range(10):
            qp = QPixmap(QString((sys.path[0]+"/larm_utilities/wave%d.png") % (n + 1)))
            if not qp.isNull():
                self.windows.append(qp)
            else:
                raise IOError("Can't open image. What's wrong with you?")
        self.connect(self.controls[3], SIGNAL("valueChanged(int)"), self.on_window_change)
        self.windowlabel.setPixmap(self.windows[0])
        
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self)
        self.mastertempo_sl.setTickInterval(4)
        self.root_param.insertChild(self.mastertempo)
        
        self.add_small_toggles("/freeze", "/gliss")
        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
    
    def on_window_change(self, v):
        self.windowlabel.setPixmap(self.windows[9-v])
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Speed jitter', 'Speed'),
        ('Size jitter', 'Size'),
        ('Transp jitter', 'Transp'),
        ('Delay jitter', 'Delay'),
        ('Pan', 'Vol')
        ) )
        
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
    """GUI for the delay"""
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label,canvas, parent,name)
        
        self.is_receiver(1)
        
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self)
        self.mastertempo_sl.setTickInterval(4)
        self.root_param.insertChild(self.mastertempo)
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Right time', 'Left time'),
        ('Right fb', 'Left fb'),
        ('Dropout size', 'Dropout prob'),
        ('', 'Volume'),
        ('', '')
        ) )

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

class Spectrldly(Machine):
    """GUI for the delay"""
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label,canvas, parent,name)
        
        p = Param(type=float, address="/pan_spread", min=0, max=1)
        sl = ParamProgress(p, self)
        self.root_param.insertChild(p)
        
        self.is_receiver(1)
        
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Time mod', 'Delay Time'),
        ('Mod Quant', 'Feedback'),
        ('Mod regen time', 'Mod rand'),
        ('Notch Freq', 'Notch Q'),
        ('Phase Offset', 'Volume')
        ) )

    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/time_mod", [0.0, 1.0]),
                'REL_Y' : ("/delay_time", [0.0, 1.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/mod_quant", [0.0, 1.0]),
                'REL_Y' : ("/feedback", [0.0, 1.0]) },
        self.mouseButtons[2] :
            {'REL_X' : ("/mod_regen_time", [0.0, 1.0]),
                'REL_Y' : ("/mod_rand", [0.0, 1.0]) },
        self.mouseButtons[3]:
            {'REL_X' : ("/notch_freq", [0.0, 1.0]),
                'REL_Y' : ("/notch_q", [0.0, 1.0]) },
        self.mouseButtons[4]:
            {'REL_X' : ("/phase_offset", [0.0, 1.0]),
                'REL_Y' : ("/vol", [0.0, 1.0]) },
        }


class Room(Machine):
    """GUI for the room/reverb"""
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label,canvas, parent,name)
        
        self.is_receiver(1)
        
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Liveness', 'Distance'),
        ('Slope', 'Xfreq'),
        ('Distortion', 'Volume'),
        ('', ''),
        ('', '')
        ) )

    def set_mouse_parameters(self):
        self.mouse_parameters =   {
        self.mouseButtons[0] :
            {'REL_X' : ("/liveness", [0.0, 99.0]),
                'REL_Y' : ("/distance", [0.0, 99.0]) },
        self.mouseButtons[1]:
            {'REL_X' : ("/slope", [0.0, 127.0]),
                'REL_Y' : ("/xfreq", [0.0, 99.0]) },
        self.mouseButtons[2]:
            {'REL_X' : ("/distortion", [0.0, 100.0]),
                'REL_Y' : ("/vol", [0.0, 100.0]) },
        self.mouseButtons[3] :
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("", [0.0, 100.0]) },
            self.mouseButtons[4]:
            {'REL_X' : ("", [0.0, 100.0]),
                'REL_Y' : ("", [0.0, 100.0]) },
        }

class Combo(Machine):
    """GUI for the comb filter"""
    def __init__(self,label,canvas, parent = None, name = None):
        Machine.__init__(self,label,canvas, parent,name)
        
        self.sliderbox = QVBox(self)
        self.controls = []
        self.params = []
        self.slider_labels = ["/lpf", "/fbk"] #osc labels
        for i in range(2):
            self.state[self.slider_labels[i]] = 0
            self.params.append(Param(address=self.slider_labels[i], 
                min=0, max=1000))
            self.root_param.insertChild(self.params[i])
            self.controls.append(LabelSlider(self.params[i], self.slider_labels[i], 
                self.sliderbox, self.slider_labels[i]))
        
        self.is_receiver(1)
            
    def generate_label_tuple(self):
        self.label_tuple = (self.label, (
        ('Pitch 1', 'Vol 1'),
        ('Pitch 2', 'Vol 2'),
        ('Pitch 3', 'Vol 3'),
        ('Pitch 4', 'Vol 4'),
        ('Pitch 5', 'Vol 5')
        ))
        
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
    """The Main machine takes care of saving and loading global presets"""
    
    def __init__(self, *args):
        MiniMachine.__init__(self, *args)
        
        self.dspbutton = QPushButton("_/ _", self)
        self.dspbutton.setToggleButton(1)
        
        self.tempo = Param(address="/tempo", type=float, min=10, max=200)
        self.root_param.insertChild(self.tempo)
        
        self.sliderbox = QVBox(self)
        QLabel("Master Tempo", self.sliderbox)
        self.temposlider = ParamProgress(self.tempo, self.sliderbox)
        self.tap_param = Param(type=Bang, address="/tap")
        self.tap = ParamPushButton(self.tap_param, self.sliderbox)
        self.tap.setMinimumWidth(20)
        self.tap.setText("Tap")
        self.tempo.insertChild(self.tap_param)
        
        QLabel("Master Pitch", self.sliderbox)
        self.masterpitch = Param(address="/pitch", type=float, min=0, max=2)
        self.masterpitchslider = ParamProgress(self.masterpitch, self.sliderbox)
        self.root_param.insertChild(self.masterpitch)
        
        QLabel("Master Volume", self.sliderbox)
        self.mastervolume = Param(address="/volume", type=float, min=0, max=2)
        self.mastervolumeslider = ParamProgress(self.mastervolume, self.sliderbox)
        self.root_param.insertChild(self.mastervolume)
        
        self.send_all_controls = Param (address="/send_all_controls", type=Bang)
        self.root_param.insertChild(self.send_all_controls)
        
        self.connect(self.send_all_controls, PYSIGNAL("paramUpdate"), self.sendall)
    
    def sendall(self, update=False):
        self.root_param.send_to_osc(True) #recursive
        
class RecordToDisk(QHBox):
    """A Recording button for capturing what's coming out."""
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
            osc.sendMsg("/main/diskrec/path", [file], self.osc_host, self.osc_port)
            osc.sendMsg("/main/diskrec/rec", [1], self.osc_host, self.osc_port)
            self.rec_button.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg("/main/diskrec/rec", [0], self.osc_host, self.osc_port)
            self.rec_button.setPaletteBackgroundColor(QColor("pink"))

class ArrayRecorder(QVBox):
    """A box which generates a recording button for every array 
    recorder in the backend, and lists them in the sampling list."""
    
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
        reclist = ['pm7', 'grandel', 'a4loop1', 'a4loop2', 'a4loop3',
            'a4loop4', 'adc3', 'adc12']
        for i in reclist:
            qApp.osc.bind(self.handle_incoming, "/rick/%s/array" % i)
            qApp.osc.bind(self.handle_incoming, "/rick/%s/arraysize" % i)
            
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
            self.samplelist.addsample(".:recordings", [self.arrays[add[2]]])
            self.add_button(add[2])
            osc.sendMsg("".join(("/main/rick/", add[2], "/pong")), [1], 
                self.osc_host, self.osc_port)
        
    def add_button(self, rec):
        label = "".join((self.arrays[rec], ": %d s")) % \
            (self.arraysizes[rec] / getgl('samplerate'))
        name = "".join(("/", rec))
        self.buttons[name] = QPushButton(label, self.buttongroup, name)
        self.buttons[name].setPaletteBackgroundColor(QColor("pink"))
        self.buttons[name].setToggleButton(1)
        self.buttons[name].show()
    
    def toggle_rec(self, boo):
        button = self.buttongroup.find(boo)
        msg = "".join(("/main/rick", button.name(), "/onoff"))
        if button.isOn():
            osc.sendMsg(msg, [1], self.osc_host, self.osc_port)
            button.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg(msg, [0], self.osc_host, self.osc_port)
            button.setPaletteBackgroundColor(QColor("pink"))
            

class MyArduino(MiniMachine):
    """Creates params for the Arduino glove"""
    
    def __init__(self, *args):
        MiniMachine.__init__(self, "arduino", *args)
        
        self.glove = Param(address="/glove")
        self.glove.set_saveable(0)
        self.led = Param(address="/led")
        self.led.set_saveable(0)
        self.root_param.insertChild(self.glove)
        self.root_param.insertChild(self.led)
        
        l = ["/x", "/y", "/z", "/f1", "/f2", "/f3"] 
        gloveparams = []
        for i, p in enumerate(l):
            gloveparams.append(Param(address=p, min=0, max=1))
            gloveparams[i].set_saveable(0)
            self.glove.insertChild(gloveparams[i])

        self.rescale = Param(address="/rescale")
        self.root_param.insertChild(self.rescale)
        self.rescaleparams = []
        self.clabel = QLabel("Calibrate", self)
        for i, p in enumerate(l):
            box = QHBox(self)
            lab = QLabel(p, box)
            self.rescaleparams.append(Param(address=p,type=bool))
            self.rescale.insertChild(self.rescaleparams[i])
            setmin = Param(address="/set_min", type=Bang)
            minbutton = ParamPushButton(setmin, box)
            self.rescaleparams[i].insertChild(setmin)
            minbutton.setText("Set Min")
            setmax = Param(address="/set_max", type=Bang)
            self.rescaleparams[i].insertChild(setmax)
            maxbutton = ParamPushButton(setmax, box)
            maxbutton.setText("Set Max")
            max = Param(address="/max", type=float)
            min = Param(address="/min", type=float)
            self.rescaleparams[i].insertChild(min)
            self.rescaleparams[i].insertChild(max)
            
            lab2 = ParamProgress(gloveparams[i], box)
            lab2.setFixedWidth(100)
            
            
        self.button1 = Param(address="/button1", type=bool)
        self.button2 = Param(address="/button2", type=bool)
        self.glove.insertChild(self.button1)
        self.glove.insertChild(self.button2)
        
        leds = []
        for i in range(4):
            leds.append(Param(address="/led" + str(i+1), type=bool))
            leds[i].set_saveable(0)
            self.led.insertChild(leds[i])
        
        self.escapeaction = QAction(self, "closeme")
        self.escapeaction.setAccel("Esc")
        self.connect(self.escapeaction, SIGNAL("activated()"), self, SLOT("hide()"))

class MyMenu(QPopupMenu):
    """The beautiful menu button"""
    def __init__(self, parent, name):
        QPopupMenu.__init__(self, parent, name)
        p = self.parent()
        p.recPathAction = QAction("Set rec path", 
            QKeySequence("F12"), p)
        p.recPathAction.addTo(self)
        p.startTimerAction = QAction("Start timer",
            QKeySequence("F11"), p)
        p.startTimerAction.addTo(self)
        
        p.focusText = QAction("Edit text", QKeySequence("F10"), p)
        p.focusText.addTo(self)
        p.focusText.setToggleAction(1)
        #p.toggleParamRouting = QAction("Param Routing",
        #    QKeySequence("F9"), p, "toggleParamRouting")
        #p.toggleParamRouting.addTo(self)
        p.toggleLogWindow = QAction("Log Window", QKeySequence("F9"), p)
        p.toggleLogWindow.addTo(self)
        #p.toggleArduinoCalib = QAction("Arduino Calibration", QKeySequence("F7"), p, "toggleArduinoCalib")
        #p.toggleArduinoCalib.addTo(self)
        p.toggleMiddleStack = QAction(
            "Toggle Canvas/Save paths/...", QKeySequence("Shift+F9"), p)
        p.helpWindow = QAction(
            "Toggle Canvas/Save paths/...", QKeySequence("Shift+F10"), p)
        #p.toggleArduinoCalib.addTo(self)
        p.restart_pd = QAction(p, "restart_pd")
        p.restart_pd.setText("Restart PD")
        p.restart_pd.addTo(self)
        p.start_pd = QAction(p, "start_pd")
        p.start_pd.setText("Start PD")
        p.start_pd.addTo(self)
        p.stop_pd = QAction(p, "stop_pd")
        p.stop_pd.setText("Stop PD")
        p.stop_pd.addTo(self)
        p.pd_gui = QAction(p)
        p.pd_gui.setText("Show PD gui (after restart)")
        p.pd_gui.setToggleAction(1)
        p.pd_gui.addTo(self)
        p.sendctrl = QAction(p, "sendctrl")
        p.sendctrl.setText("Send all controls")
        p.sendctrl.addTo(self)
        p.oscdebug = QAction(p, "oscdebug")
        p.oscdebug.setText("Debug OSC")
        p.oscdebug.setToggleAction(1)
        p.oscdebug.addTo(self)
        p.quitAction = QAction(self, "quitAction")
        p.quitAction.setText("Quit")
        p.quitAction.addTo(self)
        
class MyTextEdit(QTextEdit):
    def __init__(self, *args):
        QTextEdit.__init__(self, *args)
    
    def keyPressEvent(self, ev):
        QTextEdit.keyPressEvent(self, ev)

class GuiThread(QMainWindow):
    """The main GUI thread, where everything happens (almost)
    
    Loads all UI classes and places them in the correct position. Collects all
    params and gives them a proper parent, "/main". Does all the action/keyboard
    shortcut stuff that is so damn hard to maintain."""

    def __init__(self, starter, *args):
        QMainWindow.__init__(self, *args)
        
        #Disable Param tree updates for faster loading
        dummy_update_param = Param()
        dummy_update_param.set_updates_enabled(0)
        
        #calling object
        self.starter = starter
        
        self.setCaption("LARM")
        
        self.actions = {}
        #This is a tuple, so the background thread can keep a reference
        #to it...
        self.mouse_finetune = [0]
        
        self.setFixedSize(1024, 768)
        self.setPaletteBackgroundColor(QColor(10, 10, 10))
        self.setPaletteForegroundColor(QColor('gold'))
        
        #THA MENU
        self.menubutton = QPushButton(self, "Menu")
        self.menubutton.setPaletteForegroundColor(QColor('gold'))
        self.menubutton.setGeometry(2,2,40, 20)
        self.menubutton.setText("menu")
        self.menubutton.setPaletteBackgroundColor(QColor(50,50,50))
        self.larmmenu = MyMenu(self, "larmmenu")
        self.larmmenu.setGeometry(0, 30, 200, 200)
        self.connect(self.menubutton, SIGNAL("clicked()"), self.larmmenu, SLOT("show()"))
      
        #THA RECORDER
        self.recording = RecordToDisk(self)
        self.recording.setGeometry(50, 0, 250, 24)
        
        #THA STATUSBAR
        self.status = self.statusBar()
        self.status.setSizeGripEnabled(0)
        self.timertimer = QTimer(self)
        self.timer = QLabel("00:00", self)
        self.cpulabel = QLabel("0.0%", self)
        self.cpulabel.setMinimumWidth(100)
        self.status_paramlabel = QLabel("Param", self)
        self.status_paramlabel.setMinimumWidth(200)
        self.status.addWidget(self.cpulabel,0)
        self.status.addWidget(self.timer,0 )
        self.status.addWidget(self.status_paramlabel, 0)
        qApp.osc.bind(self.cpu_report, "/pd/cpu") 
        
######################################################
##MIDDLE RACK
######################################################

        self.middle_rack = QVBox(self)
        self.middle_rack.setGeometry(320, 5, 330, 700)
        self.middle_rack.setSpacing(2)

        self.saving = MainMachine("Main", self.middle_rack, "mainsave")
        #self.saving.setFixedHeight(150)
        
        
        ##RUGAR crap
        """
        diskplayparams = []
        pop = QVBox(self.middle_rack)
        brack = QHBox(pop)
        pop.setPaletteBackgroundColor(QColor(55,0,0))
        p = Param(address="/diskplayvol", type=float, min=0, max=100)
        diskplayparams.append(p)
        ctl = ParamProgress(p, brack)
        brack.setStretchFactor(ctl, 2) 
        p = Param(address="/diskplaynext", type=Bang)
        diskplayparams.append(p)
        ctl = ParamPushButton(p, brack)
        brack.setStretchFactor(ctl, 1) 
        ctl.setText("Play (next)")
        p = Param(address="/diskplaystop", type=Bang)
        diskplayparams.append(p)
        ctl = ParamPushButton(p, brack)
        brack.setStretchFactor(ctl, 1) 
        ctl.setText("Stop")
        p = Param(address="/diskplayreset", type=Bang)
        diskplayparams.append(p)
        ctl = ParamPushButton(p, brack)
        brack.setStretchFactor(ctl, 1) 
        ctl.setText("Reset")
        p = Param(address="/diskplayseek", type=float)
        diskplayparams.append(p)
        ctl = ParamProgress(p, pop)
        p = Param(address="/diskplaystatus", type=str)
        diskplayparams.append(p)
        label = ParamLabel(p, pop)
        label.setText("This is the disk player")
        """
        
        self.middle_stack = QWidgetStack(self.middle_rack)
        self.canvas = LarmCanvas(self.middle_stack, "Hej hej")
        self.middle_stack.addWidget(self.canvas, 0)
        
        self.save_selector = SaveSelector(self.middle_stack)
        self.middle_stack.addWidget(self.save_selector, 1)
        
        #this should be before samplers(?)
        self.urack = QVBox(self)
        self.urack.setGeometry(800, 5, 200, self.height())
        self.samplelist = SampleList(self.urack, "Samplelist")
        
######################################################
##MACHINES
######################################################    

        
        self.machines = [] #list of machine objects

        #NB: Param routing is disabled
        #self.param_routing = ParamRouting(self)
        #self.param_routing.setGeometry(670, 5, 110, 50)
        #self.param_routing.show()
##        self.param_routing.tpr = QAction(self.param_routing, "toggleParamRouting")
##        self.param_routing.tpr.setAccel(QKeySequence("F9"))
##        self.param_routing.tpr.setToggleAction(0)
        
        #self.machines.append(self.param_routing.saving)
        
        self.urack2 = QVBox(self.urack)
        self.urack2.setSpacing(2)
        self.mlp1 = MouseLooper("MouseLooper1", self.canvas, 
            self.urack2)
        self.mlp2 = MouseLooper("MouseLooper2", self.canvas, 
            self.urack2)
        self.mlp3 = MouseLooper("MouseLooper3", self.canvas, 
            self.urack2)
        self.mlp4 = MouseLooper("MouseLooper4", self.canvas, 
            self.urack2)
        
        for m in (self.mlp1, self.mlp2, self.mlp3, self.mlp4):
            self.machines.append(m)
            m.root_param.set_save_address("/mouselooper")
            
        self.narrowbox = QVBox(self)
        self.narrowbox.setGeometry(650, 5, 140, 670)
        self.narrowbox.setSpacing(4)

        
        ##RUGAR crap
        #[self.saving.root_param.insertChild(p) for p in diskplayparams]
        
        
        self.textedit = MyTextEdit(self.narrowbox)
        self.textedit.setPaletteBackgroundColor(QColor(50,50,50))
        self.textedit.setPaletteForegroundColor(QColor("gray"))
        self.textedit.setTextFormat(Qt.PlainText)
        self.textedit.setFocusPolicy(QWidget.NoFocus)
        self.textedit.setFont(QFont(QString("DejaVu Sans Mono"), 7))
        #self.textedit.setFixedHeight(50)
        self.textedit.setHScrollBarMode(QScrollView.AlwaysOff)
        self.textedit.setVScrollBarMode(QScrollView.AlwaysOff)
        self.txtfilename = getgl("txtfile")
        if self.txtfilename[0] != "/" :
            self.txtfilename = "".join((sys.path[0], "/", self.txtfilename))
        txtfile = QFile(self.txtfilename)
        if (txtfile.open(IO_ReadOnly)):
            stream = QTextStream(txtfile)
            self.textedit.setText(stream.read())
        
        self.sends = RoutingView(5, self.narrowbox)
        self.sends.setMinimumHeight(200)
        
        self.logwindow = QTextEdit(self)
        self.logwindow.setFont(QFont("DejaVu Sans Mono", 7))
        self.logwindow.setTextFormat(Qt.LogText)
        self.logwindow.setPaletteBackgroundColor(QColor(50,50,50))
        self.logwindow.setPaletteForegroundColor(QColor("orange"))
        self.logwindow.setHScrollBarMode(QScrollView.AlwaysOff)
        self.logwindow.setVScrollBarMode(QScrollView.AlwaysOff)
        self.logwindow.setFocusPolicy(QWidget.NoFocus)
        self.logwindow.setGeometry(320, 710, 475, 55) 
        self.logwindow.show()
#        self.logfile = QFile("/tmp/pdlog")
#        if (self.logfile.open(IO_ReadOnly)):
#            self.stream = QTextStream(txtfile)  
#        self.logwindow.append(self.stream.read())

        self.rec = ArrayRecorder(self.samplelist, self.narrowbox)
        self.rec.setFixedHeight(300)
        
        self.rack1 = QVBox(self)
        self.rack1.setGeometry(20, 30, 300, 716)
        self.rack1.setSpacing(2)
        self.pm7 =  pm7(self.rack1, "pm7")
        self.machines.append(self.pm7.saving)
        
        self.grandel = Grandel("Grandel", self.canvas, self.rack1)
        self.machines.append(self.grandel)
        
        self.delay = Delay("Delay", self.canvas, self.rack1)
        self.machines.append(self.delay)
        
#       self.spectrldly = Spectrldly("SpectrlDly", self.canvas, self.rack1)
#       self.machines.append(self.spectrldly)
        
        self.combo = Combo("Combo", self.canvas, self.middle_rack)
        self.machines.append(self.combo)

        self.room = Room("Room", self.canvas, self.middle_rack)
        self.machines.append(self.room)
        
##        self.my_arduino = MyArduino(self)
##        self.my_arduino.setGeometry(200,200,300,300)
##        self.saving.root_param.insertChild(self.my_arduino.root_param)
##        self.my_arduino.hide()
##        self.my_arduino.init_controls()
        
        ##Hook up all machines to base
        dummy_update_param.set_updates_enabled(1)
        for ma in self.machines:
            self.saving.root_param.insertChild(ma.root_param)
            if True: #ma is not self.param_routing.saving:
                qApp.splash.message("Initing %s" % ma.label.title())
                ma.init_controls()
                #TODO: add init sends
                ma.show()
                
        self.saving.init_controls()
        
        self.save_selector.rebuild(self.saving.root_param)
        
        #qApp.splash.message("Initing Param routing")
        #self.param_routing.init_controls(self.saving.root_param)
        self.pm7.show()
        
######################################################
##EPILOGUE
######################################################
  
        self.setFocusPolicy(QWidget.StrongFocus)
        self.setFocus()
        
        self.endcommand = self.starter.endApplication
        
        #This is the main mode. It's about how we treat key presses.
        #we also have the piano mode (2)
        self.current_mode = 1
        if not getgl('accordion_mode'):
            self.piano_keys = [90, 83, 88, 68, 67, 86, 71, 66, 
            72, 78, 74, 77, 81, 50, 87, 51, 69, 82, 53, 84, 54, 
            89, 55, 85, 73, 57, 79, 48, 80]
        elif getgl('accordion_mode') is 1:
            self.piano_keys = [90, 83, 69, 88, 68, 82, 67, 70, 
            84, 86, 71, 89, 66, 72, 85, 78, 74, 73, 77, 75, 79, 
            44, 76, 80, 46]
        else:
            self.piano_keys = [81,50,65,87,51,90,83,69,52,88,68,82,
            53,67,70,84,54,86,71,89,55,66,72,85,56,78,74,73,57,77,75,
            79,48,44,76,80,43,46]

        self.host = getgl('osc_address')
        self.port = getgl('osc_port')
        
        self.initActions()
        #self.disableAltAction = QAction(self, "disableAltAction")
        #self.disableAltAction.setAccel(QKeySequence("ALT"))
        
        
        self.osc_host = getgl('osc_address')
        self.osc_port = getgl('osc_port')
        
        self.connect(qApp, PYSIGNAL("machine_activated()"), self.machine_activated)
        self.connect(qApp, PYSIGNAL("machine_deactivated()"), self.machine_deactivated)
        self.connect(self.saving.dspbutton, SIGNAL("toggled(bool)"), self.turn_on_dsp)
        self.connect(self.recPathAction, 
            SIGNAL("activated()"), self.recording.choose_recpath)
        self.connect(self.startTimerAction, 
            SIGNAL("activated()"), self.action_start_timer)
        self.connect(self.timertimer, 
            SIGNAL("timeout()"), self.action_count_timer)
        self.connect(self.quitAction, SIGNAL("activated()"), self.endcommand)
        self.connect(self.focusText, SIGNAL("toggled(bool)"), 
            self.menu_actions)
##        self.connect(self.toggleParamRouting, SIGNAL("activated()"), 
##            self.param_routing.toggle_show)
        self.connect(self.toggleLogWindow, SIGNAL("activated()"), 
            self.menu_actions)
        self.connect(self.toggleMiddleStack, SIGNAL("activated()"), 
            self.menu_actions)
        self.connect(self.helpWindow, SIGNAL("activated()"), 
            self.menu_actions)
##        self.connect(self.toggleArduinoCalib, SIGNAL("activated()"),
##            self.toggle_arduino_calibration)
##        self.connect(self.param_routing.tpr, SIGNAL("activated()"), 
##            self.param_routing.toggle_show)
        self.connect(self.sendctrl, SIGNAL("activated()"), self.saving.sendall)
        self.connect(self.oscdebug, SIGNAL("toggled(bool)"), self.action_oscdebug)
        self.connect(qApp, PYSIGNAL("paramEcho"), self.show_param_echo)
        
    def initActions(self):
        # First start with "keyPress->on, keyRelease->off" type toggles. 
        # these can't be handled by QActions, methinks.
        # they are dealed with in the keyPressEvent/keyReleaseEvent methods
        
        #Modifiers: Ctrl, Alt, Win, ?, ?, Alt Gr, Shift
        self.modifiers = set([4129, 4131, 4179, 4139, 4180, 4181, 4128])
        self.active_modifiers = set()
        
        self.stgl_keys = get_keyboard(self)["tgl_keys"]
        
        #This is somehow related to piano mode
        self.key_mapping_list = [None for i in range(0, 91)] #->z
        for i in "abcdefghijklmnopqrstuvwxyz0123456789":
            o = eval("".join(["Qt.Key_", i.upper()]))
            self.key_mapping_list[eval("".join(["Qt.Key_", i.upper()]))] = i
        
        # then for some real actions
        #
        # Mouseloopers
        #
        for key, this_action in get_keyboard(self)["push_keys"].items():
            self.actions[str(this_action)] = QAction(self)
            self.actions[str(this_action)].setAccel(QKeySequence(key))
            self.connect(self.actions[str(this_action)], SIGNAL("activated()"), 
            this_action)
        del key, this_action
        
        ##some special shortcuts...
        
        for i in range(4):
            q = QAction("snap_rc_%d" % i, QKeySequence("F%d" % (i + 1)), self)
            self.connect(q, SIGNAL("activated()"), self.actionSnapshotRecall)
            q.myindex = i
            q = QAction("snap_sv_%d" % i, QKeySequence("SHIFT+F%d" % (i + 1)), self)
            self.connect(q, SIGNAL("activated()"), self.actionSnapshotSave)
            q.myindex = i
            q = QAction("seq_play_%d" % i, QKeySequence("F%d" % (i + 5)), self)
            self.connect(q, SIGNAL("activated()"), self.actionSeqRec)
            q.myindex = i
            q = QAction("seq_rec_%d" % i, QKeySequence("SHIFT+F%d" % (i + 5)), self)
            self.connect(q, SIGNAL("activated()"), self.actionSeqPlay)
            q.myindex = i
                
    def cpu_report(self, *msg):
        self.cpulabel.setText("%.1f" % msg[0][2])
        
    def deactivate_all(self):
        [ma.deactivate() for ma in self.machines if ma.active]
        self.toggle_piano_mode(0)
        self.logwindow.setGeometry(320, 710, 475, 55)
    
    def stop_all(self):
        [ma.on_off(0) for ma in self.machines]
      
    def menu_actions(self, boo=None):
        if self.sender() is self.focusText:
            if boo:
                self.textedit.setFocus()
            else:
                self.textedit.clearFocus()
                self.setFocus()
        elif self.sender() is self.toggleLogWindow:
            if self.logwindow.height() < 300:
                self.logwindow.setGeometry(200, 200, 600, 400)
                self.logwindow.raiseW()
            else:
                self.logwindow.setGeometry(320, 710, 475, 55)
        elif self.sender() is self.toggleMiddleStack:
            m = self.middle_stack
            m.raiseWidget(
                m.widget(m.id(m.visibleWidget()) + 1) or 0)
        elif self.sender() is self.helpWindow:
            self.logwindow.setGeometry(200, 200, 600, 400)
            self.logwindow.raiseW()
            self.print_help()
    
    def print_help(self):
        self.logwindow.append("""Help for Larm
=============
Soon.
""")
            
            
    def show_param_echo(self, *things):
        self.status_paramlabel.setText("%s: %.2f" % things)
    
    
    def toggle_arduino_calibration(self):
        if not self.my_arduino.isShown():
            self.my_arduino.raiseW()
            self.my_arduino.show()
        else:
            self.my_arduino.hide()
            
    def turn_on_dsp(self, boo):
        if not self.starter.pdprocess.isRunning():
            if boo:
                self.sender().setOn(0)
                self.logwindow.show()
                self.logwindow.raiseW()
                self.starter.really_start_pd()
            return
        if boo:
            try:
                self.recording_inited
            except AttributeError:
                osc.sendMsg("/main/rick/ping", [1], self.osc_host, self.osc_port)
                self.recording_inited = 1
            osc.sendMsg("/pd/dsp", [1], self.osc_host, self.osc_port)
            self.saving.dspbutton.setText("____")
            self.saving.dspbutton.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg("/pd/dsp", [0], self.osc_host, self.osc_port)
            self.saving.dspbutton.setText("_/ _")
            self.saving.dspbutton.unsetPalette()
    
    def toggle_piano_mode(self, arg=None):
        if self.current_mode == 1 and arg is not 0:
            self.current_mode = 2
            self.canvas.canvas.setBackgroundColor(QColor(255, 150, 150))
        else:
            self.current_mode = 1
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
        min = self.timercount // 60
        sec = self.timercount % 60
        self.timer.setText('%02d:%02d' % (min, sec))
        
    def actionSnapshotRecall(self):
        ac = self.sender()
        [ma.recall_snapshot(ac.myindex) for ma in self.machines if ma.active]
                
    def actionSnapshotSave(self):
        ac = self.sender()
        [ma.save_snapshot(ac.myindex) for ma in self.machines if ma.active]
                
    def actionSeqPlay(self):
        ac = self.sender()
        i = ac.myindex
        [ma.seqparams[i].set_state(int(ma.seqparams[i].get_state() is 0) 
            ) for ma in self.machines if ma.active]
    
    def actionSeqRec(self):
        ac = self.sender()
        i = ac.myindex
        [ma.seqparams[i].set_state(int(ma.seqparams[i].get_state() is not 2) + 1
            ) for ma in self.machines if ma.active]

    def action_oscdebug(self, boo):
        if boo:
            osc.sendMsg("/pd/oscdebug", [1], self.osc_host, self.osc_port)
        else:
            osc.sendMsg("/pd/oscdebug", [0], self.osc_host, self.osc_port)
    
    def machine_activated(self):
        pass
        
    def machine_deactivated(self):
        pass
 
    def tgl_x_only(self, arg = None):
        self.status.message("Canvas X only", 1000)
        if arg is not None:
            [ma.set_x_only(arg) for ma in self.machines]
        else:
            [ma.set_x_only(ma.x_only) for ma in self.machines]
    
    def tgl_y_only(self, arg = None):
        self.status.message("Canvas Y only", 1000)
        if arg is not None:
            [ma.set_y_only(arg) for ma in self.machines]
        else:
            [ma.set_y_only(ma.y_only) for ma in self.machines]
            
    def tgl_finetune(self, arg):
        self.status.message("Canvas Finetune", 1000)
        if self.mouse_finetune[0] or arg == 0:
            self.mouse_finetune[0] = 0
        else:
            self.mouse_finetune[0] = 1
##
##    def deac_finetune(self):
##        self.mouse_finetune[0] = 0
        
    def action_machine_onoff(self):
        for ma in self.machines:
            if ma.active:
                ma.on_off()
    
    def action_show_numbers(self):
        if Machine.shownumbers:
            Machine.shownumbers = 0
            [ma.do_hide_numbers() for ma in Machine.activeMachines]
        else:
            Machine.shownumbers = 1
            [ma.do_show_numbers() for ma in Machine.activeMachines]
                
    
    def leaveEvent(self, e):
        self.active_modifiers.clear()
        QMainWindow.leaveEvent(self, e)
    
    def focusOutEvent(self, e):
        self.active_modifiers.clear()
        QMainWindow.focusOutEvent(self, e)
    
    #filter autorepeat, ignore modified keys (except shift) and pass on as pysignals
    def keyPressEvent(self, e):
        if e.isAutoRepeat() or self.textedit.hasFocus():
            e.ignore()
            return
        # Ctrl_L = 4129; Alt_L = 4131; Shift_L = 4128
        if e.key() in self.modifiers:
            self.active_modifiers.add(e.key())
        else:
            if not self.active_modifiers:
                if self.current_mode == 2:
                    try:
                        #FIXME: Create /main/keyboard param, without saving abs,
                       # and use
                       #that for sending 
                        osc.sendMsg("/main/keyboard", [self.piano_keys.index(e.key()), 1], 
                            self.host, self.port)
                    except ValueError:
                        pass
                else:
                    try:
                        self.stgl_keys["nomod"][self.key_mapping_list[e.key()]](1)
                    except (KeyError, IndexError):
                        pass
            
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt"][self.key_mapping_list[e.key()]](1)
                except (KeyError, IndexError):
                    pass
            

    def keyReleaseEvent(self, e):
        if e.isAutoRepeat() or self.textedit.hasFocus():
            e.ignore()
            return
        if e.key() in self.modifiers:
            self.active_modifiers.discard(e.key())
        else:
            if not self.active_modifiers:
                if self.current_mode == 2:
                    try:
                        #FIXME: Create /main/keyboard param, without saving abs,
                       # and use
                       #that for sending 
                        osc.sendMsg("/main/keyboard", [self.piano_keys.index(e.key()), 0], 
                            self.host, self.port)
                    except ValueError:
                        pass
                else:
                    try:
                        self.stgl_keys["nomod"][self.key_mapping_list[e.key()]](0)
                    except (KeyError, IndexError):
                        pass
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt"][self.key_mapping_list[e.key()]](0)
                except (KeyError, IndexError):
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
        try:
            self.inSocket = osc.createListener(getgl('osc_address'), getgl('osc_listen_port'))
        except:
            QMessageBox.critical(None, "Larm", "OSC address %s, port %d, is already in use.\nPerhaps another instance of Larm is already running. \nOtherwise change your settings." % (getgl('osc_address'), getgl('osc_listen_port')))
            sys.exit()
        
        self.pdcommand = ['nice', '-n0', 'pd', '-rt', '-nogui']
        self.pdcommand.append(getgl('pdcommand'))
        self.pdprocess = QProcess()
        self.pdloop = 0
        
        # Set up the GUI part
        self.gui=GuiThread(self)
        self.gui.show()
        
        qApp.connect(self.pdprocess, SIGNAL("readyReadStderr()"), self.read_stderr )
        qApp.connect(self.gui.restart_pd,
            SIGNAL("activated()"), self.restart_pd)
        qApp.connect(self.gui.start_pd,
            SIGNAL("activated()"), self.really_start_pd)
        qApp.connect(self.gui.stop_pd,
            SIGNAL("activated()"), self.stop_pd)
        qApp.connect(self.gui.pd_gui,
            SIGNAL("activated()"), self.change_pd_gui)
        qApp.connect(self.pdprocess, SIGNAL("processExited()"), 
            self.start_pd)
        
        self.osc_timer = QTimer()
        QObject.connect(self.osc_timer, SIGNAL("timeout()"), self.read_osc)
        self.osc_timer.start(2)
        
        qApp.splash.message("Starting event polling thread")
        self.thread1 = RealPollingThread(self.gui)
        self.thread1.start()
    
    def change_pd_gui(self):
        self.pdcommand = ['nice', '-n0', 'pd', '-rt']
        if not self.gui.pd_gui.isOn():
            self.pdcommand.append("-nogui")
        self.pdcommand.append(getgl('pdcommand'))
        
    def read_osc(self):
        osc.getOSC(self.inSocket)
        
    def read_stderr(self):
        while self.pdprocess.canReadLineStderr():
            self.gui.logwindow.append(self.pdprocess.readLineStderr())
    
    def stop_pd(self):
        if self.pdprocess.isRunning():
            self.pdprocess.tryTerminate()
            self.gui.logwindow.append("Stopping engine...")
            return True
        else:
            self.gui.logwindow.append("No engine to stop")
            return False
    
    def start_pd(self):
        if self.pdloop and not self.pdprocess.isRunning():
            self.pdprocess.setArguments(QStringList.fromStrList(self.pdcommand))
            self.gui.logwindow.append("Starting engine...")
            self.pdprocess.start()
            self.pdloop = 0
        elif self.pdprocess.isRunning():
            self.gui.logwindow.append("Engine already running")
        
    def really_start_pd(self):
        if not self.pdprocess.isRunning():
            self.pdprocess.setArguments(QStringList.fromStrList(self.pdcommand))
            self.gui.logwindow.append("Starting engine...")
            self.pdprocess.start()
            self.pdloop = 0
        else:
            self.gui.logwindow.append("Engine already running")
    
    def restart_pd(self):
        self.pdloop = 1
        self.stop_pd()
    
    def endApplication(self):
        self.gui.logwindow.show()
        self.gui.logwindow.raiseW()
        self.pdloop = 0
        if self.pdprocess.isRunning():
            self.stop_pd()
        #save notes text
        self.gui.logwindow.append("Saving notes file...")
        filename = str(self.gui.txtfilename)
        s=str(self.gui.textedit.text())

        f = open(filename, "w")
        f.write(s)
        if s[-1:] != "\n":
            f.write("\n")
        f.close()
        self.thread1.isrunning = 0
        self.gui.logwindow.append("Good-bye!")
        QTimer.singleShot(1000, qApp, SLOT("quit()"))
        
class MyDevice(evdev.Device):
    def __init__(self, filename):
        evdev.Device.__init__(self, filename)
    def resetRel(self):
        self.axes['REL_X'] = 0
        self.axes['REL_Y'] = 0
        
class RealPollingThread(QThread):
    
    def __init__(self, gui):
        QThread.__init__(self)
        self.gui = gui
        self.active = False
        self.activeMachines = set()
        QObject.connect(qApp, PYSIGNAL("addRemoveMachine"), 
            self.set_machine_active)
        try:
            self.d = MyDevice(getgl("mouse_device"))
        except OSError:
            QMessageBox.critical(None, "Larm", 
                "Couldn't find mouse. Please close Larm, check your settings and return. \n(Current set path:  %s)" % getgl("mouse_device"))
            exit()
        
    def set_canvas_active(self, boo):
        self.active = boo;
        if not boo:
            for k, v in self.d.buttons.items():
                self.d.buttons[k] = 0
    
    def set_machine_active(self, *args):
        if args[1]:
            self.activeMachines.add(args[0])
        else:
            self.activeMachines.discard(args[0])
    
    def run(self):
        self.isrunning = 1
        d = self.d
        d.axes['REL_X'], d.axes['REL_Y'] = 0, 0
        poll = d.poll
        resetRel = d.resetRel
        finetune = self.gui.mouse_finetune
        machines = self.activeMachines
        polltime = getgl('polltime')
        host = getgl('osc_address')
        port = getgl('osc_port')
        QObject.connect(self.gui.canvas, PYSIGNAL("canvasActive"), 
            self.set_canvas_active)
        while self.isrunning:
            QObject.emit(qApp, PYSIGNAL("oscPing"), ())
            resetRel()
            poll()
            mult = 8
            if finetune[0]:
                mult = 0.4
            if machines and self.active:
                d.axes['REL_X'] *= mult
                d.axes['REL_Y'] *= mult
                #iterate over copy
                #FIXME
                try:
                    [QObject.emit(m, PYSIGNAL("rawMouseEvents"), (d,)) for m in machines.copy()]
                except AttributeError, e:
                    print "Attribute Error in polling thread: %s" % e
            sleep(polltime)
        


if __name__ == "__main__":
    a = QApplication(sys.argv)
    font = QFont("DejaVu Sans", 7)
    a.setFont(font)
    try:
        import psyco
        psyco.profile()
    except ImportError:
        QMessageBox.information(None, "Larm", "Can't import psyco. Install it to make it go fast.")
    pix = QPixmap(sys.path[0]+"/splash.png")
    qApp.splash = QSplashScreen(pix)
    qApp.splash.show()
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    client = PollingThread()
    if "--print-osc" in sys.argv:
        client.gui.saving.root_param.printTree()
        sys.exit()
    a.setMainWidget(client.gui)
    qApp.splash.hide()
    a.exec_loop()
                

