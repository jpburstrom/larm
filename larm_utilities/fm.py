# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"


# Form implementation generated from reading ui file '/home/johannes/python/sc/larm_utilities/fm.ui'
#
# Created: tis feb 27 00:32:07 2007
#      by: The PyQt User Interface Compiler (pyuic) 3.16
#
# WARNING! All changes made in this file will be lost!


import sys
from qt import *

from jmachine import *
from jrouting import Routing
from larmglobals import getgl

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

class FMMiniMachine(MiniMachine):
    def __init__(self, *args):
        MiniMachine.__init__(self, *args)
    
    def tgl_active(self, arg = None):
        MiniMachine.tgl_active(self, arg)
        #stupid?

class pm7(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)
        
        self.setFixedHeight(320)

        if not name:
            self.setName("pm7")
               
        self.saving = FMMiniMachine("pm7",self,"pm7save")
        self.saving.setGeometry(QRect(0,0,300,50))

        self.tabWidget = QTabWidget(self,"tabWidget")
        self.tabWidget.setGeometry(QRect(0,50,300,270))
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
        self.params = []
        self.slider_labels = ["/speed", "/speeddev", "/len", "/lendev", "/amp", "/ampdev"] #osc labels
        for i in range(6):
            self.params.append(Param(type=int,address=self.slider_labels[i],
                min=0, max=1000))
            slider = ParamSlider(self.params[i], QSlider.Horizontal, self.tab, self.slider_labels[i])
            slider.setGeometry(QRect(10,(i * 20)+85,200,24))
            self.controls.append(slider)
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
        self.octHi_param = Param(address="/octHi", type=int, min=0, max=9)
        self.saving.root_param.insertChild(self.octHi_param)
        self.octHi = ParamSpinBox(self.octHi_param, self.tab,"/octHi")
        self.octHi.setGeometry(QRect(169,204,32,18))

        self.octLo_param = Param(address="/octLo", type=int, min=0, max=9)
        self.saving.root_param.insertChild(self.octLo_param)
        self.octLo = ParamSpinBox(self.octLo_param, self.tab,"/octLo")
        self.octLo.setGeometry(QRect(73,204,32,18))
        
        self.connect(self.octHi_param, PYSIGNAL("paramUpdate"), self.check_oct)
        self.connect(self.octLo_param, PYSIGNAL("paramUpdate"), self.check_oct)
        
        self.octLoLabel = QLabel(self.tab,"octLoLabel")
        self.octLoLabel.setGeometry(QRect(19,208,55,16))
        self.octHiLabel = QLabel(self.tab,"octHiLabel")
        self.octHiLabel.setGeometry(QRect(114,208,55,16))
        
        self.mastertempo = Param(type=float, address="/master_tempo", min=0, max=32)
        self.mastertempo_sl = LabelSlider(self.mastertempo, "Master Tempo", self.tab)
        self.mastertempo_sl.setGeometry(QRect(10, 228, 280, 20))
        self.saving.root_param.insertChild(self.mastertempo)
        
        #start wave chooser
        self.op1_param = Param(address="/op1")
        self.op1_param.set_enableosc(0)
        self.saving.root_param.insertChild(self.op1_param)
        self.op2_param = Param(address="/op2")
        self.op2_param.set_enableosc(0)
        self.saving.root_param.insertChild(self.op2_param)
        self.op3_param = Param(address="/op3")
        self.op3_param.set_enableosc(0)
        self.saving.root_param.insertChild(self.op3_param)
        
        self.wavebox = QHBox(self.tab)
        self.wavebox.setGeometry(QRect(130,8,134,61))
                
        p = Param(address="/seqorder", type=int, min=0, max=3)
        self.saving.root_param.insertChild(p)
        sl = ParamSlider(p, self.wavebox, "Seqorder")
        sl.setPageStep(1)
        sl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        #sl.setText(self.__tr("Order"))
        
        self.wavebox2 = QVBox(self.wavebox)
        self.squ = QLabel(self.wavebox2)
        self.squ.setPaletteForegroundColor(QColor(85,255,0))
        self.saw = QLabel(self.wavebox2)
        self.saw.setPaletteForegroundColor(QColor(85,255,0))
        self.tri = QLabel(self.wavebox2)
        self.tri.setPaletteForegroundColor(QColor(85,255,0))
        self.sin = QLabel(self.wavebox2)
        self.sin.setPaletteForegroundColor(QColor(85,255,0))
        
        self.wave1_param = Param(address="/wave", type=int, min=0, max=3)
        self.op1_param.insertChild(self.wave1_param)
        self.wave1 = ParamSlider(self.wave1_param, self.wavebox, "/wave1")
        
        self.wave2_param = Param(address="/wave", type=int, min=0, max=3)
        self.op2_param.insertChild(self.wave2_param)
        self.wave2 = ParamSlider(self.wave2_param, self.wavebox,"/wave1")

        self.wave3_param = Param(address="/wave", type=int, min=0, max=3)
        self.op3_param.insertChild(self.wave3_param)
        self.wave3 = ParamSlider(self.wave3_param, self.wavebox,"/wave1")
        
        self.wave1.setPageStep(1)
        self.wave2.setPageStep(1)
        self.wave3.setPageStep(1)

        
        #Start keyboard
        self.keyboardHi, self.keyboardHi_param = self.generate_keyboard("/keyboardHi", 16, 8)
        self.keyboardLo, self.keyboardLo_param = self.generate_keyboard("/keyboardLo", 16, 48)
        
        [self.saving.root_param.insertChild(par) for par in self.keyboardHi_param + self.keyboardLo_param + self.params]
            

        rc = QVBox(self.tab_2)
        rc.setGeometry(0,0,300, 280)
        self.routing = Routing(3, 6, True, rc)
        self.routing2 = Routing(3, 5, True, rc)
        rl1 = ["/op1", "/op2", "/op3", "/relfreq", "/vol", "/pan"]
        rl2 = ["/delay", "/attack", "/decay", "/sustain", "/release"]
        rl = rl1
        for rou in (self.routing, self.routing2):
            i = 0
            clist= []
            for ch in rou.root_param.children():
                ch.set_enableosc(0)
                self.saving.root_param.insertChild(ch)
                ch.set_address(rl1[i])
                j = 0
                for c in ch.children():
                    clist.append(c)
                    c.set_address(rl[j])
                    c.type = float
                    c.max = 1000
                    c.min = 0
                    j += 1
                i += 1
            rl = rl2
            rou.set_column_width(40)
            rou.set_row_height(25)
            rou.adjustSize()
            
        rl1 = ["op1", "op2", "op3", "relfreq", "vol", "pan"]
        rl2 = ["D", "A", "D", "S", "R"]
        self.routing.set_row_labels(QStringList.fromStrList(rl1))
        self.routing.set_col_labels(QStringList.fromStrList(rl1))
        
        self.routing2.set_row_labels(QStringList.fromStrList(rl1))
        self.routing2.set_col_labels(QStringList.fromStrList(rl2))
        self.routing2.setFixedHeight(180)
        #self.routing2.table1.setFixedHeight(180)
        self.clearWState(Qt.WState_Polished)
        
        self.languageChange()
        
        self.saving.init_controls()
        
    def languageChange(self):
        self.setCaption(self.__tr("pm7"))
        self.setIconText(QString.null)
        self.octLoLabel.setText(self.__tr("Oct min"))
        self.octHiLabel.setText(self.__tr("Oct max"))
        self.sin.setText(self.__tr("sin"))
        self.tri.setText(self.__tr("tri"))
        self.saw.setText(self.__tr("saw"))
        self.squ.setText(self.__tr("squ"))
        self.tabWidget.changeTab(self.tab,self.__tr("1"))
        self.tabWidget.changeTab(self.tab_2,self.__tr("2"))
    
    def toggle_page(self):
        if self.tabWidget.currentPage() is self.tab:
            self.tabWidget.showPage(self.tab_2)
        else:
            self.tabWidget.showPage(self.tab)
            
    def generate_keyboard(self, label, x, y):
        buttons = []
        params = []
        pos = [(0, 14), (8, 0), (16, 14), (24, 0), (32, 14), (48, 14), 
            (56, 0), (64, 14), (72, 0), (80, 14), (88, 0), (96, 14)]
        for r in range (12):
            param = Param(address=label+str(r), type=bool)
            params.append(param)
            button = ParamRadioButton(param, self.tab,label+str(r))
            button.setPaletteForegroundColor(QColor(255,0,255))
            button.setFocusPolicy(QRadioButton.NoFocus)
            button.setGeometry(pos[r][0] + x, pos[r][1] + y, 16, 16)
            buttons.append(button)
        return buttons, params
    
    def check_oct(self, msg):
        if msg is self.octHi_param.UpdateState:
            if self.octHi_param.get_state() >= self.octLo_param.get_state():
                return
            if self.sender() is self.octHi_param:
                self.octLo_param.set_state(self.octHi_param.get_state())
            elif self.sender() is self.octLo_param:
                self.octHi_param.set_state(self.octLo_param.get_state())
    
    def activate(self):
        self.saving.activate()
    def deactivate(self):
        self.saving.deactivate()
    def on_off(self, arg = None):
        self.saving.on_off(arg)
        #This is an unsafe hack.
    def tgl_active(self, arg = None):
        self.saving.tgl_active(arg)
        
    def __tr(self,s,c = None):
        return qApp.translate("pm7",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = pm7()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
