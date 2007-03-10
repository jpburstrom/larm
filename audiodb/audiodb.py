#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from sqlobject import *
import sys, os, fnmatch, string
import FileHasher

__all__ = ["AudioDb"]

db_filename = os.path.abspath('data.db')
#if os.path.exists(db_filename):
#    os.unlink(db_filename)
connection_string = 'sqlite://' + db_filename
connection = connectionForURI(connection_string)
sqlhub.processConnection = connection

class dbSoundFiles(SQLObject):
    fullPath = StringCol()
    hash = StringCol(length=32)
    active = BoolCol(default=True)
    tags = RelatedJoin('dbTags')

class dbTags(SQLObject):
    name = StringCol()
    dbSoundFiles = RelatedJoin('dbSoundFiles')

class AudioDb:
    """ methods for creating, modifying and reading a database of sound files """

    filepath = ['.', "/mnt/magnum/_BACKUP/mobile/home/samples"]  # Change this to your audio file directories

    def __init__(self, path='data.db'):
    
        db_filename = os.path.abspath(path)
        #if os.path.exists(db_filename):
        #    os.unlink(db_filename)
        connection_string = 'sqlite://' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection
    
    def getch(self, msg=False): 
    # Emulates mscvt.getch(), from win32 python. I'm *sure* this is meant to be in
    # curses, but I can't find it... 
        if msg:
            print msg
        import tty
        fd = sys.stdin.fileno()
        tty_mode = tty.tcgetattr(fd)
        tty.setcbreak(fd)
        try: ch = os.read(fd, 1)
        finally: tty.tcsetattr(fd, tty.TCSAFLUSH, tty_mode)
        return ch

    def locate(self, pattern, root=os.curdir):
        '''Locate all files matching supplied filename pattern in and below
        supplied root directory.'''
        for root in self.filepath:
            for path, dirs, files in os.walk(os.path.abspath(root)):
                for filename in fnmatch.filter(files, pattern):
                    yield os.path.join(path, filename)
    def printdelimiter(self):
        """Print a silly delimiter for easier view"""
        print "=========================="

    def listfiles(self):
        """Print out all files in database as well as return all file objects"""
        fileObjs = dbSoundFiles.select()
        i = 0
        filelist = []
        for fileObj in fileObjs:
            print "%d > %s" % (i, fileObj.fullPath)
            i += 1
        return fileObjs


    def listtags(self, hash=None):
        """ returns tags for all or one certain soundfile. One: hash as arg, All: no arg
        """
        if hash:
            tags = dbSoundFiles.select(dbSoundFiles.q.hash==hash)[0].tags
        else:
            tag = dbTags.select()
            tags = list(tag)
        i = 0
        taglist = []
        for tag in tags:
            taglist.append(`i`+' ' +tag.name+ ' || ')
            i += 1
        print "".join(taglist)
        return tags

    def settags(self, fileObj):
        """Set tags for a certain file. Arg: dbSoundFiles object"""
        print "Set tags for " + fileObj.fullPath
        self.playsoundfile(fileObj.fullPath)
        taglist=[]
        for tag in fileObj.tags:
            taglist.append(tag.name)
        print "Current tags: " + " ".join(taglist)
        print "Available tags:"
        availTags = self.listtags()
        resp = raw_input("Add space separated tags or tag numbers. Prepend list with '-' to delete tags. Press Enter to exit): ")
        if resp != '':
            resplist = resp.split(' ')
            delete = False
            for tagname in resplist:
                if tagname == '-':
                    delete = True
                    continue
                if tagname.isdigit():
                    newtag = availTags[int(tagname)].name
                else:
                    newtag = string.lower(tagname)
                exists = False
                for tag in availTags:
                    if tag.name == newtag:
                        tag1 = tag
                        exists = True
                if not exists and not delete:
                    tag1 = dbTags(name=newtag)
                if not tag1 in fileObj.tags:
                    fileObj.addDbTags(tag1)
                    print "%s added" % tag1.name
                elif tag1 in fileObj.tags and delete:
                    fileObj.removeDbTags(tag1)
                    print "%s deleted" % tag1.name

    def selectfilestotag(self):
        """Menu for selecting files to tag, and maintaining the collection of tags"""
        while True:
            print "<1> Edit all files"
            print "<2> Edit all untagged files"
            print "<3> Edit specific file"
            print "<4> Delete specific tag"
            print "<5> Rename specific tag"
            print "... or leave empty to exit."
            resp = self.getch()
            if resp.isdigit():
                if 0 < int(resp) <= 5:
                    choice = int(resp)
                if choice == 1:
                    for file in dbSoundFiles.select():
                        self.settags(file)
                elif choice == 2:
                    p = "No files to edit"
                    for file in dbSoundFiles.select():
                        if not file.tags:
                            self.settags(file)
                            p = ""
                    print p
                elif choice == 3:
                    fileObjs = self.listfiles()
                    resp = self.getch("Select file to edit: ")
                    if resp.isdigit():
                        self.settags(fileObjs[int(resp)])
                elif choice == 4:
                    tags = self.listtags()
                    resp = raw_input("Select tag(s) to DELETE (space separated): ").split(' ')
                    for r in resp:
                        if r.isdigit():
                            files = dbSoundFiles.select()
                            for f in files:
                                f.removeDbTags(tags[int(r)])
                            tags[int(r)].delete(tags[int(r)].id)
                            print "Tag %s deleted." % tags[int(r)].name 
                elif choice == 5:
                    tags = self.listtags()
                    resp = raw_input("Select tag(s) to rename (space separated): ").split(' ')
                    for r in resp:
                        if r.isdigit():
                            r = int(r)
                            oldname = tags[r].name
                            new = string.lower(raw_input("New tag name: ").split(' ')[0])
                            tags[r].name = new 
                            print "Tag %s renamed to %s" % (oldname, new)
            else:
                break 
        
    def rescandirectory(self):
        """Check for new files in directory and update paths and stuff."""
        print "Rescanning directory/ies"
        existingfiles = [] # list of files in db
        for file in dbSoundFiles.select():
            #print file #DEBUG
            existingfiles.append(file)

        filehashdict = {} # files currently on disk
        files = self.locate('*.wav')
        for file in files:
            print "Found " + file
            h = FileHasher.readfile(file)
            filehashdict[h] = file

        for file in existingfiles: 
            if file.hash in filehashdict: 
                print file.fullPath +": activated" 
                file.active = True 
                file.fullPath = filehashdict[file.hash]
                filehashdict.pop(file.hash) 
            else:
                print file.fullPath +": deactivated" 
                file.active = False

        for hash in filehashdict: # insert new files into db
            fileObj = dbSoundFiles(fullPath=filehashdict[hash], hash=hash)
            print filehashdict[hash] + ": activated and inserted" 
            self.settags(fileObj)

                
    ##function: find soundfiles based on tags
    def alltags(self):
        tagObj = dbTags.select()
        tl = []
        for tag in tagObj:
            tl.append(tag.name)
        return tl



    def findfilesfromtag(self, tag):
        tagObj = dbTags.select(dbTags.q.name==tag)
        fl = []
        for tag in tagObj:
            for t in tag.dbSoundFiles: fl.append(t.fullPath)
        return fl


    def playsoundfile(self, file):
        k = True
        while k is True:
            p = os.spawnvp(os.P_NOWAIT, 'aplay',  ('aplay', '-q', file))
            i = self.getch()
            os.kill(p, 15)
            if i == 'p':
                k = True
            else:
                k = False

