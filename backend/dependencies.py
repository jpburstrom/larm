#!/usr/bin/python

import os
import fnmatch
import re

def locate(pattern, exclude = "", filepath=[os.curdir]):
    '''Locate all files matching supplied filename pattern in and below
            supplied root directory.'''
    for root in filepath:
        for path, dirs, files in os.walk(os.path.abspath(root)):
            if not exclude in path:
                for filename in fnmatch.filter(files, pattern):
                    yield os.path.join(path, filename)

p = re.compile(".*obj\ [0-9]+?\ [0-9]+?\ (.+?)\ ")
objs = {}
bl = open("blacklist", "r")
blacklist = []
for bla in bl:
    blacklist.append(bla[:-1])

for i in locate("*.pd", "/attic"):
    f = open(i, "r")
    for line in f:
        g = p.match(line)
        if g:
            if not os.path.exists("".join([os.path.dirname(i),"/", g.group(1), ".pd"])) \
                and not os.path.exists("".join(["/usr/local/lib/pd/extra/", g.group(1), ".pd_linux"])) \
                    and g.group(1) not in blacklist:
                try:
                    objs[(g.group(1))].add(i)
                except KeyError:
                    objs[(g.group(1))] = set([i])
            else:
                pass

for k, v in objs.items():
    print k, v
#help(fnmatch)
