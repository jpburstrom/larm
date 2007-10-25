#!/usr/bin/env python
#TODO: Perhaps move all osc sending functions to param or similar


import  os
import sys
from qt import *

from copy import copy
from time import sleep
from Queue import Queue

#import osc
import evdev

from larm_utilities import *


class MouseLooper(Machine):
    """GUI for the looping machine. """
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label, canvas, parent, canvaslabel,name,fl)
                
        self.buffer_param = Param(type=str, address="/buffer")
        self.buffer_param.set_saveable(0)
        self.root_param.insertChild(self.buffer_param)

        
        self.smplabel = ParamLabel(self.buffer_param, self)
        self.smplabel.setAlignment(QLabel.AlignRight)
        self.sample_loaded = None
        self.sample_path = None
        
        self.chkbox = QCheckBox(self.tek, "savesample")
        self.chkbox.setGeometry(0, 0, 12,12)
        self.connect(self.chkbox, SIGNAL("toggled(bool)"), self.set_chkbox_color)
        QToolTip.add(self.chkbox, "Save with sample")
        self.connect(self.chkbox, SIGNAL("toggled(bool)"), 
            self.set_sample_save)
        
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
    
    def load_sample(self, sample, path, dest):
        self.sample_path = path
        if dest == self.label and self.sample_loaded != sample:
            self.buffer_param.set_state(path)
            self.sample_loaded = path
    
    def set_chkbox_color(self, boo):
        if boo:
            self.chkbox.setPaletteBackgroundColor(Qt.green)
        else:
            self.chkbox.setPaletteBackgroundColor(Qt.white)
        

    def set_sample_save(self, boo):
        self.buffer_param.set_saveable(boo)
    
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
    """Just a slider with a label beside it."""
    def __init__(self, param, label, parent = None, name = None,fl = 0):
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
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        
        self.sliderbox = QVBox(self)
        self.controls = []
        self.params = []
        self.slider_labels = ["/voldev", "/pandev", "/window"] #osc labels
        for i in range(3):
            self.params.append(Param(type=int, address=self.slider_labels[i], max=100, min=0))
            self.root_param.insertChild(self.params[i])
            slider = LabelSlider(self.params[i], self.slider_labels[i], 
                self.sliderbox, self.slider_labels[i])
            self.controls.append(slider)
        self.params[2].set_max_value(9)
        self.controls[2].slider.setPageStep(1)

        self.windows = []
        for n in range(10):
            qp = QPixmap(QString((sys.path[0]+"/larm_utilities/wave%d.png") % (n + 1)))
            if not qp.isNull():
                self.windows.append(qp)
            else:
                raise IOError("Can't open image. What's wrong with you?")
        self.connect(self.controls[2].slider, SIGNAL("valueChanged(int)"), self.on_window_change)
        self.controls[2].label.setPixmap(self.windows[0])
        
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self)
        self.mastertempo_sl.setTickInterval(4)
        self.root_param.insertChild(self.mastertempo)
        
        self.freezebtn_param = Param(type=bool, address="/freeze")
        self.root_param.insertChild(self.freezebtn_param)
        self.freezebtn = ParamPushButton(self.freezebtn_param, self)
        self.freezebtn.setText("Freeze")
        self.freezebtn.setMaximumHeight(16)
        self.freezebtn.setFlat(1)
        self.connect(self.freezebtn, SIGNAL("toggled(bool)"), self.on_freeze)
        
        self.connect(self, PYSIGNAL("snapshot_loaded"), self.update_controls)
    
    def on_freeze(self, boo):
        if boo:
            self.freezebtn.setPaletteForegroundColor(QColor(255,0,0))
        else:
            self.freezebtn.setPaletteForegroundColor(QColor(0,0,0))
            
    def on_window_change(self, v):
        self.controls[2].label.setPixmap(self.windows[v])
    
    def update_controls(self, preset = None):
        if self.freezebtn_param.get_state():
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
    """GUI for the delay"""
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self)
        self.mastertempo_sl.setTickInterval(4)
        self.root_param.insertChild(self.mastertempo)
    
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
    """GUI for the room/reverb"""
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
    
    def generate_label_tuple(self):
        self.label_tuple = (self.label, [
        ['Liveness', 'Distance'],
        ['Slope', 'Xfreq'],
        ['Distortion', 'Volume'],
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
    def __init__(self,label,canvas, parent = None, canvaslabel = None, name = None,fl = 0):
        Machine.__init__(self,label,canvas, parent, canvaslabel,name,fl)
        
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
    """The Main machine takes care of saving and loading global presets"""
    
    def __init__(self, *args):
        MiniMachine.__init__(self, *args)
        
        
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
            self.samplelist.addsample(".:recordings", self.arrays[add[2]])
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
            setmax = Param(address="/set_max", type=Bang)
            self.rescaleparams[i].insertChild(setmax)
            maxbutton = ParamPushButton(setmax, box)
            maxbutton.setText("Set Max")
            setmin = Param(address="/set_min", type=Bang)
            self.rescaleparams[i].insertChild(setmin)
            minbutton = ParamPushButton(setmin, box)
            minbutton.setText("Set Min")
            max = Param(address="/max", type=float)
            min = Param(address="/min", type=float)
            self.rescaleparams[i].insertChild(min)
            self.rescaleparams[i].insertChild(max)
            
            lab2 = ParamLabel(gloveparams[i], box)
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

class MyRouting(Routing):
    """The Routing UI.
    A Grid of sliders, without connecting machines to itself."""
    def __init__(self, row, col, routeToSelf = True, parent = None,name = None,fl = 0):
        Routing.__init__(self, row, col, routeToSelf = True, parent = parent,name = name,fl = 0)
        
        self.osc_labels = ["/a4loop-1", "/a4loop-2", "/a4loop-3", "/a4loop-4", 
            "/grandel-1", "/delay-1", "/combo-1", "/pm7", 
            "/adc12", "/adc3"]
        
        self.saving = MiniMachine("routing",self,"routingsave")
        
        i = 0
        for p_param in self.params:
            self.saving.root_param.insertChild(p_param)
            p_param.set_address(self.osc_labels[i])
            j = 0
            for param in p_param.children():
                param.set_address("".join(["/send" + str(j)]))
                param.type=float
                param.max=1000
                param.min = 0
                param.set_state(0)
                j += 1
            i += 1
            
        self.saving.setGeometry(QRect(0,0,314,48))
        self.table1.move(QPoint(0, 50))
        
        
        labels = ["Loop 1", "Loop 2", "Loop 3", "Loop 4", 
            "Grandel", "Delay", "Combo", "pm7", "adc12", "adc3"]
        self.set_row_labels(QStringList.fromStrList(labels))
        labels = ["Room", "Grandel", "Delay", "Combo", "dac3"]
        self.set_col_labels(QStringList.fromStrList(labels))
        
        #This removes the slider which connects machines to itself
        for cl in range(1, 4):
            self.clear_cell(cl+3, cl)

class MyMenu(QPopupMenu):
    """The beautiful menu button"""
    def __init__(self, parent, name):
        QPopupMenu.__init__(self, parent, name)
        
        self.parent().dspAction = QAction(self.parent(), "dspAction")
        self.parent().dspAction.setToggleAction(1)
        self.parent().dspAction.setText("DSP")
        self.parent().dspAction.addTo(self)
        self.insertSeparator()
        self.parent().recPathAction = QAction("Set rec path", 
            QKeySequence("F12"), self.parent(), "recPathAction")
        self.parent().recPathAction.addTo(self)
        self.parent().startTimerAction = QAction("Start timer",
            QKeySequence("F11"), self.parent(), "startTimerAction")
        self.parent().startTimerAction.addTo(self)
        
        self.parent().focusText = QAction("Edit text",
            QKeySequence("F10"), self.parent(), "focusText")
        self.parent().focusText.addTo(self)
        self.parent().focusText.setToggleAction(1)
        self.parent().toggleParamRouting = QAction("Param Routing",
            QKeySequence("F9"), self.parent(), "toggleParamRouting")
        self.parent().toggleParamRouting.addTo(self)
        self.parent().toggleLogWindow = QAction("Log Window",
            QKeySequence("F8"), self.parent(), "toggleLogWindow")
        self.parent().toggleLogWindow.addTo(self)
        self.parent().toggleArduinoCalib = QAction("Arduino Calibration", QKeySequence("F7"), self.parent(), "toggleArduinoCalib")
        self.parent().toggleArduinoCalib.addTo(self)
        self.parent().restart_pd = QAction(self.parent(), "restart_pd")
        self.parent().restart_pd.setText("Restart PD")
        self.parent().restart_pd.addTo(self)
        self.parent().start_pd = QAction(self.parent(), "start_pd")
        self.parent().start_pd.setText("Start PD")
        self.parent().start_pd.addTo(self)
        self.parent().stop_pd = QAction(self.parent(), "stop_pd")
        self.parent().stop_pd.setText("Stop PD")
        self.parent().stop_pd.addTo(self)
        self.parent().sendctrl = QAction(self.parent(), "sendctrl")
        self.parent().sendctrl.setText("Send all controls")
        self.parent().sendctrl.addTo(self)
        self.parent().oscdebug = QAction(self.parent(), "oscdebug")
        self.parent().oscdebug.setText("Debug OSC")
        self.parent().oscdebug.setToggleAction(1)
        self.parent().oscdebug.addTo(self)

        self.parent().quitAction = QAction(self, "quitAction")
        self.parent().quitAction.setText("Quit")
        self.parent().quitAction.addTo(self)
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

    def __init__(self, endcommand, *args):
        QMainWindow.__init__(self, *args)
        
        self.setCaption("LARM")
        
        qApp.mainwindow = self
        
        self.actions = {}
        #This is a list, so the background thread can keep a reference
        #to it...
        self.mouse_finetune = [0]
        
        self.setFixedSize(1024, 768)
        self.setPaletteBackgroundColor(QColor(10, 10, 10))
        self.setPaletteForegroundColor(QColor('gold'))
        
        #THA MENU
        self.menubutton = QPushButton(self, "Menu")
        self.menubutton.setPaletteForegroundColor(QColor('gold'))
        self.menubutton.setGeometry(2,2,40, 20)
        self.menubutton.setText("_/ _")
        self.menubutton.setPaletteBackgroundColor(QColor(50,50,50))
        self.larmmenu = MyMenu(self, "larmmenu")
        self.larmmenu.setGeometry(0, 30, 200, 200)
        self.connect(self.menubutton, SIGNAL("clicked()"), self.larmmenu, SLOT("show()"))
      
        #THA RECORDER
        self.recording = RecordToDisk(self)
        self.recording.setGeometry(50, 0, 200, 24)
        
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
##CANVAS
######################################################

        self.canvascon = QVBox(self)
        self.canvascon.setGeometry(345, 5, 305, 470)
        self.canvaslabels = Canvasinfo(self.canvascon)
        self.canvaslabels.setFixedSize(300, 148)
        self.canvas = MarioDots(self.canvascon, "Hej hej")
        self.canvas.setFixedHeight(302)
        
        #this should be before samplers(?)
        self.urack = QVBox(self)
        self.urack.setGeometry(800, 5, 200, 674)
        self.samplelist = SampleList(self.urack, "Samplelist")
        
######################################################
##MACHINES
######################################################    

        
        self.machines = [] #list of machine objects

        self.param_routing = ParamRouting(self)
        self.param_routing.setGeometry(670, 5, 110, 50)
        #self.param_routing.show()
##        self.param_routing.tpr = QAction(self.param_routing, "toggleParamRouting")
##        self.param_routing.tpr.setAccel(QKeySequence("F9"))
##        self.param_routing.tpr.setToggleAction(0)
        
        self.machines.append(self.param_routing.saving)
        
        self.urack2 = QVBox(self.urack)
        self.urack2.setSpacing(2)
        self.mlp1 = MouseLooper("MouseLooper1", self.canvas, 
            self.urack2, self.canvaslabels )
        self.mlp2 = MouseLooper("MouseLooper2", self.canvas, 
            self.urack2, self.canvaslabels )
        self.mlp3 = MouseLooper("MouseLooper3", self.canvas, 
            self.urack2, self.canvaslabels )
        self.mlp4 = MouseLooper("MouseLooper4", self.canvas, 
            self.urack2, self.canvaslabels )
        
        for m in (self.mlp1, self.mlp2, self.mlp3, self.mlp4):
            self.machines.append(m)
            m.root_param.set_save_address("/mouselooper")
            
        self.narrowbox = QVBox(self)
        self.narrowbox.setGeometry(650, 55, 140, 670)
        self.narrowbox.setSpacing(4)

        self.saving = MainMachine("Main", self.narrowbox, "mainsave")
        #self.saving.setFixedHeight(150)
        
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
        
        self.logwindow = QTextEdit(self)
        self.logwindow.setTextFormat(Qt.LogText)
        self.logwindow.setPaletteBackgroundColor(QColor(50,50,50))
        self.logwindow.setPaletteForegroundColor(QColor("orange"))
        self.logwindow.setHScrollBarMode(QScrollView.AlwaysOff)
        self.logwindow.setVScrollBarMode(QScrollView.AlwaysOff)
        self.logwindow.setFocusPolicy(QWidget.NoFocus)
        self.logwindow.setGeometry(200, 200, 600, 400)
        self.logwindow.hide()
#        self.logfile = QFile("/tmp/pdlog")
#        if (self.logfile.open(IO_ReadOnly)):
#            self.stream = QTextStream(txtfile)  
#        self.logwindow.append(self.stream.read())

        self.rec = ArrayRecorder(self.samplelist, self.narrowbox)
        self.rec.setFixedHeight(300)

        self.routing = MyRouting(10, 5, True, self)
        self.routing.setGeometry(330, 475, 315, 250)
        self.machines.append(self.routing.saving)

        self.rack1 = QVBox(self)
        self.rack1.setGeometry(20, 30, 300, 716)
        self.rack1.setSpacing(2)
        self.pm7 =  pm7(self.rack1, "pm7")
        self.machines.append(self.pm7.saving)
        
        self.grandel = Grandel("Grandel", self.canvas, self.rack1, self.canvaslabels)
        self.machines.append(self.grandel)
        
        self.delay = Delay("Delay", self.canvas, self.rack1, self.canvaslabels)
        self.machines.append(self.delay)
        
        self.combo = Combo("Combo", self.canvas, self.rack1, self.canvaslabels)
        self.machines.append(self.combo)

        self.room = Room("Room", self.canvas, self.rack1, self.canvaslabels)
        self.machines.append(self.room)
        
        self.my_arduino = MyArduino(self)
        self.my_arduino.setGeometry(200,200,300,300)
        self.saving.root_param.insertChild(self.my_arduino.root_param)
        self.my_arduino.hide()
        self.my_arduino.init_controls()
        
        ##Hook up all machines to base
        for ma in self.machines:
            self.saving.root_param.insertChild(ma.root_param)
            if ma is not self.param_routing.saving:
                ma.init_controls()
        self.saving.init_controls()
        self.param_routing.init_controls(self.saving.root_param)
        
######################################################
##EPILOGUE
######################################################
  
        self.setFocusPolicy(QWidget.StrongFocus)
        self.setFocus()
        
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
        
        self.connect(self.dspAction, SIGNAL("toggled(bool)"), self.turn_on_dsp)
        self.connect(self.recPathAction, 
            SIGNAL("activated()"), self.recording.choose_recpath)
        self.connect(self.startTimerAction, 
            SIGNAL("activated()"), self.action_start_timer)
        self.connect(self.timertimer, 
            SIGNAL("timeout()"), self.action_count_timer)
        self.connect(self.quitAction, SIGNAL("activated()"), self.endcommand)
        self.connect(self.focusText, SIGNAL("toggled(bool)"), 
            self.toggle_textedit_focus)
        self.connect(self.toggleParamRouting, SIGNAL("activated()"), 
            self.param_routing.toggle_show)
        self.connect(self.toggleLogWindow, SIGNAL("activated()"), 
            self.toggle_log_window)
        self.connect(self.toggleArduinoCalib, SIGNAL("activated()"),
            self.toggle_arduino_calibration)
##        self.connect(self.param_routing.tpr, SIGNAL("activated()"), 
##            self.param_routing.toggle_show)
        self.connect(self.sendctrl, SIGNAL("activated()"), self.action_sendctrl)
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
        
        #just a silly mapping game
        self.key_mapping_list = [None for i in range(0, 91)] #->z
        for i in "abcdefghijklmnopqrstuvwxyz":
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
        
        self.actions["snapshot_save"] = []
        self.actions["snapshot_recall"] = []
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
        
    def deactivate_all(self):
        for ma in self.machines:
            ma.deactivate()
            self.set_piano_mode(0)
    def stop_all(self):
        for ma in self.machines:
            ma.on_off(0)
    
    def toggle_textedit_focus(self, boo):
        if boo:
            self.textedit.setFocus()
        else:
            self.textedit.clearFocus()
            self.setFocus()
            
    def show_param_echo(self, *things):
        self.status_paramlabel.setText("%s: %.2f" % things)
    
    def toggle_log_window(self):
        if not self.logwindow.isShown():
            self.logwindow.raiseW()
            self.logwindow.show()
        else:
            self.logwindow.hide()
    
    def toggle_arduino_calibration(self):
        if not self.my_arduino.isShown():
            self.my_arduino.raiseW()
            self.my_arduino.show()
        else:
            self.my_arduino.hide()
            
    def turn_on_dsp(self, boo):
        try:
            self.recording_inited
        except AttributeError:
            osc.sendMsg("/main/rick/ping", [1], self.osc_host, self.osc_port)
            self.recording_inited = 1
        if boo:
            osc.sendMsg("/pd/dsp", [1], self.osc_host, self.osc_port)
            self.menubutton.setText("____")
            self.menubutton.setPaletteBackgroundColor(QColor("red"))
        else:
            osc.sendMsg("/pd/dsp", [0], self.osc_host, self.osc_port)
            self.menubutton.setText("_/ _")
            self.menubutton.setPaletteBackgroundColor(QColor(50,50,50))
    
    def set_piano_mode(self, boo):
        self.current_mode = int(boo) + 1 
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

    def action_sendctrl(self):
        for p in self.saving.root_param.queryList("Param"):
            p._send_to_osc()

    def action_oscdebug(self, boo):
        if boo:
            osc.sendMsg("/pd/oscdebug", [1], self.osc_host, self.osc_port)
        else:
            osc.sendMsg("/pd/oscdebug", [0], self.osc_host, self.osc_port)
    
    def tgl_x_only(self, arg = None):
        if arg is not None:
            [ma.set_x_only(arg) for ma in self.machines]
        else:
            [ma.set_x_only(ma.y_only) for ma in self.machines]
    
    def tgl_y_only(self, arg = None):
        if arg is not None:
            [ma.set_x_only(arg) for ma in self.machines]
        else:
            [ma.set_x_only(ma.y_only) for ma in self.machines]
            
    def tgl_finetune(self, arg):
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
            for ma in Machine.activeMachines:
                ma.do_hide_numbers()
        else:
            Machine.shownumbers = 1
            for ma in Machine.activeMachines:
                ma.do_show_numbers()
    
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
                    except KeyError:
                        pass
                    except IndexError:
                        pass
            
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt"][self.key_mapping_list[e.key()]](1)
                except KeyError:
                    pass
                except IndexError:
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
                    except KeyError:
                        pass
                    except IndexError:
                        pass
            elif self.active_modifiers == set([Qt.Key_Alt]):
                try:
                    self.stgl_keys["Alt"][self.key_mapping_list[e.key()]](0)
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
        self.inSocket = osc.createListener(getgl('osc_address'), getgl('osc_listen_port'))
        command = ['nice', '-n0']
        command.extend(getgl('pdcommand').split())
        self.pdprocess = QProcess(QStringList.fromStrList(command))
        self.pdprocess.start()
        self.pd_running = 1
        self.pdloop = 0
        
        # Set up the GUI part
        self.gui=GuiThread(self.endApplication)
        self.gui.show()
        
        qApp.connect(self.pdprocess, SIGNAL("readyReadStderr()"), self.read_stderr )
        qApp.connect(self.gui.restart_pd,
            SIGNAL("activated()"), self.restart_pd)
        qApp.connect(self.gui.start_pd,
            SIGNAL("activated()"), self.really_start_pd)
        qApp.connect(self.gui.stop_pd,
            SIGNAL("activated()"), self.stop_pd)
        qApp.connect(self.pdprocess, SIGNAL("processExited()"), 
            self.start_pd)
        
        self.osc_timer = QTimer()
        QObject.connect(self.osc_timer, SIGNAL("timeout()"), self.read_osc)
        self.osc_timer.start(2)
        self.running = 1

        self.thread1 = RealPollingThread(self.gui)
        self.thread1.start()

    def read_osc(self):
        osc.getOSC(self.inSocket)
        
    def read_stderr(self):
        while self.pdprocess.canReadLineStderr():
            self.gui.logwindow.append(self.pdprocess.readLineStderr())
    
    def stop_pd(self):
        if self.pd_running:
            self.pd_running = 0
            self.pdprocess.tryTerminate()
            self.gui.logwindow.append("Stopping engine...")
        #QTimer.singleShot( 500, self.pdprocess, SLOT("kill()") )
        else:
            self.gui.logwindow.append("No engine to stop")
    
    def start_pd(self):
        if self.pdloop and not self.pd_running:
            self.gui.logwindow.append("Starting engine...")
            self.pdprocess.start()
            self.pdloop = 0
            self.pd_running = 1
        elif self.pd_running:
            self.gui.logwindow.append("Engine already running")
        
    def really_start_pd(self):
        if not self.pd_running:
            self.gui.logwindow.append("Starting engine...")
            self.pdprocess.start()
            self.pdloop = 0
            self.pd_running = 1
        else:
            self.gui.logwindow.append("Engine already running")
    
    def restart_pd(self):
        self.pdloop = 1
        self.stop_pd()
    
    def endApplication(self):
        self.pdloop = 0
        self.stop_pd()
        #save notes text
        if isinstance(self.gui.txtfilename, QString):
            self.gui.txtfilename = str(self.gui.txtfilename)

        s=str(self.gui.textedit.text())

        f = open(self.gui.txtfilename, "w")
        f.write(s)
        if s[-1:] != "\n":
            f.write("\n")
        f.flush()
        self.running = 0
        del self.inSocket
        self.thread1.isrunning = 0
        self.stop_pd()
        sleep(0.1)
        qApp.quit()
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
        self.d = MyDevice(getgl("mouse_device"))
        
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
            if machines and self.active:
                if finetune[0]:
                    d.axes['REL_X'] /= 20.0
                    d.axes['REL_Y'] /= 20.0
                [QObject.emit(m, PYSIGNAL("rawMouseEvents"), (d,)) for m in machines]
            sleep(polltime)
        

try:
    import psyco
    psyco.bind(PollingThread)
    psyco.bind(Machine.handle_mouse)
    psyco.bind(Machine.update_canvas)
except ImportError:
    "Can't import psyco. What do we do?"

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    client = PollingThread()
    a.setMainWidget(client.gui)
    a.exec_loop()
                

