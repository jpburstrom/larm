# Copyright 2007 Johannes Burström, <johannes@ljud.org>
# -*- coding: utf-8 -*-
__version__ = "$Revision$"

import sys
from qt import *


class Machine(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("Machine")



        self.frame7 = QFrame(self,"frame7")
        self.frame7.setGeometry(QRect(0,0,140,150))
        self.frame7.setPaletteBackgroundColor(QColor(100,100,100))
        self.frame7.setFrameShape(QFrame.StyledPanel)
        self.frame7.setFrameShadow(QFrame.Raised)

        self.textLabel2 = QLabel(self.frame7,"textLabel2")
        self.textLabel2.setGeometry(QRect(10,10,120,20))
        self.textLabel2.setPaletteForegroundColor(QColor(255,255,255))
        textLabel2_font = QFont(self.textLabel2.font())
        textLabel2_font.setFamily("Pigiarniq Heavy")
        textLabel2_font.setPointSize(10)
        self.textLabel2.setFont(textLabel2_font)

        self.languageChange()

        self.resize(QSize(600,480).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Form2"))
        self.textLabel2.setText(self.__tr("textLabel2"))


    def __tr(self,s,c = None):
        return qApp.translate("Machine",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = Machine()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
