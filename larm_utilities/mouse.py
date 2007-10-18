#!/usr/bin/env python

from time import sleep
import  os
import evdev
from copy import copy
import sys,threading, Queue, qt

#ALL OF THIS IS NOW IN MAIN SCRIPT

POLLTIME = 0.02

class MyDevice(evdev.Device):
    def __init__(self, filename):
        evdev.Device.__init__(self, filename)
    def resetRel(self):
        self.axes['REL_X'] = 0
        self.axes['REL_Y'] = 0


class GuiThread(qt.QMainWindow):

  def __init__(self, queue, endcommand, *args):
    qt.QMainWindow.__init__(self, *args)
    self.queue = queue
    self.editor = qt.QMultiLineEdit(self)
    self.setCentralWidget(self.editor)
    self.endcommand = endcommand
    
  def closeEvent(self, ev):
    """
    We just call the endcommand when the window is closed
    instead of presenting a button for that purpose.
    """
    self.endcommand()

  def processIncoming(self):
    """
    Handle all the messages currently in the queue (if any).
    """
    while self.queue.qsize():
      try:
        msg = self.queue.get(0)
        # Check contents of message and do what it says
        # As a test, we simply print it
        self.editor.insertLine(str(msg))
      except Queue.Empty:
        pass
    
class PollingThread:   
    """
    Launch the main part of the GUI and the worker thread. 
    periodicCall and endApplication could reside in the GUI part, 
    but putting them here means that you have all the thread 
    controls in a single place.
    """
    def __init__(self):
        # Create the queue
        self.queue = Queue.Queue()
        # Set up the GUI part
        self.gui=GuiThread(self.queue, self.endApplication)
        self.gui.show()
        # A timer to periodically call periodicCall :-)
        self.timer = qt.QTimer()
        qt.QObject.connect(self.timer, qt.SIGNAL("timeout()"), self.periodicCall)
        # Start the timer -- this replaces the initial call to periodicCall
        self.timer.start(100)
        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        print root
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()
        if not self.running:
            root.quit()
          
    def endApplication(self):
        self.running = 0
    
    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be a 'select()'.
        One important thing to remember is that the thread has to 
        yield control.
        """
        d = MyDevice("/dev/input/event1")
        poll = d.poll
        resetRel = d.resetRel
        put_ = self.queue.put
        while self.running:
            poll()
            put_(d)
            resetRel()
            sleep( POLLTIME)


root = qt.QApplication(sys.argv)
client = PollingThread()
root.setMainWidget(client.gui)
root.exec_loop()
                

