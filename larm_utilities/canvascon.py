# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"
# -*- coding: utf-8 -*-

import sys
from qt import *
#Import the MarioDots module
from canvas import *


class Form1(QDialog):
    def __init__(self,parent = None,name = None,modal = 0,fl = 0):
        QDialog.__init__(self,parent,name,modal,fl)

        if not name:
            self.setName("Form1")

        self.setPaletteBackgroundColor(QColor(100,100,100))


        self.pushButton3 = QPushButton(self,"pushButton3")
        self.pushButton3.setGeometry(QRect(380,380,102,25))

        self.pushButton1 = QPushButton(self,"pushButton1")
        self.pushButton1.setGeometry(QRect(160,380,99,25))

        self.marioDots2 = MarioDots(self,"marioDots2")
        self.marioDots2.setGeometry(QRect(150,40,300,300))

        self.textLabel1 = QLabel(self,"textLabel1")
        self.textLabel1.setGeometry(QRect(150,20,300,20))
        self.textLabel1.setPaletteForegroundColor(QColor(255,255,255))
        self.textLabel1.setPaletteBackgroundColor(QColor(100,100,100))
        self.textLabel1.setBackgroundOrigin(QLabel.WindowOrigin)
        textLabel1_font = QFont(self.textLabel1.font())
        textLabel1_font.setFamily("Futura")
        textLabel1_font.setPointSize(12)
        self.textLabel1.setFont(textLabel1_font)

        self.languageChange()

        self.resize(QSize(632,425).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)

        self.connect(self.pushButton1,SIGNAL("released()"),self.marioDots2.test)
        self.connect(self.marioDots2,SIGNAL("newlabel(const QString&)"),self.textLabel1.setText)


    def languageChange(self):
        self.setCaption(self.__tr("Form1"))
        self.pushButton3.setText(self.__tr("pushButton3"))
        self.pushButton1.setText(self.__tr("pushButton1"))
        self.textLabel1.setText(self.__tr("textLabel1"))


    def __tr(self,s,c = None):
        return qApp.translate("Form1",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = Form1()
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
