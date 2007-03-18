#!/usr/bin/env python

from qt import QColor, QAction, QKeySequence

def getgl(key):
    
    gl = {
        "pdcommand" : "pd -nogui -rt -cb_scheduler /home/johannes/pd/larm/immer2-back.pd", #pd launch command
        "polltime" : 0.02, #ms, how often mouse gets polled
        "mouse_resolution" : 3000, #a factor, larger = faster (i think)
        "osc_address" : "127.0.0.1", 
        "osc_port" : 9000, #port for sending osc msgs
        "osc_listen_port" : 9001, #port for receiving osc
        "mouse_device" : "/dev/input/event2", #path to mouse device. you may need r/w permissions...
        "audiodb_path" : 'audiodb/data.db', #relative (to script) or absolute path to audiofile db
        "samplerate" : 48000, #samplerate of backend, needed to calculate rec buffer labels 
        "txtfile" : "notes.txt" #file with notes
        }

    return gl[key]

def dbp(*msg):
    pass
    #print msg
    
