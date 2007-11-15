#!/usr/bin/env python
"""A soundfile library/tagger

Scanning directories for soundfiles (wav format), and makes it possible to add
tags. The files are kept in the database forever (currently no delete function,
but should be easy to implement), and set to inactive when removed, so the tag settings can be kept (good for eg removable devices, just rescan and previously inactive files will be activated). 

Files can also be moved within the directories - the db is saving a unique hash string for every file, so they can be identified. If the hash has changed (eg after editing), the user is informed and may choose to update the hash string.
"""
# -*- coding: utf-8 -*-

import sys, os
from qt import *

from sqlobject import *
import fnmatch
import wave

import FileHasher

DB_PATH = "/home/johannes/myprojects/larm/trunk/audiodb/data.db"
FILEPATHS = ["/home/johannes/samples"]  # Change this to your audio file directories

class dbSoundFiles(SQLObject):
    fullPath = StringCol()
    hash = StringCol(length=32)
    active = BoolCol(default=True)
    size = IntCol(default=0)
    channels = IntCol(default=0)
    samplerate = IntCol(default=0)
    tags = RelatedJoin('dbTags')

class dbTags(SQLObject):
    name = StringCol()
    dbSoundFiles = RelatedJoin('dbSoundFiles')

class TagEditor(QMainWindow):
    def __init__(self,parent = None,name = None,fl = 0):
    
        QMainWindow.__init__(self,parent,name,fl)
        
        self.filepaths = FILEPATHS
        
        
        self.menu = QMenuBar(self)
        self.menu.insertItem( "Quit", qApp, SLOT("quit()"), QKeySequence("CTRL+Key_Q") );
        self.status = QStatusBar(self)

        if not name:
            self.setName("Tag_editor")
        self.mainbox = QHBox(self)
        self.setCentralWidget(self.mainbox)

        self.frame5 = QVBox(self.mainbox,"frame5")
        self.mainbox.setStretchFactor(self.frame5, 2)
        self.frame5.setFrameShape(QFrame.StyledPanel)
        self.frame5.setFrameShadow(QFrame.Raised)

        self.textLabel1_3 = QLabel(self.frame5,"textLabel1_3")
        
        self.tags_cb = QComboBox(self.frame5,"tags_cb")
        
        self.playbox = QHBox(self.frame5)
        self.playbtn = QPushButton("Play", self.playbox)
        self.stopbtn = QPushButton("Stop", self.playbox)
        
        self.samples_box = QListBox(self.frame5,"samples_box")
        
        self.rescan_button = QPushButton("Rescan Directory", self.frame5)

        self.frame3 = QVBox(self.mainbox,"frame3")
        self.mainbox.setStretchFactor(self.frame3, 1)
        self.frame3.setFrameShape(QFrame.StyledPanel)
        self.frame3.setFrameShadow(QFrame.Raised)

        self.textLabel1 = QLabel(self.frame3,"textLabel1")

        self.newtag_box = QLineEdit(self.frame3,"newtag_box")
        self.newtag_box.mousePressEvent = self.newtag_box_mouse_press

        self.available_tags = QListBox(self.frame3,"available_tags")

        self.frame4 = QVBox(self.mainbox,"frame4")
        self.mainbox.setStretchFactor(self.frame4, 1)
        self.frame4.setFrameShape(QFrame.StyledPanel)
        self.frame4.setFrameShadow(QFrame.Raised)

        self.textLabel1_2 = QLabel(self.frame4,"textLabel1_2")
        self.textLabel1_2.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        self.used_tags = QListBox(self.frame4,"used_tags")
        
        self.mainbox.adjustSize()

        self.languageChange()

        self.resize(QSize(608,670).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)
        
        self.playprocess = None
        self.currentObj = None

        self.setup_db()

        self.connect(self.used_tags,SIGNAL("selected(int)"),self.switch_tag_placement)
        self.connect(self.available_tags,SIGNAL("selected(int)"),self.switch_tag_placement)
        self.connect(self.newtag_box,SIGNAL("returnPressed()"),self.add_new_tag)
        self.connect(self.tags_cb, SIGNAL("activated(const QString&)"), self.filter_soundfiles)
        self.connect(self.samples_box, SIGNAL("selected(const QString&)"), self.play_soundfile)
        self.connect(self.samples_box, SIGNAL("highlighted(const QString&)"), self.change_current_file)
        self.connect(self.playbtn, SIGNAL("pressed()"), self.play_soundfile)
        self.connect(self.stopbtn, SIGNAL("pressed()"), self.stop_soundfile)
        self.connect(self.rescan_button, SIGNAL("pressed()"), self.rescandirectory)
        
    def switch_tag_placement(self, index):
        tag = dbTags.select(dbTags.q.name == str(self.sender().text(index)))[0]
        if self.sender() is self.available_tags:
            send = self.available_tags
            recv = self.used_tags
            if list(self.currentObj):
                self.currentObj[0].addDbTags(tag)
        elif self.sender() is self.used_tags:
            send = self.used_tags
            recv = self.available_tags
            if list(self.currentObj):
                self.currentObj[0].removeDbTags(tag)
        recv.insertItem(send.text(index))
        send.removeItem(index)
    
    def add_new_tag(self):
        t = self.sender().text()
        if not self.available_tags.findItem(t):
            self.available_tags.insertItem(t)
            self.tags_cb.insertItem(t)
            dbTags(name=str(t))
            self.alltags.append(t)
        self.sender().clear()
        self.sender().clearFocus()
        
    def newtag_box_mouse_press(self, ev):
        self.newtag_box.clear()
        
    def setup_db(self):
        db_filename = os.path.abspath(DB_PATH)
        connection_string = 'sqlite://' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
        
        self.alltags = self.listtags()
        self.alltags.sort()
        self.available_tags.insertStrList(self.alltags)
        self.tags_cb.insertItem("@ALL")
        self.tags_cb.insertItem("@UNTAGGED")
        self.tags_cb.insertItem("@INACTIVE")
        self.tags_cb.insertStrList(self.alltags)
        self.filter_soundfiles("@ALL")
    
    def filter_soundfiles(self, string):
        string = str(string)
        if string in ("@ALL", "@UNTAGGED", "@INACTIVE"):
            fl = self.listfiles(string)
        else:
            fl = self.findfilesfromtag(string)
        self.samples_box.clear()
        self.samples_box.insertStrList(fl)
        self.samples_box.sort()
    
    def change_current_file(self, string):
        self.currentObj = dbSoundFiles.selectBy(fullPath=str(string), active=True)
        if not self.currentObj.count():
            return
        tags = self.currentObj[0].tags
        taglist = []
        self.available_tags.clear()
        [taglist.append(t.name) for t in tags]
        [self.available_tags.insertItem(t) for t in self.alltags if t not in taglist]
        self.used_tags.clear()
        self.used_tags.insertStrList(taglist)
        co = self.currentObj[0]
        if co.channels is 1:
            ch = "Mono"
        elif co.channels is 2:
            ch = "Stereo"
        else:
            ch = "%d channels" % co.channels
        size = "0.0 s"
        if co.samplerate:
            size = "%.1f s" % (float(co.size) / float(co.samplerate))
        self.status.message("%s: %d Hz, %s, %s" % (co.fullPath, co.samplerate, ch, size))
        qApp.clipboard().setText(co.fullPath, QClipboard.Selection)
        
        
    def listfiles(self, filter=None):
        """Print out all files in database as well as return all file objects"""
        q=''
        if filter in ("@ALL", "@UNTAGGED"):
            q = dbSoundFiles.q.active==True
        elif filter == ("@INACTIVE"):
            q = dbSoundFiles.q.active==False
        fileObjs = dbSoundFiles.select(q)
        i = 0
        filelist = []
        [filelist.append(f.fullPath) for f in fileObjs if not f.tags or filter != "@UNTAGGED"]
        #for fileObj in fileObjs:
        #    print "%d > %s" % (i, fileObj.fullPath)
        #    i += 1
        return filelist
    
    def listtags(self, hash=None):
        """ returns tags for all or one certain soundfile. One: hash as arg, All: no arg
        """
        if hash:
            tags = dbSoundFiles.selectBy(hash=hash, active=True)[0].tags
        else:
            tag = dbTags.select()
            tags = list(tag)
        i = 0
        taglist = []
        [taglist.append(t.name) for t in tags]
        return taglist
    
    def findfilesfromtag(self, tag = None):
        if tag:
            tagObj = dbTags.selectBy(name=tag)
        else:
            tagObj = dbTags.select()
        fl = []
        for tag in tagObj:
            [fl.append(t.fullPath) for t in tag.dbSoundFiles if t.active is True]
        return fl
        
    def play_soundfile(self, string=None):
        if string:
            self.soundplayer(True, string)
        elif not string and self.samples_box.currentText():
            self.soundplayer(True, str(self.samples_box.currentText()))
    
    def stop_soundfile(self):
        self.soundplayer(False)
    
    def soundplayer(self, play, file=None):
        if self.playprocess and play:
            self.soundplayer(False)
        if play and file:
            self.playprocess = os.spawnvp(os.P_NOWAIT, 'aplay',  ('aplay', '-q', file))
        elif not play:
            os.kill(self.playprocess, 15)
            self.playprocess = None
    
    def locate(self, pattern):
        '''Locate all files matching supplied filename pattern in and below
        supplied root directory.'''
        for root in self.filepaths:
            for path, dirs, files in os.walk(os.path.abspath(root)):
                for filename in fnmatch.filter(files, pattern):
                    yield os.path.join(path, filename)
    
    def limit_to_new(self, db, files):
        return [files.remove(p.fullPath) for p in db if p.fullPath in files]
        
    def scan_for_new_files(self):
        self.status.message("Scanning for new files...")
        self.rescandirectory(self.limit_to_new)
        self.status.clear()
                    
    def rescandirectory(self, limitcallback = None):
        """Check for new files in directory and update paths and stuff."""
        existingfiles = dbSoundFiles.select()

        filehashdict = {} # files currently on disk
        gen = self.locate('*.wav')
        files = []
        [files.append(f) for f in gen]
        if limitcallback:
            limitcallback(existingfiles, files)
        n = len(files)
        progress = QProgressDialog("%d files found. Hashing..." % n, "Cancel", n, self)
        
        i = 0
        for file in files:
            h = FileHasher.readfile(file)
            filehashdict[h] = file
            i+=1
            progress.setProgress(i)
            qApp.processEvents()
            if progress.wasCanceled():
                return
        progress.setProgress(n)
        
        n = existingfiles.count()
        i = 0
        progress = QProgressDialog("Checking against database...", "Cancel", n, self)
        for file in existingfiles: 
            if file.hash in filehashdict: 
                file.active = True 
                file.fullPath = filehashdict[file.hash]
                self.inspect_wave(file)
                filehashdict.pop(file.hash) 
            elif file.hash not in filehashdict and not limitcallback:
                file.active = False
            if progress.wasCanceled():
                return
            i+=1
            progress.setProgress(i)
            qApp.processEvents()
        progress.setProgress(n)
        
        n = len(filehashdict)
        i = 0
        progress = QProgressDialog("Inserting new files", "Cancel", n, self)
        for hash, path in filehashdict.items(): # insert new files into db
            if progress.wasCanceled():
                return
            selected = dbSoundFiles.selectBy(fullPath=path)
            if selected.count() and QMessageBox.question(self, "Is this file changed?", \
                "This file: <br> %s <br> already exists in the database, but the file seem to have changed. To preserve the tags for the file, press Yes. If this is a new file and you want to assign new tags to it, press No." % path,
                "&No", "&Yes"):
                selected[0].hash = hash
                selected[0].active = True
            else:
                fileObj = dbSoundFiles(fullPath=path, hash=hash, active=True)
                self.inspect_wave(fileObj)
            i+=1
            progress.setProgress(i)
            qApp.processEvents()
        progress.setProgress(n)
        self.tags_cb.setCurrentText(QString("@UNTAGGED"))
        self.filter_soundfiles("@UNTAGGED")
    
    def inspect_wave(self, sqlobj):
        file = sqlobj.fullPath
        try:
            f = wave.open(file, "r")
        except IOError:
            print "wavlength: No such file"
        else:
            sqlobj.size = int(f.getnframes())
            sqlobj.channels = int(f.getnchannels())
            sqlobj.samplerate = int(f.getframerate())
            if 0 in (sqlobj.size, sqlobj.channels, sqlobj.samplerate):
                QMessageBox.warning(self, "Couldn't get wave data", \
                "There seems to be something wrong with this file: <br> %s <br>   Tage couldn't extract all the data he needs. Please check it.                File is deactivated for now." % file)
                sqlobj.active = False
            f.close()
        
    def languageChange(self):
        self.setCaption(self.__tr("Tag Editor"))
        self.textLabel1_3.setText(self.__tr("Sound files"))
        self.samples_box.clear()
        self.textLabel1.setText(self.__tr("Available tags"))
        self.available_tags.clear()
        self.textLabel1_2.setText(self.__tr("Choose tag by clicking on available tags"))

    def __tr(self,s,c = None):
        return qApp.translate("Tag_editor",s,c)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    try:
        import psyco
        psyco.profile()
    except ImportError:
        QMessageBox.information(None, "Tage", "Can't import psyco. Install it to make it go fast.")
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = TagEditor()
    a.setMainWidget(w)
    w.show()
    #QTimer.singleShot(0, w.scan_for_new_files)
    a.exec_loop()
    if w.playprocess:
        w.soundplayer(False)
