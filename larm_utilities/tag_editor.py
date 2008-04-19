#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
"""A soundfile library/tagger

Scanning directories for soundfiles (wav format), and makes it possible to add
tags. The files are kept in the database forever (currently no delete function,
but should be easy to implement), and set to inactive when removed, so the tag settings can be kept (good for eg removable devices, just rescan and previously inactive files will be activated). 

Files can also be moved within the directories - the db is saving a unique hash string for every file, so they can be identified. If the hash has changed (eg after editing), the user is informed and may choose to update the hash string.

Options:
    -p --plot           Plot when analyzing (extremely slow, but good for debug)
    -h --help           Show this help
"""

from __future__ import with_statement

import sys, os
from qt import *

from sqlobject import *
from aubio.task import *
import fnmatch
import wave
import getopt

import FileHasher

DB_PATH = "/home/johannes/myprojects/larm/trunk/larm_utilities/data.db"
FILEPATHS = ["/home/johannes/samples"]  # Change this to your audio file directories

TESTRUN = False #no saving to db
PLOT = False 

class dbSoundFiles(SQLObject):
    fullPath = StringCol()
    hash = StringCol(length=32)
    active = BoolCol(default=True)
    size = IntCol(default=0)
    channels = IntCol(default=0)
    samplerate = IntCol(default=0)
    popularity = IntCol(default=None)
    tags = RelatedJoin('dbTags')
    spectral_centroid = FloatCol(default=None)
    spectral_flatness = FloatCol(default=None)
    onsets = IntCol(default=None)
    onset_cues = StringCol(default=None)
    power = FloatCol(default=None)

class dbTags(SQLObject):
    name = StringCol()
    dbSoundFiles = RelatedJoin('dbSoundFiles')

