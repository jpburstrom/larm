# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/johannes/python/sc/larm_utilities/fm.ui'
#
# Created: tis feb 27 00:32:07 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *

from jmachine import MiniMachine
from jrouting import Routing
from larmglobals import getgl
        
class MySlider(QSlider):
    def __init__(self,orientation, parent = None,name = None):
        QSlider.__init__(self,orientation,parent,name)
        self.name = name
    
    def valueChange(self):
        self.emit(PYSIGNAL("valueChanged"), (self.name, self.value()))

class MySpinBox(QSpinBox):
    def __init__(self, parent = None,name = None):
        QSpinBox.__init__(self,parent,name)
        self.name = name
        self.connect(self, SIGNAL("valueChanged(int)"), self.getvalue)
    
    def getvalue(self, i):
        self.emit(PYSIGNAL("valueChanged"), (self.name, i))

class MyRadioButton(QRadioButton):
    def __init__(self, parent = None,name = None):
        QRadioButton.__init__(self,parent,name)
        self.name = name
        self.connect(self, SIGNAL("stateChanged(int)"), self.getvalue)
    
    def getvalue(self, i):
        self.emit(PYSIGNAL("stateChanged"), (self.name, i))
    

class pm7(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("pm7")

        self.tabWidget = QTabWidget(self,"tabWidget")
        self.tabWidget.setGeometry(QRect(0,50,300,280))
        self.tabWidget.setTabPosition(QTabWidget.Bottom)
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        
        self.tab = QWidget(self.tabWidget,"tab")
        self.tabWidget.tabBar().setPaletteForegroundColor(QColor(0,0,0))
        self.tabWidget.insertTab(self.tab,QString.fromLatin1("3"))
        self.tab_2 = QWidget(self.tabWidget,"tab_2")
        self.tabWidget.insertTab(self.tab_2,QString.fromLatin1(""))
        for boj in self.tabWidget.children():
            boj.setPaletteBackgroundColor(QColor(50,50,50))
        

        #  Sliders
        self.controls = []
        self.slider_labels = ["/speed", "/speeddev", "/len", "/lendev", "/amp", "/ampdev"] #osc labels
        for i in range(6):
            slider = MySlider(QSlider.Horizontal, self.tab, self.slider_labels[i])
            slider.setGeometry(QRect(10,(i * 20)+85,200,24))
            slider.setMinValue(1)
            slider.setMaxValue(1000)
            self.controls.append(slider)
            self.connect(slider, PYSIGNAL("valueChanged"), self.get_data)
        self.slider_labels = set(self.slider_labels)

            
        #Slider labels
        self.labels = []
        texts = ['Speed', 'Speed dev', 'Length', 'Length dev', 'Amp', 'Amp dev']
        for r in range(6):
            k = (r * 20) + 88
            textLabel = QLabel(self.tab, texts[r])
            textLabel.setGeometry(QRect(213,k,63,16))
            textLabel.setText(texts[r])
            self.labels.append(textLabel)
        
        #Octave
        self.octHi = MySpinBox(self.tab,"/octHi")
        self.octHi.setGeometry(QRect(169,204,32,18))
        self.octHi.setMaxValue(9)

        self.octLo = MySpinBox(self.tab,"/octLo")
        self.octLo.setGeometry(QRect(73,204,32,18))
        self.octLo.setMaxValue(9)
        
        self.connect(self.octLo, PYSIGNAL("valueChanged"), self.get_data)
        self.connect(self.octHi, PYSIGNAL("valueChanged"), self.get_data)

        self.octLoLabel = QLabel(self.tab,"octLoLabel")
        self.octLoLabel.setGeometry(QRect(19,208,55,16))

        self.octHiLabel = QLabel(self.tab,"octHiLabel")
        self.octHiLabel.setGeometry(QRect(114,208,55,16))
        
        #start wave chooser
        self.wave = QButtonGroup(self.tab,"wave")
        self.wave.setGeometry(QRect(141,9,84,78))
        self.wave.setFrameShape(QButtonGroup.NoFrame)
        ##
        self.wave1 = QButtonGroup(self.wave,"/wave1")
        self.wave1.setGeometry(QRect(5,15,43,57))
        self.wave1.setFrameShape(QButtonGroup.NoFrame)
        self.wave1.setFrameShadow(QButtonGroup.Plain)
        self.wave1.setExclusive(1)
        self.sin = QRadioButton(self.wave1,"sin_1")
        self.sin.setGeometry(QRect(2,-1,38,16))
        self.sin.setPaletteForegroundColor(QColor(85,255,0))
        self.sin.setFocusPolicy(QRadioButton.NoFocus)
        self.tri = QRadioButton(self.wave1,"tri_1")
        self.tri.setGeometry(QRect(2,13,43,16))
        self.tri.setPaletteForegroundColor(QColor(85,255,0))
        self.tri.setFocusPolicy(QRadioButton.NoFocus)
        self.saw = QRadioButton(self.wave1,"saw_1")
        self.saw.setGeometry(QRect(2,27,43,16))
        self.saw.setPaletteForegroundColor(QColor(85,255,0))
        self.saw.setFocusPolicy(QRadioButton.NoFocus)
        self.squ = QRadioButton(self.wave1,"squ_1")
        self.squ.setGeometry(QRect(2,41,45,16))
        self.squ.setPaletteForegroundColor(QColor(85,255,0))
        self.squ.setFocusPolicy(QRadioButton.NoFocus)

        self.wave2 = QButtonGroup(self.wave,"/wave2")
        self.wave2.setGeometry(QRect(48,13,16,60))
        self.wave2.setFrameShape(QButtonGroup.NoFrame)
        self.wave2.setFrameShadow(QButtonGroup.Plain)
        self.wave2.setExclusive(1)
        self.squ_2 = QRadioButton(self.wave2,"squ_2")
        self.squ_2.setGeometry(QRect(2,44,16,16))
        self.squ_2.setPaletteForegroundColor(QColor(85,255,0))
        self.squ_2.setFocusPolicy(QRadioButton.NoFocus)
        self.sin_2 = QRadioButton(self.wave2,"sin_2")
        self.sin_2.setGeometry(QRect(2,0,16,16))
        self.sin_2.setPaletteForegroundColor(QColor(85,255,0))
        self.sin_2.setFocusPolicy(QRadioButton.NoFocus)
        self.tri_2 = QRadioButton(self.wave2,"tri_2")
        self.tri_2.setGeometry(QRect(2,14,16,16))
        self.tri_2.setPaletteForegroundColor(QColor(85,255,0))
        self.tri_2.setFocusPolicy(QRadioButton.NoFocus)
        self.saw_2 = QRadioButton(self.wave2,"saw_2")
        self.saw_2.setGeometry(QRect(2,29,16,16))
        self.saw_2.setPaletteForegroundColor(QColor(85,255,0))
        self.saw_2.setFocusPolicy(QRadioButton.NoFocus)

        self.wave3 = QButtonGroup(self.wave,"/wave3")
        self.wave3.setGeometry(QRect(67,12,16,61))
        self.wave3.setFrameShape(QButtonGroup.NoFrame)
        self.wave3.setFrameShadow(QButtonGroup.Plain)
        self.wave3.setExclusive(1)
        self.tri_3 = QRadioButton(self.wave3,"tri_3")
        self.tri_3.setGeometry(QRect(0,45,16,16))
        self.tri_3.setPaletteForegroundColor(QColor(85,255,0))
        self.tri_3.setFocusPolicy(QRadioButton.NoFocus)
        self.saw_3 = QRadioButton(self.wave3,"saw_3")
        self.saw_3.setGeometry(QRect(0,30,16,16))
        self.saw_3.setPaletteForegroundColor(QColor(85,255,0))
        self.saw_3.setFocusPolicy(QRadioButton.NoFocus)
        self.sin_3 = QRadioButton(self.wave3,"sin_3")
        self.sin_3.setGeometry(QRect(0,1,16,16))
        self.sin_3.setPaletteForegroundColor(QColor(85,255,0))
        self.sin_3.setFocusPolicy(QRadioButton.NoFocus)
        self.squ_3 = QRadioButton(self.wave3,"squ_3")
        self.squ_3.setGeometry(QRect(0,15,16,16))
        self.squ_3.setPaletteForegroundColor(QColor(85,255,0))
        self.squ_3.setFocusPolicy(QRadioButton.NoFocus)
        
        self.connect(self.wave1, SIGNAL("pressed(int)"), self.wave1_sel)
        self.connect(self.wave2, SIGNAL("pressed(int)"), self.wave2_sel)
        self.connect(self.wave3, SIGNAL("pressed(int)"), self.wave3_sel)
        
        #Start keyboard
        self.keyboardHi = self.generate_keyboard("/keyboardHi", 16, 8)
        self.keyboardLo = self.generate_keyboard("/keyboardLo", 16, 48)
        
        self.saving = MiniMachine("pm7",self,"pm7save")
        self.saving.setGeometry(QRect(0,0,300,50))

        
        self.routing = Routing(11, 3, True, self.tab_2)
        self.routing.set_column_width(80)
        self.routing_labels = ["op1", "op2", "op3", "relfq", "D", "A", "D", "S", "R", "vol", "pan"]
        #this is stupid.
        self.routing_labels2 = ["op1", "op2", "op3", "relfq", "delay", "attack", "decay", "sustain", "release", "vol", "pan"]
        self.routing_osc_labels = ["/op%d/op1", "/op%d/op2", "/op%d/op3", "/op%d/relfreq", 
            "/op%d/delay", "/op%d/attack", "/op%d/decay", "/op%d/sustain", 
            "/op%d/release", "/op%d/vol", "/op%d/pan"]
        self.routing.set_row_labels(QStringList.fromStrList(self.routing_labels))
        self.routing.setGeometry(2, 2, 305, 600)
        
        self.connect(self.routing, PYSIGNAL("output"), self.get_routing_data)
        self.connect(self.saving, PYSIGNAL("preset_loaded"), self.update_controls)
        self.connect(self.saving, PYSIGNAL("snapshot_loaded"), self.update_controls)

        self.languageChange()
        
        self.clearWState(Qt.WState_Polished)
        
        self.saving.init_controls()
    
    def wave1_sel(self, int):
        self.saving.store_and_send("/op1/wave", int)
    def wave2_sel(self, int):
        self.saving.store_and_send("/op2/wave", int)
    def wave3_sel(self, int):
        self.saving.store_and_send("/op3/wave", int)
        
    def toggle_page(self):
        if self.tabWidget.currentPage() is self.tab:
            self.tabWidget.showPage(self.tab_2)
        else:
            self.tabWidget.showPage(self.tab)

    def get_data(self, label, data):
        self.saving.store_and_send(label, data)
        #self.saving.state[label] = data
    
    def get_routing_data(self, data):
        self.saving.store_and_send(self.routing_osc_labels[data[0][0]] % (data[0][1] + 1), data[1])
        
    def update_controls(self, preset = None):
        #Todo: check this one... there may be some kind of bug, but hopefully
        #just related to the messy save file...
        for k, v in self.saving.state.items():
            if k.startswith("/op"):
                o = k.split("/")
                if o[2] == "wave":
                    self.wave.child("/wave"+o[1][-1]).setButton(v)
                else:
                    self.routing.setvalue(self.routing_labels2.index(o[2]), self.routing_labels.index(o[1]), v)
            elif k in self.slider_labels or k.startswith("/oct"):
                self.child(k).setValue(v)
            else:
                try:
                    if v == 2:
                        self.tab.child(k).setState(QButton.On)
                    elif v == 0: 
                        self.tab.child(k).setState(QButton.Off)
                except AttributeError: pass
                    #print "AttributeError:" , k, v

    def generate_keyboard(self, label, x, y):
        buttons = []
        pos = [(0, 14), (8, 0), (16, 14), (24, 0), (32, 14), (48, 14), 
            (56, 0), (64, 14), (72, 0), (80, 14), (88, 0), (96, 14)]
        for r in range (12):
            button = MyRadioButton(self.tab,label+str(r))
            button.setPaletteForegroundColor(QColor(255,0,255))
            button.setFocusPolicy(QRadioButton.NoFocus)
            button.setGeometry(pos[r][0] + x, pos[r][1] + y, 16, 16)
            self.connect(button, PYSIGNAL("stateChanged"), self.get_data)
            buttons.append(button)
        return buttons

    def languageChange(self):
        self.setCaption(self.__tr("pm7"))
        self.setIconText(QString.null)
        self.octLoLabel.setText(self.__tr("Oct min"))
        self.octHiLabel.setText(self.__tr("Oct max"))
        self.wave.setTitle(self.__tr("wave"))
        self.wave1.setTitle(QString.null)
        self.sin.setText(self.__tr("sin"))
        self.tri.setText(self.__tr("tri"))
        self.saw.setText(self.__tr("saw"))
        self.squ.setText(self.__tr("squ"))
        self.tabWidget.changeTab(self.tab,self.__tr("1"))
        self.tabWidget.changeTab(self.tab_2,self.__tr("2"))
    
    def activate(self):
        self.saving.activate()
    def deactivate(self):
        self.saving.deactivate()
    def on_off(self, arg = None):
        self.saving.on_off(arg)
    def tgl_active(self):
        self.saving.tgl_active()
        
    def __tr(self,s,c = None):
        return qApp.translate("pm7",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = pm7()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
