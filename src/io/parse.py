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
# Alex 20090203
# eLyXer parsers

import codecs
from util.trace import Trace
from util.options import *


class ParseTree(object):
  "A parsing tree"

  default = '~~default~~'

  def __init__(self, types):
    "Create the parse tree"
    self.root = dict()
    for type in types:
      if hasattr(type, 'start'):
        self.addstart(type, type.start)
      elif hasattr(type, 'starts'):
        for start in type.starts:
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
    branches = [self.root]
    for piece in reader.currentsplit():
      current = branches[-1]
      piece = piece.rstrip('>')
      if piece in current:
        branches.append(current[piece])
    while not ParseTree.default in branches[-1]:
      Trace.error('Line ' + reader.currentline().strip() + ' not found')
      branches.pop()
    last = branches[-1]
    return last[ParseTree.default]

class Parser(object):
  "A generic parser"

  def __init__(self):
    self.begin = 0
    self.parameters = dict()

  def parseheader(self, reader):
    "Parse the header"
    header = reader.currentsplit()
    reader.nextline()
    self.begin = reader.linenumber + 1
    return header

  def parseparameter(self, reader):
    "Parse a parameter"
    split = reader.currentline().strip().split(' ', 1)
    reader.nextline()
    if len(split) == 0:
      return
    key = split[0]
    if len(split) == 1:
      self.parameters[key] = True
      return
    if not '"' in split[1]:
      self.parameters[key] = split[1].strip()
      return
    doublesplit = split[1].split('"')
    self.parameters[key] = doublesplit[1]

  def __str__(self):
    "Return a description"
    return self.__class__.__name__ + ' (' + self.begin + ')'

class LoneCommand(Parser):
  "A parser for just one command line"

  def parse(self,reader):
    "Read nothing"
    return []

class TextParser(Parser):
  "A parser for a command and a bit of text"

  endings = ['\\end_layout', '\\end_inset', '\\emph', '\\family', '\\noun',
      '\\color', '\\size', '\\series']

  def parse(self, reader):
    "Parse lines as long as they are text"
    contents = []
    while not self.isending(reader):
      container = self.factory.create(reader)
      contents.append(container)
    return contents

  def isending(self, reader):
    "Check if text is ending"
    current = reader.currentsplit()
    if len(current) == 0:
      return True
    return current[0] in TextParser.endings

class ExcludingParser(Parser):
  "A parser that excludes the final line"

  def parse(self, reader):
    "Parse everything up to (and excluding) the final line"
    contents = []
    while not reader.currentnonblank().startswith(self.ending):
      container = self.factory.create(reader)
      contents.append(container)
    return contents

class BoundedParser(ExcludingParser):
  "A parser bound by a final line"

  def parse(self, reader):
    "Parse everything, including the final line"
    contents = ExcludingParser.parse(self, reader)
    # skip last line
    reader.nextline()
    return contents

class BoundedDummy(Parser):
  "A bound parser that ignores everything"

  def parse(self, reader):
    "Parse the contents of the container"
    while not reader.currentline().startswith(self.ending):
      reader.nextline()
    # skip last line
    reader.nextline()
    return []

class StringParser(Parser):
  "Parses just a string"

  def parseheader(self, reader):
    "Do nothing, just take note"
    self.begin = reader.linenumber + 1
    return []

  def parse(self, reader):
    "Parse a single line"
    contents = [reader.currentline()]
    reader.nextline()
    return contents

class InsetParser(BoundedParser):
  "Parses a LyX inset"

  def parse(self, reader):
    "Parse inset parameters into a dictionary"
    while reader.currentline() != '\n' and not reader.currentline().startswith('\\'):
      self.parseparameter(reader)
    return BoundedParser.parse(self, reader)

class HeaderParser(Parser):
  "Parses the LyX header"

  def parse(self, reader):
    "Parse header parameters into a dictionary"
    while not reader.currentline().startswith(self.ending):
      self.parseline(reader)
      reader.nextline()
    # skip last line
    reader.nextline()
    return []

  def parseline(self, reader):
    "Parse a single line as a parameter or as a start"
    line = reader.currentline()
    for key in HeaderParser.openings:
      if line.startswith(key):
        HeaderParser.openings[key](self, reader)
        return
    # no match
    self.parseparameter(reader)

  def parsebranch(self, reader):
    branch = reader.currentline().split()[1]
    reader.nextline()
    subparser = HeaderParser().complete('\\end_branch')
    subparser.parse(reader)
    options = BranchOptions()
    for key in subparser.parameters:
      options.set(key, subparser.parameters[key])
    Options.branches[branch] = options

  def complete(self, ending):
    self.ending = ending
    return self

  openings = {'\\branch':parsebranch}

