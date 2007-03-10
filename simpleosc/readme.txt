SimpleOSC 0.2

ixi software - 4 July, 2006.
www.ixi-software.net


Changes:
0.2
- in order to make it simpler to use simpleOSC the callBackManager and ouSockets are now
global variables in the oscAPI module so that the user does not have to deal with them. This
makes the API cleaner and more compact. 

0.1.3
- switched licence to LGPL.

0.1.2
- some tiding up

0.1.1
- removed oscController.py to make it more general
- osc.py and oscAPI.py are now a package to make it more compact
- included latest version of OSC.py 


Description:
SimpleOSC is a simple API for the Open Sound Control for Python 
(by Daniel Holth, Clinton McChesney 
--> pyKit.tar.gz file at http://wiretap.stetson.edu
Documentation at http://wiretap.stetson.edu/docs/pyKit/)

The main aim of this implementation is to provide with a simple way to
deal with the OSC implementation that makes life easier to those who
don't have understanding of sockets. This would not be on your screen
without the help of Daniel Holth and the  support of Buchsenhausen, Innsbruck, Austria..

Download page:
www.ixi-software.net/download/simpleosc.html
or go to www.ixi-software.net and get into backyard/code section
Note that simpleOSC is included in Mirra.

License : 
 This library is free software; you can redistribute it and/or modify it under the terms of the Lesser GNU, Lesser General Public License as published by the Free Software Foundation.

This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with this library; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

SimpleOSC contains small parts by others such as OSC.py by Daniel Holtz. Licence and credits are included on those parts from others.

System requirements:
OS X, GNU/Linux, Windows .... with Python installed

How to use:
Check the appTemplate.py example to see how to use it. 

About OSC:
http://cnmat.cnmat.berkeley.edu/OSC/Max/

Files:
appTemplate.py	 the example, run this to see how it works
oscTestpatch.pd	Pure Data example
oscTestPatch.sc	SuperCollider example
oscTestPatch.pat	MAX/MSP example
readme.txt		this file :)
osc folder:
	OSC.py		Daniel Holths OSC implementation
	oscApi.py		Set of functions that simplify the use of Daniels implementation



Feedback:
contact us on www.ixi-software.net
info@ixi-software.net


