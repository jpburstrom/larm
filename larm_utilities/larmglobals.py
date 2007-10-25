#!/usr/bin/env python

from qt import QColor, QAction, QKeySequence, QMessageBox
import sys
from os import path
#from xmlsave import XmlSaving

def getgl(key):
    
    gl = {
        "pdcommand" : "".join(["pd -nogui -rt ", sys.path[0],  "/backend/immer2-back.pd"]), #pd launch command
        #"pdcommand" : "true", #not pd launch command
        "polltime" : 0.04, #ms, how often mouse gets polled
        "mouse_resolution" : 1500, #some kind of resolution factor, larger = slower
        "osc_address" : "127.0.0.1", 
        "osc_port" : 9000, #port for sending osc msgs
        "osc_listen_port" : 9001, #port for receiving osc
        "mouse_device" : "/dev/input/event101", #path to mouse device. you may need r/w permissions...
        "audiodb_path" : 'audiodb/data.db', #relative (to script) or absolute path to audiofile db
        "samplerate" : 48000, #samplerate of backend, needed to calculate rec buffer labels 
        "txtfile" : path.expanduser("~/.larm/notes.txt"), #file with notes
        "preset_file" : path.expanduser('~/.larm/presets.xml')
        }

    return gl[key]
    
def get_keyboard(caller):
    keys = {"tgl_keys" : 
        #these are functions taking 1/0 as argument, for keyboard press/release.
                {"nomod" : {
                    "q" : caller.mlp1.tgl_active,
                    "w" : caller.mlp2.tgl_active,
                    "e" : caller.mlp3.tgl_active,
                    "r" : caller.mlp4.tgl_active,
                    #"a" : caller.pm7.tgl_active,
                    "s" : caller.grandel.tgl_active,
                    "d" : caller.delay.tgl_active,
                    "f" : caller.combo.tgl_active,
                    "g" : caller.room.tgl_active,
                    "m" : caller.tgl_x_only,
                    "n" : caller.tgl_y_only,
                    "b" : caller.tgl_finetune,
                    },
                "Alt" : {
                    "q" : caller.mlp1.on_off,
                    "w" : caller.mlp2.on_off,
                    "e" : caller.mlp3.on_off,
                    "r" : caller.mlp4.on_off,
                    "a" : caller.pm7.on_off,
                    "s" : caller.grandel.on_off,
                    "d" : caller.delay.on_off,
                    "f" : caller.combo.on_off,
                    "g" : caller.room.on_off,
                 }
            }, "push_keys" :
                { "SHIFT+Q" : caller.mlp1.tgl_active,
                "SHIFT+W" : caller.mlp2.tgl_active,
                "SHIFT+E" : caller.mlp3.tgl_active,
                "SHIFT+R" : caller.mlp4.tgl_active,
                "CTRL+Q" : caller.mlp1.on_off,
                "CTRL+W" : caller.mlp2.on_off,
                "CTRL+E" : caller.mlp3.on_off,
                "CTRL+R" : caller.mlp4.on_off,
                "<"     : caller.pm7.toggle_page,
                "SHIFT+A" : caller.pm7.tgl_active,
                "SHIFT+S" : caller.grandel.tgl_active,
                "SHIFT+D" : caller.delay.tgl_active,
                "SHIFT+F" : caller.combo.tgl_active,
                "SHIFT+G" : caller.room.tgl_active,
                "CTRL+A" : caller.pm7.on_off,
                "CTRL+S" : caller.grandel.on_off,
                "CTRL+D" : caller.delay.on_off,
                "CTRL+F" : caller.combo.on_off,
                "CTRL+G" : caller.room.on_off,
                "Esc"   : caller.deactivate_all, 
                "CapsLock": caller.action_show_numbers,
                "Space": caller.action_machine_onoff,
                "CTRL+Esc" : caller.stop_all
                #"F1|F2|F3|F4" : caller.actionSnapshotRecall #these are set
                #"SHIFT+F1|F2|F3|F4" : caller.actionSnapshotSave #in main script
                }
            }
    return keys
    
def dbp(*msg):
    pass
    #print msg
    
def alert(*msg):
    
    QMessageBox.warning(None, "Larm says:", "".join(msg))
    
