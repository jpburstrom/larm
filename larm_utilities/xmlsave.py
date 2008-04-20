# -*- coding: utf-8 -*-
# Copyright 2007 Johannes Burström, <johannes@ljud.org>
__version__ = "$Revision$"

import shutil
import os
import xml.etree.ElementTree as ET

from xml.parsers.expat import ExpatError


#TEMP
#from jmachine import Param
from larmglobals import alert, getgl

class XmlSaving:
    """A class for saving Param trees into an xml file.
    
    Different class instances shares the same ElementTree, which only loads 
    into memory once. Saving saves directly to disk, but any load operation 
    uses the ElementTree in memory. Look out for changing the preset file while
    the program is running."""
    
    #Place for the ElementTree
    root = None
    """
    
    Create one instance of this, and it will write to file
    whenever you save a preset. Probably wise to keep it in memory
    instead of recalling from disk?!?"""
    def __init__(self):
    
        self.path= getgl("preset_file")
        
        #Check if we've already loaded the xml doc, and 
        if not self.__class__.root:
            self.init_document()

    def init_document(self):
        """Create a new saving document
        
        If file is not present, not valid xml or not starting with <presets>,
        a new file is generated."""
        try:
            tree = ET.parse(self.path)
        except IOError:
            alert("IOError: Preset file doesn't exist. A new file is written to %s." % self.path)
            if not os.path.exists(os.path.dirname(self.path)):
                os.makedirs(os.path.dirname(self.path))
            self.create_new_document()
        except ExpatError:
            alert("ExpatError: Preset file %s is malformed. A backup is made, and a new \
            file is created" % self.path)
            shutil.copy(self.path, self.path + "~")
            self.create_new_document()
        else:
            self.__class__.root = tree.getroot()
            if self.__class__.root.tag != "presets":
                alert("Preset file is well-formed, but doesn't seem to contain our presets. A backup is made, and a new file is created" % self.path)
                shutil.copy(self.path, self.path + "~")
                self.create_new_document()
    
    def create_new_document(self):
        print "Creating new saving document"
        self.__class__.root = ET.Element("presets")
        ET.ElementTree(self.__class__.root).write(self.path)
    
    def save_preset(self, presetname, param, replace = True):
        """Saves all child items of param as preset
        
        args: Desired preset name, base param, replace = clear preset before update"""
        #First try to find the whole path at once
        node = self.__class__.root.find(param.full_save_address[1:])
        #If that fails, go through elements one by one: create new ones if needed
        if node is None:
            node = self.__class__.root
            for add in param.full_save_address.split("/"):
                if len(add) is 0:
                    continue
                else:
                    nunode = node.find(add)
                    if nunode is None:
                        nunode = ET.SubElement(node, add)
                    node = nunode
        #When we've found our base node, try to find an existing preset to update
        preset = None
        for preset in node:
            if preset.get('name') == presetname:
                break
            else:
                preset = None
        #If that fails, create a new preset with supplied name
        if preset is None:
            preset = ET.SubElement(node, "preset")
        #walk through all children of supplied param
        if replace:
            preset.clear()
        preset.set('name', presetname)
        for el in param.queryList("Param"):
            if not el.is_saveable():
                continue
            #extract the relative path of each children
            rel_path = el.full_address[len(param.full_address) + 1:]
            #and try to find the path directly
            node = preset.find(rel_path)
            #Otherwise we do a little dance
            if not node:
                node = preset
                for add in rel_path.split("/"):
                    if len(add) is 0:
                        continue
                    else:
                        nunode = node.find(add)
                        if nunode is None:
                            nunode = ET.SubElement(node, add)
                        node = nunode
            #and set the attrs for the param
            node.set('type', el.type.__name__)
            #node.set('state', "||".join(str(i) for i in el.get_state()))
            if el.type is list:
                node.clear()
                for l in el.get_state():
                    nunode = ET.subelement(9
            else:
                node.set('state', str(el.get_state()))
            
        try:    
            ET.ElementTree(self.__class__.root).write(self.path)
        except IOError:
            self.save_error()
    
    def save_error(self):
        alert("Couldn't save preset file. Please check path, permissions and whatnot.")
        
        
    def load_preset(self, presetname, param, check = False):
        """Loads a preset into param"""
        #Find the node in question
        if not isinstance(presetname, ET._ElementInterface):
            node = self.__class__.root.find(param.full_save_address[1:])
            if not node:
                self.load_error()
                return
            presets = None
            #See if we have any presets
            presets = node.findall("preset")
            if not presets:
                self.load_error()
                return
            #and check if our preset is present
            for preset in presets:
                if preset.get('name') == presetname:
                    break
            if not preset:
                self.load_error()
            #find all children of supplied param
            if check:
                return preset
        else:
            preset = presetname
        plist = param.queryList('Param')
        for p in plist:
            node = preset
            #and for each child, find the state and update.
            pp = node.find(p.full_address[len(param.full_address) + 1:])
            if pp is None or pp.get('type') is None:
                continue
            if pp.get('type') == 'bool':
                state = eval(pp.get('state'))
            elif pp.get('type') == 'list':
                state = pp.get('state').split("||")
                print state
            else:
                state = pp.get('state')
            p.set_state(eval(pp.get('type'))(state))
    
    def check_preset(self, presetname, param):
        return self.load_preset(presetname, param, True)
    
    def delete_preset(self, presetname, param):
        node = self.__class__.root.find(param.full_save_address[1:])
        p = self.load_preset(presetname, param, True)
        node.remove(p)
        try:    
            ET.ElementTree(self.__class__.root).write(self.path)
        except IOError:
            self.save_error()
    
    def list_presets(self, param):
        node = self.__class__.root.find(param.full_save_address[1:])
        if not node:
            self.load_error()
            return
        presets = None
        #See if we have any presets
        presets = node.findall("preset")
        if not presets:
            self.load_error()
            return
        presetlist = [preset.get('name') for preset in presets]
        return presetlist
            
        
    def load_error(self):
        pass
        #FIXME:load_error.check this.
        #alert("Can't load preset. Something has gone terribly wrong, like, for example, you have misplaced the preset file or something. Please check your settings.")
        
if __name__ == "__main__":
    from random import random
    parent = Param(address="/parent")
    p1 = Param(address="/p1")
    p2 = Param(address="/p2.")
    p3 = Param(address="/p3.")
    par = []
    for i in range(10):
        par.append(Param(address="/pp" + str(i)))
        if i > 0:
            par[(i - 1)].insertChild(par[i])
        par[i].set_state(random())
    
    parent.insertChild(par[0])
    parent.insertChild(p2)
    p2.insertChild(p3)
    p2.set_state(22)
    
    s = XmlSaving()
    #s.save_preset("Test preset", parent)    
    #s.save_preset("Test preset2", p2)
    p1.set_state(21)
    p2.set_state(23)
    p3.set_state(400)
    print '///////////////////'
    s.load_preset("Test preset", parent)
    for pk in par:
        print pk.state
    print p1.state
    print p2.state
    print p3.state
