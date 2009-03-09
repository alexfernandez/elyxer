#!/usr/bin/python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090203
# eLyXer parsers

import codecs
from trace import Trace


class ParseTree:
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
    tree[ParseTree.default] = type

  def find(self, reader):
    "Find the current sentence in the tree"
    tree = self.root
    for piece in reader.currentsplit():
      piece = piece.rstrip('>')
      if piece in tree:
        tree = tree[piece]
    if not ParseTree.default in tree:
      Trace.error('Line ' + reader.currentline().strip() + ' not found')
    return tree[ParseTree.default]

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
    while not reader.currentline().startswith(self.ending):
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

class ImageCommand(BoundedParser):
  "Parses an image command"

  def parseheader(self, reader):
    "Skip one line, parse next line"
    reader.nextline()
    return reader.currentsplit()

class NamedCommand(BoundedParser):
  "Parses a command with a name"

  def parseheader(self, reader):
    "Skip one line, parse text in quotes"
    reader.nextline()
    header = reader.currentline().split('"')
    self.name = header[1]
    self.key = self.name.replace(' ', '-')
    return header

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