#Main Loop

if __name__ == '__main__':  
    while True:
        print "Soundfile tagger. Please choose:"
        print "<1> Rescan directory"
        print "<2> Edit tags"
        print "<3> View tags and info for soundfiles"
        print "<4> Exit"
        print "<0> Recreate Tables"
        adb = AudioDb()
        #adb.alltags()
        resp = adb.getch()
        if resp.isdigit():
            if 0 < int(resp) <= 5:
                choice = int(resp)
                if choice == 1:
                    adb.rescandirectory()
                elif choice == 2:
                    adb.selectfilestotag()
                elif choice == 3:
                    fileObjs = adb.listfiles()
                    resp = adb.getch("Select file to view info about: ")
                    f = list(fileObjs)
                    if resp.isdigit() and int(resp) < len(f):
                        f = []
                        f.append(fileObjs[int(resp)])
                    adb.printdelimiter()
                    for fileObj in f:
                        tl = []
                        for t in fileObj.tags: tl.append(t.name)
                        print "Path: %s \nActive: %s\nTags: %s\nHash: %s" % (fileObj.fullPath, fileObj.active, " ".join(tl), fileObj.hash)
                        adb.printdelimiter()
                        adb.getch()

                elif choice == 0:
                    dbSoundFiles.dropTable(ifExists=True, dropJoinTables=True)
                    dbTags.dropTable(ifExists=True, dropJoinTables=True)
                    dbSoundFiles.createTable()
                    dbTags.createTable()
                    print "Tables created."

                elif choice == 4:
                    sys.exit()
