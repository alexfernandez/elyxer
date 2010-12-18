#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   eLyXer -- convert LyX source files to HTML output.
#
#   Copyright (C) 2009 Alex Fernández
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# --end--
# Alex 20090509
# eLyXer factory to create and parse containers

from util.trace import Trace
from conf.config import *
from gen.styles import *
from ref.link import *
from ref.label import *
from bib.biblio import *
from ref.index import *
from maths.formula import *
from maths.command import *
from maths.hybrid import *
from gen.table import *
from gen.image import *
from gen.layout import *
from gen.list import *
from gen.inset import *
from gen.notes import *
from gen.float import *
from gen.header import *
from gen.change import *
from maths.array import *
from bib.tex import *
from bib.pub import *
from xtra.newfangle import *
from maths.macro import *
from maths.extracommand import *


class ContainerFactory(object):
  "Creates containers depending on the first line"

  def __init__(self):
    "Read table that convert start lines to containers"
    types = dict()
    for start, typename in ContainerConfig.starts.iteritems():
      types[start] = globals()[typename]
    self.tree = ParseTree(types)

  def createcontainer(self, reader):
    "Parse a single container."
    #Trace.debug('processing "' + reader.currentline().strip() + '"')
    if reader.currentline() == '':
      reader.nextline()
      return None
    container = Cloner.create(self.tree.find(reader))
    container.start = reader.currentline().strip()
    self.parse(container, reader)
    return container

  def parse(self, container, reader):
    "Parse a container"
    parser = container.parser
    parser.parent = container
    parser.ending = self.getending(container)
    parser.factory = self
    container.header = parser.parseheader(reader)
    container.begin = parser.begin
    self.parsecontents(container, reader)
    container.parameters = parser.parameters
    container.parser = None

  def parsecontents(self, container, reader):
    "Parse the contents of a container."
    contents = container.parser.parse(reader)
    if isinstance(contents, basestring):
      # read a string, set as parsed
      container.parsed = contents
      container.contents = []
    else:
      container.contents = contents

  def getending(self, container):
    "Get the ending for a container"
    split = container.start.split()
    if len(split) == 0:
      return None
    start = split[0]
    if start in ContainerConfig.startendings:
      return ContainerConfig.startendings[start]
    classname = container.__class__.__name__
    if classname in ContainerConfig.endings:
      return ContainerConfig.endings[classname]
    if hasattr(container, 'ending'):
      Trace.error('Pending ending in ' + container.__class__.__name__)
      return container.ending
    return None

class ParseTree(object):
  "A parsing tree"

  default = '~~default~~'

  def __init__(self, types):
    "Create the parse tree"
    self.root = dict()
    for start, type in types.iteritems():
      self.addstart(type, start)

  def addstart(self, type, start):
    "Add a start piece to the tree"
    tree = self.root
    for piece in start.split():
      if not piece in tree:
        tree[piece] = dict()
      tree = tree[piece]
    if ParseTree.default in tree:
      Trace.error('Start ' + start + ' duplicated')
    tree[ParseTree.default] = type

  def find(self, reader):
    "Find the current sentence in the tree"
    branches = self.matchline(reader.currentline())
    while not ParseTree.default in branches[-1]:
      branches.pop()
    last = branches[-1]
    return last[ParseTree.default]

  def matchline(self, line):
    "Match a given line against the tree, as deep as possible."
    branches = [self.root]
    for piece in line.split(' '):
      current = branches[-1]
      piece = piece.rstrip('>')
      if piece in current:
        branches.append(current[piece])
      else:
        return branches
    return branches

