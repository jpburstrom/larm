

from sqlobject import *

try:
    import pyext
except:
    print "ERROR: This script must be loaded by the PD/Max pyext external"


#################################################################

class MessageSeq(pyext._class):


    _inlets=1
    _outlets=1
    
    def __init__(self,*args):
        self.pointer = 0
        self.seq = []
        self.state = 0
        
    def bang_1(self):
        if self.state is 1 and self.seq:
            try:
                l = self.seq[self.pointer]
                self.pointer += 1
            except IndexError:
                l = self.seq[0]
                self.pointer = 1
            self._outlet(1, l)
        
    def _anything_1(self, *args):
        if self.state is 2:
            self.seq.append(args)
    
    def float_1(self, f):
        if f is 2:
            self.seq = []
        self.state = int(f)
    
    def debug_1(self):
        print self.seq
        
