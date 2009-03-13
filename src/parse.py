#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090203
# eLyXer parsers

import codecs
from trace import Trace


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
      Trace.debug('Line ' + reader.currentline().strip() + ' not found')
      branches.pop()
    last = branches[-1]
    return last[ParseTree.default]

class Parser(object):
  "A generic parser"

  def __init__(self):
    self.begin = 0

  def parseheader(self, reader):
    "Parse the header"
    header = reader.currentsplit()
    reader.nextline()
    self.begin = reader.index + 1
    return header

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

class BoundedParser(Parser):
  "A parser bound by a final line"

  def parse(self, reader):
    "Parse the contents of the container"
    contents = []
    while not reader.currentnonblank().startswith(self.ending):
      container = self.factory.create(reader)
      contents.append(container)
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
    self.begin = reader.index + 1
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
    self.parameters = dict()
    if reader.currentline().startswith(self.ending):
      reader.nextline()
      return []
    while reader.currentline() != '\n':
      partitioned = reader.currentline().strip().partition(' ')
      if len(partitioned[1]) == 0:
        Trace.error('Wrong inset parameter "' + reader.currentline().strip() + '"')
        return
      key = partitioned[0]
      self.parameters[key] = partitioned[2].replace('"', '')
      reader.nextline()
    return BoundedParser.parse(self, reader)

class FormulaParser(Parser):
  "Parses a formula"

  def parseheader(self, reader):
    "See if the formula is inlined"
    if reader.currentline().find('$') > 0:
      return ['inline']
    else:
      return ['block']
  
  def parse(self, reader):
    "Parse the formula"
    if reader.currentline().find('$') > 0:
      formula = reader.currentline().split('$')[1]
    else:
      # formula of the form \[...\]
      reader.nextline()
      formula = reader.currentline()[:-3]
    while not reader.currentline().startswith(self.ending):
      reader.nextline()
    reader.nextline()
    return [formula]

