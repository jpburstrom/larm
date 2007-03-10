from qt import *

class Saving:
    def __init__(self, path=''):
        self.basepath = "/larm"
        self.path = self.basepath+path
    
    def save(self, state):
        self.s = QSettings()
        self.s.setPath("ljud.org", "soundcanvas", QSettings.User)
        self.s.beginGroup(self.path)
        for k, v in state.items():
            self.s.writeEntry(k.replace("/", "+"), v)
        self.s.endGroup()
    
    def ls(self):
        self.s = QSettings()
        self.s.setPath("ljud.org", "soundcanvas", QSettings.User)
        return self.s.entryList(self.path)
  
#OBSOLETE?:  
    def lsr(self, path = None):
        if path is None:
            self.q = QSettings()
            path = self.path
            self.val_list = [ ]
        map(self.lsr, [path + "/" +  k for k in self.q.subkeyList(path)])
        self.q.beginGroup(path)
        map( self.val_list.append, [(QString(path + "/" ), i, 
            self.getvalue2(self.q, i)) for i in self.q.entryList("")])
        self.q.endGroup()
        return self.val_list
    
    def getdirs(self):
        self.s = QSettings()
        return self.s.subkeyList(self.path)
    
    def cd(self, dir):
        self.path = self.basepath+dir
    
    def getvalues(self, keys):
        self.s = QSettings()
        self.s.beginGroup(self.path)
        temp = {}
        for key in keys:
            v = self.s.readDoubleEntry(key)
            if v[1]:
                temp[key] = v[0]
                continue
            else:
                v = self.s.readEntry(key)
                if v[1]:
                    temp[key] = v[0]
                    continue
        return temp

#OBSOLETE?:                        
    def getvalue2(self, inst, key):
        v = inst.readNumEntry(key)
        if v[1]:
            return v[0]
        else:
            v = inst.readDoubleEntry(key)
            if v[1]:
                return v[0]
            else:
                v = inst.readEntry(key)
                if v[1]:
                    return v[0]
    
if __name__ == "__main__":
    c = Saving("/mouselooper")
    s = QSettings
    print c.path
    print c.lsr()
