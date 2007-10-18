# py/pyext - python script objects for PD and MaxMSP
#
# Copyright (c) 2002-2005 Thomas Grill (gr@grrrr.org)
# For information on usage and redistribution, and for a DISCLAIMER OF ALL
# WARRANTIES, see the file, "license.txt," in this distribution.  
#

"""This is an example script for the py/pyext object's basic functionality.

pyext Usage:
- Import pyext

- Inherit your class from pyext._class

- Specfiy the number of inlets and outlets:
    Use the class members (variables) _inlets and _outlets
    If not given they default to 1
    You can also use class methods with the same names to return the respective number

- Constructors/Destructors
    You can specify an __init__ constructor and/or an __del__ destructor.
    The constructor will be called with the object's arguments

    e.g. if your PD or MaxMSP object looks like
    [pyext script class arg1 arg2 arg3]

    then the __init__(self,*args) function will be called with a tuple argument
    args = (arg1,arg2,arg3) 
    With this syntax, you will have to give at least one argument.
    By defining the constructor as __init__(self,*args) you can also initialize 
    the class without arguments.

- Methods called by pyext
    The general format is 'tag_inlet(self,arg)' resp. 'tag_inlet(self,*args)':
        tag is the PD or MaxMSP message header.. either bang, float, list etc.
        inlet is the inlet (starting from 1) from which messages are received.
        args is a tuple which corresponds to the content of the message. args can be omitted.

    The inlet index can be omitted. The method name then has the format 'tag_(self,inlet,args)'.
    Here, the inlet index is a additional parameter to the method

    You can also set up methods which react on any message. These have the special forms
        _anything_inlet(self,*args)
    or
        _anything_(self,inlet,*args) 

    Please see below for examples.

    Any return values are ignored - use _outlet (see below).

    Generally, you should avoid method_, method_xx forms for your non-pyext class methods.
    Identifiers (variables and functions) with leading underscores are reserved for pyext.

- Send messages to outlets:
    Use the inherited _outlet method.
    You can either use the form
        self._outlet(outlet,arg1,arg2,arg3,arg4) ... where all args are atoms (no sequence types!)
    or
        self._outlet(outlet,arg) ... where arg is a sequence containing only atoms

- Use pyext functions and methods: 
    See the __doc__ strings of the pyext module and the pyext._class base class.

"""

try:
    import pyext
except:
    print "ERROR: This script must be loaded by the PD/Max pyext external"

import wave

#################################################################

class bufcheck(pyext._class):
    """Example of a simple class which receives messages and writes to outlets"""

    def __init__(self,*args):
        self.container = {}
        self.counter = 0

    # number of inlets and outlets
    _inlets=1
    _outlets=2

    def check_1(self,*args):
        path = str(args[0])
        pathlist = path.split("/")
        buffer = "".join(("/", pathlist[-1])) 
        try:
            self._outlet(1, [path, self.container[path]]) #check if sample is loaded. if so,  put it in the first outlet
        except KeyError:
            if len(pathlist) > 2:
                self._outlet(2, [path, "".join((pathlist[-1], str(self.counter)))]) #if path is a real file path, put it in the second outlet for loading.
                self.counter += 1
            else:
                self.container[path] = path  #if path is in the form /foo, it's already a buffer (as in recording), and should be loaded directly.
                self._outlet(1, path) 
    
    def store_1(self, *args):
        path = str(args[0])
        buffer = str(args[1])
        self.container[path] = buffer
    
    def debugprint_(self, *args):
        print "===bufcheck contents:==="
        for key, val in self.container.items():
            print key, val


class wavlength(pyext._class):
    """This is a simple class with one method looping over time."""

    # number of inlets and outlets
    _inlets=1
    _outlets=1

    def read_1(self,*args):
        self._detach(1)
        #self._priority(1)
        try:
            f = wave.open(str(args[0]), "r")
        except IOError:
            print "wavlength: No such file"
        else:
            p = int(f.getnframes())
            self._outlet(1,[args[0], args[1], p])

class seq(pyext._class):
    """simple arpeggiator sequencer"""

    def __init__(self,*args):
        self.notes = []
        self.index = 0

    # number of inlets and outlets
    _inlets=1
    _outlets=1

    def list_1(self,*args):
        if args[1] and args[0] not in self.notes:
            self.notes.append(args[0])
        elif not args[1] and args[0] in self.notes:
            self.notes.remove(args[0])

    def bang_1(self):
        if self.notes:
            self.index += 1
            try:
                f = self.notes[self.index]
            except IndexError:
                self.index = 0
                f = self.notes[0]
            self._outlet(1,f)


class wavememory(pyext._class):

    _inlets=1
    _outlets=1
    
    def __init__(self,*args):
        try:
            self.__class__.waves = self.__class__.waves
        except AttributeError:
            self.__class__.waves = {}

    def add_1(self, *args):
        self.__class__.waves[str(args[0])] = args[1]

    def get_1(self, *args):
        try:
            self._outlet(1, self.__class__.waves[str(args[0])])
        except KeyError:
            self._outlet(1, [])

    def del_1(self, *args):
        try:
            self.__class__.waves.pop(str(args[0]))
        except KeyError:
            pass
    
    def print_1(self):
        for k, v in self.__class__.waves.items():
            print k, v
        
