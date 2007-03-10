""" 
	 FileHasher.py 
	 Alessio Saltarin - 2003

	 Usage: python FileHasher.py [file_path] 
	 
"""

import os
import sys
import md5

def readfile(filename):
    f = file(filename,'rb');
    m = md5.new();
    readBytes = 1024; # read 1024 bytes per time
    totalBytes = 0;
    while (readBytes):
        readString = f.read(readBytes);
        m.update(readString);
        readBytes = len(readString);
        totalBytes+=readBytes;
    f.close();
    return m.hexdigest();

if __name__ == '__main__':
    if (len(sys.argv)==2):
        readfile(sys.argv[1]);
    else:
        print "Usage: python FileHasher.py [file_path]\n";
