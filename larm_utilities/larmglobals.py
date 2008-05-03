# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"

from qt import QColor, QAction, QKeySequence, QMessageBox
import sys
from os import path
#from xmlsave import XmlSaving

gl = {
    "pdcommand" : "".join([sys.path[0],  "/backend/immer2-back-s2-lomem.pd"]), #file to launch
    "polltime" : 0.04, #ms, how often mouse gets polled
    "mouse_resolution" : 3000, #some kind of resolution factor, larger = slower
    "osc_address" : "127.0.0.1", 
    "osc_port" : 9000, #port for sending osc msgs
    "osc_listen_port" : 9001, #port for receiving osc
    "mouse_device" : "/dev/input/event101", #path to mouse device. you may need r/w permissions...
    "audiodb_path" : 'audiodb/data.db', #relative (to script) or absolute path to audiofile db
    "samplerate" : 48000, #samplerate of backend, needed to calculate rec buffer labels 
    "txtfile" : path.expanduser("~/.larm/notes.txt"), #file with notes
    "preset_file" : path.expanduser('~/.larm/presets.py'),
    "accordion_mode" : 0
}

settings_file = path.expanduser('~/.larm/larmrc')

def generate_settings():
    try:
        f = open(settings_file, "w")
    except IOError:
        print "Couldn't open settings file"
    else:
        f.write("#This is python code. Make sure you keep it readable.\n")
        f.write(repr(gl).replace(",",",\n").replace("{", "{\n"))
        f.close()

try:
    f = open(settings_file, "r")
except IOError:
    generate_settings()    
else:
    settings = f.read()
    f.close()
    try:
        ggl = eval(settings)
    except:
        print "Couldn't read larmrc"
    else:
        gl.update(ggl)

def getgl(key):
    """Get basic settings for the program
    
    Instead of relying on a complex xml or qt setting setup, 
    this is an oldschool python dictionary serving basic settings.
    
    Arg: dict key"""    
    
    return gl[key]
    
def get_keyboard(caller):
    """A function serving keyboard shortcuts
    
    This function returns a python dictionary with key/method pairs. The methods 
    may be on/off toggles and stuff, called from the main class.
    
    Arg: Calling class instance"""
    
    keys = {"tgl_keys" : 
        #these are functions taking 1/0 as argument, for keyboard press/release.
                {"nomod" : {
                    "q" : caller.mlp1.tgl_active,
                    "w" : caller.mlp2.tgl_active,
                    "e" : caller.mlp3.tgl_active,
                    "r" : caller.mlp4.tgl_active,
                    "t" : caller.pm7.tgl_active,
                    "a" : caller.grandel.tgl_active,
                    "s" : caller.delay.tgl_active,
#                    "d" : caller.spectrldly.tgl_active,
                    "f" : caller.combo.tgl_active,
                    "g" : caller.room.tgl_active,
                    "x" : caller.tgl_x_only,
                    "z" : caller.tgl_y_only,
                    "c" : caller.tgl_finetune,
                    },
                "Alt" : {
                    "q" : caller.mlp1.on_off,
                    "w" : caller.mlp2.on_off,
                    "e" : caller.mlp3.on_off,
                    "r" : caller.mlp4.on_off,
                    "t" : caller.pm7.on_off,
                    "a" : caller.grandel.on_off,
                    "s" : caller.delay.on_off,
#                    "d" : caller.spectrldly.on_off,
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
                "Ctrl+Tab"     : caller.pm7.toggle_page,
                #"Tab"     : caller.switch_middle_stack,
                "SHIFT+T" : caller.pm7.tgl_active,
                "SHIFT+A" : caller.grandel.tgl_active,
                "SHIFT+S" : caller.delay.tgl_active,
#               "SHIFT+D" : caller.spectrldly.tgl_active,
                "SHIFT+F" : caller.combo.tgl_active,
                "SHIFT+G" : caller.room.tgl_active,
                "CTRL+T" : caller.pm7.on_off,
                "CTRL+A" : caller.grandel.on_off,
                "CTRL+S" : caller.delay.on_off,
#               "CTRL+D" : caller.spectrldly.on_off,
                "CTRL+F" : caller.combo.on_off,
                "CTRL+G" : caller.room.on_off,
                "Esc"   : caller.deactivate_all, 
                "Tab": caller.action_show_numbers,
                "Space": caller.action_machine_onoff,
                "CTRL+Esc" : caller.stop_all,
                "CTRL+V"     : caller.toggle_piano_mode
                #"F1|F2|F3|F4" : caller.actionSnapshotRecall #these are set
                #"SHIFT+F1|F2|F3|F4" : caller.actionSnapshotSave #in main script
                }
            }
    return keys
    
def dbp(*msg):
    """A simple and unused debug print function.
    
    Args: message to print."""
    pass
    #print msg
    
def alert(*msg):
    """A simple alert box.
    
    Args: message to display"""
    QMessageBox.warning(None, "Larm says:", "".join(msg))
    
