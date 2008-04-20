#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2008 Johannes Burström, <johannes@ljud.org>

import os
import shutil
import re

from larmglobals import alert, getgl

class EasySave(object):
    
    presets = None 
    
    def __init__(self, path = None):
        
        self.path = path or getgl("preset_file")
        self.maybe_load_file()
    
    def maybe_load_file(self):
        
        if self.__class__.presets is not None:
            return
        print "TSERT"
        try:
            f = open(self.path, 'r')
        except IOError:
            alert("IOError: Preset file doesn't exist. \
            A new file is written to %s." % self.path)
            self.__class__.presets = {}
            self.write_file()
        else:
            config_string = f.read()
            try:
                self.__class__.presets = eval(config_string)
            except:
                alert("There's something wrong with the file. \
                A backup is made, and a new file is created")
                shutil.copy(self.path, self.path + "~")
                
                self.__class__.presets = {}
                
    
    def save_preset(self, presetname, param, replace = True):
        """Saves all child items of param as preset
        
        args: Desired preset name, base param, replace = clear preset before update"""        
        if not param.full_address in self.__class__.presets:
            self.__class__.presets[param.full_address] = {}
        
        if not presetname in self.__class__.presets[param.full_address] or replace:
            self.__class__.presets[param.full_address][presetname] = {}
            
        for el in param.queryList("Param"):
            if not el.is_saveable():
                continue
            self.__class__.presets[param.full_address][presetname][el.full_address] = el.get_state()
        
        self.write_file()
        
    def load_preset(self, presetname, param, check = False):
        """Loads a preset into param"""
        #Find the node in question
        try:
            preset = self.__class__.presets[param.full_address][presetname]
        except KeyError:
            self.load_error()
            return
        plist = param.queryList('Param')
        for p in plist:
            try:
                p.set_state(preset[p.full_address])
            except KeyError:
                print "KE"
            
    def delete_preset(self, presetname, param):
        if not self.__class__.presets[param.full_address].pop(presetname, None):
            print "EasySave: Couldn't find preset to delete"
        else:
            self.write_file()
    
    def list_presets(self, param):
        """list all presets of Param.
        
        Returns list of preset names."""
        
        print self.__class__.presets
        try:
            presets = self.__class__.presets[param.full_address].keys()
        except KeyError:
            presets = []
        return presets
    
    def write_file(self):
        try:
            f = open(self.path, 'w')
        except IOError, e:
            alert("Couldn't write to file. %s" % e)
        else:
            p = re.compile("({|},)")
            string = p.sub(r'\1\n', repr(self.__class__.presets))
            f.write(string)
            f.close()
        
    def load_error(self):
        pass
        #FIXME:load_error.check this.
        #alert("Can't load preset. Something has gone terribly wrong, like, for example, you have misplaced the preset file or something. Please check your settings.")
        
    def save_error(self):
        alert("Couldn't save preset file. Please check path, \
            permissions and whatnot.")
    