class Analyzer(object):

    def onset_detection(self, file):

        filename = file.fullPath
        
        plot = PLOT
        beat = 0
        outplot = 0

        params = taskparams()
        params.hopsize    = 512
        params.bufsize    = 1024
        params.threshold  = 0.01
        params.dcthreshold = 1.
        params.zerothres  = 0.008
        params.silence    = -80.0
        params.mintol     = 0.028
        params.verbose    = False
        # default take back system delay
        # if options.delay: params.delay = int(float(options.delay)/params.step)

        dotask = taskonset

        #for plotting
        params.storefunc=True

        lonsets, lofunc = [], []
        wplot,oplots = [],[]
        modes = ['dual']
        for i in range(len(modes)):
            params.onsetmode = modes[i] 
            while True:
                qApp.processEvents()
                filetask = dotask(filename,params=params)
                onsets = filetask.compute_all()
                    
                onsetspersec = len(onsets)/(file.size/48000.0)
                if onsetspersec > 5 and params.threshold <= 2.15:
                    params.threshold += 0.25
                else:
                    break


            ofunc = filetask.ofunc
            lofunc.append(ofunc)

            if plot:
                if beat: 
                    filetask.plot(oplots, onsets)
                else:
                    filetask.plot(onsets, ofunc, wplot, oplots, nplot=False)

            if plot: filetask.plotplot(wplot, oplots, outplot="/tmp/onset", extension="png",
              xsize=0.8,ysize=0.8,spectro=False)

        return [int(file.samplerate * i[0] * filetask.params.step) for i in onsets]


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
        
        if TESTRUN:
            foo = QLabel("TESTRUN", self.frame5)
            foo.setPaletteBackgroundColor(Qt.red)
            foo.setPaletteForegroundColor(Qt.white)
        
        self.textLabel1_3 = QLabel(self.frame5,"textLabel1_3")
        
        self.tags_cb = QComboBox(self.frame5,"tags_cb")
        
        self.playbox = QHBox(self.frame5)
        self.playbtn = QPushButton("Play", self.playbox)
        self.stopbtn = QPushButton("Stop", self.playbox)
        
        self.samples_box = QListBox(self.frame5,"samples_box")
        
        self.rescan_button = QPushButton("Full Rescan", self.frame5)
        self.analyze_button = QPushButton("Re-analyze files", self.frame5)
        self.purge_empty_button= QPushButton("Purge inactive files", self.frame5)
        
        self.rightframe = QVBox(self.mainbox)
        self.mainbox.setStretchFactor(self.rightframe, 2)
        self.topright = QHBox(self.rightframe)
        self.rightframe.setStretchFactor(self.topright, 2)
        
        self.logwindow = QTextEdit(self.rightframe)
        self.logwindow.setTextFormat(Qt.LogText)
        
        if PLOT:
            pixmap = QPixmap("/tmp/onset.png")
            self.plot = QLabel(self.rightframe)
            self.plot.setPixmap(pixmap)
        
        self.frame3 = QVBox(self.topright,"frame3")
        self.frame3.setFrameShape(QFrame.StyledPanel)
        self.frame3.setFrameShadow(QFrame.Raised)

        self.textLabel1 = QLabel(self.frame3,"textLabel1")

        self.newtag_box = QLineEdit(self.frame3,"newtag_box")
        self.newtag_box.mousePressEvent = self.newtag_box_mouse_press

        self.available_tags = QListBox(self.frame3,"available_tags")
        
        
        self.frame4 = QVBox(self.topright,"frame4")
        self.frame4.setFrameShape(QFrame.StyledPanel)
        self.frame4.setFrameShadow(QFrame.Raised)

        self.textLabel1_2 = QLabel(self.frame4,"textLabel1_2")
        self.textLabel1_2.setAlignment(QLabel.WordBreak | QLabel.AlignVCenter)

        self.used_tags = QListBox(self.frame4,"used_tags")
        
        self.samplecontext = QPopupMenu(self)
        self.samplecontext.insertItem("Reanalyze")
        self.mainbox.adjustSize()
        
        self.languageChange()

        self.resize(QSize(608,670).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)
        
        self.playprocess = None
        self.currentObj = None

        self.setup_db()

        self.connect(self.samples_box, SIGNAL("contextMenuRequested(QListBoxItem *, const QPoint &)"), self.samplecontext_request)
        self.connect(self.samplecontext, SIGNAL("activated(int)"), self.samplecontext_handler)
        self.connect(self.used_tags,SIGNAL("selected(int)"),self.switch_tag_placement)
        self.connect(self.available_tags,SIGNAL("selected(int)"),self.switch_tag_placement)
        self.connect(self.newtag_box,SIGNAL("returnPressed()"),self.add_new_tag)
        self.connect(self.tags_cb, SIGNAL("activated(const QString&)"), self.filter_soundfiles)
        self.connect(self.samples_box, SIGNAL("selected(const QString&)"), self.play_soundfile)
        self.connect(self.samples_box, SIGNAL("highlighted(const QString&)"), self.change_current_file)
        self.connect(self.playbtn, SIGNAL("pressed()"), self.play_soundfile)
        self.connect(self.stopbtn, SIGNAL("pressed()"), self.stop_soundfile)
        self.connect(self.rescan_button, SIGNAL("pressed()"), self.rescandirectory)
        self.connect(self.analyze_button, SIGNAL("pressed()"), self.analyze)
        self.connect(self.purge_empty_button, SIGNAL("pressed()"), self.purge_empty)
        
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
        
    def samplecontext_handler(self, id):
        if self.sender().text(id) == "Reanalyze":
            self.analyze(self.currentObj[0])
            #self.filter_soundfiles(str(self.tags_cb.currentText()))
    
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
    
    def purge_empty(self):
        if not TESTRUN and QMessageBox.question(self, "Are you sure?", \
            "You're about to remove all inactive files from the database. Are you sure about this? ",
            "&No", "&Yes"):
            results = dbSoundFiles.selectBy(active=False)
            [row.destroySelf() for row in list(results) ]
        
        
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
        qApp.clipboard().setText(co.fullPath, QClipboard.Selection)
        self.logwindow.append(
"""/////////////////////////
%s: %d Hz, %s, %s 
spectral centroid (unused): %s 
spectral flatness measure (unused): %s 
number of onsets:%s 
onset cues: %s 
power in rms (unused): %s""" % 
            (co.fullPath, co.samplerate, ch, size, co.spectral_centroid, 
                co.spectral_flatness, co.onsets, co.onset_cues, co.power))
        self.logwindow.scrollToBottom()
        
        
    def samplecontext_request(self, item, qp):
        self.samplecontext.popup(qp)
        
        
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
        [files.remove(p.fullPath) for p in db if p.fullPath in files]
        return files
        
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
            files = limitcallback(existingfiles, files)
        n = len(files)
        progress = QProgressDialog("%d files found. Hashing..." % n, "Cancel", n, self)
        
        i = 0
        for file in files:
            self.logwindow.append("Hashing %s" % file);
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
                if not TESTRUN:
                    file.fullPath = filehashdict[file.hash]
                    self.inspect_wave(file)
                filehashdict.pop(file.hash) 
            elif file.hash not in filehashdict and not limitcallback and not TESTRUN:
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
            if TESTRUN or progress.wasCanceled():
                return
            selected = dbSoundFiles.selectBy(fullPath=path)
            if selected.count() and QMessageBox.question(self, "Is this file changed?", \
                "This file: <br> %s <br> already exists in the database, but the file seem to have changed. To preserve the tags for the file, press Yes. If this is a new file and you want to assign new tags to it, press No." % path,
                "&No", "&Yes"):
                selected[0].hash = hash
                selected[0].active = True
                fileObj = selected[0]
            else:
                fileObj = dbSoundFiles(fullPath=path, hash=hash, active=True)
            self.analyze(fileObj)
            i+=1
            progress.setProgress(i)
            qApp.processEvents()
        progress.setProgress(n)
        self.tags_cb.setCurrentText(QString("@UNTAGGED"))
        self.filter_soundfiles("@UNTAGGED")
    
    def inspect_wave(self, sqlobj):
        file = sqlobj.fullPath
        self.logwindow.append("inspecting %s..." % file);
        try:
            f = wave.open(file, "r")
        except IOError:
            print "wavlength: No such file"
        else:
            size = int(f.getnframes())
            channels = int(f.getnchannels())
            samplerate = int(f.getframerate())
            if 0 in (size, channels, samplerate):
                QMessageBox.warning(self, "Couldn't get wave data", \
                    "There seems to be something wrong with this file: <br> %s <br>   Tage couldn't extract all the data he needs. Please check it.                File is deactivated for now." % file)
                if not TESTRUN:
                    sqlobj.active = False
                    f.close()
                    return False
                else:
                    f.close()
                    return False
            elif not TESTRUN:
                sqlobj.active = True
                sqlobj.size = size
                sqlobj.channels = channels
                sqlobj.samplerate = samplerate
            f.close()
            return True
    
    def analyze(self, files=None):
        plot = PLOT
        analyzer = Analyzer()
        if not files:
            files = dbSoundFiles.select()
            n = files.count()
        elif not isinstance(files, list):
            files = [files]
            n = len(files)
        else:
            n = len(files)
        i = 0
        progress = QProgressDialog("Checking against database...", "Cancel", n, self)
        for file in files:
            if file.active:
                progress.setLabelText(QString("Inspecting %s" % file.fullPath))
                if not self.inspect_wave(file):
                    continue
                if TESTRUN:
                    analyzer.onset_detection(file)
                else:
                    self.logwindow.append("checking onsets...");
                    onsets = [0]
                    onsets.extend(analyzer.onset_detection(file))
                    file.onsets = len(onsets)
                    file.onset_cues = " ".join(["%s" % el for el in onsets])
                if plot:
                    self.logwindow.append("plotting...");
                    self.plot.pixmap().load("/tmp/onset.png")
                    self.plot.update()
            if progress.wasCanceled():
                return
            i+=1
            progress.setProgress(i)
            qApp.processEvents()
        self.logwindow.append("DONE")
        progress.setProgress(n)
                
    def languageChange(self):
        self.setCaption(self.__tr("Tag Editor"))
        self.textLabel1_3.setText(self.__tr("Sound files"))
        self.samples_box.clear()
        self.textLabel1.setText(self.__tr("Available tags"))
        self.available_tags.clear()
        self.textLabel1_2.setText(self.__tr("Choose tag by clicking on available tags"))

    def __tr(self,s,c = None):
        return qApp.translate("Tag_editor",s,c)

def usage():
    print __doc__

def parse_options():
    global PLOT
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp", ["help", "plot"])
    except getopt.GetoptError, err:
        print str(err) 
        usage()
        sys.exit(2)
    output = None
    verbose = False
    for o, a in opts:
        if o in ("-p", "--plot"):
            PLOT = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        else:
            assert False, "unhandled option"


if __name__ == "__main__":
    a = QApplication(sys.argv)
    parse_options()
    try:
        import psyco
        psyco.profile()
    except ImportError:
        QMessageBox.information(None, "Tage", "Can't import psyco. Install it to make it go fast.")
##    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = TagEditor()
    a.setMainWidget(w)
    w.show()
##    w.analyze()
    if QMessageBox.question(w, "What do you think?", \
            "Should we do a scan for new files?",
            "&No", "&Yes"):
        QTimer.singleShot(0, w.scan_for_new_files)
    a.exec_loop()
##    if w.playprocess:
##        w.soundplayer(False)
    
