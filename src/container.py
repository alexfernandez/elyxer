#!/usr/bin/python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090131
# eLyXer containers for Lyx data that output HTML

from trace import Trace
from parse import *
from output import *


class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  @classmethod
  def comesnext(cls, reader):
    "Return if the current line matches"
    line = reader.currentline()
    if hasattr(cls, 'start'):
      return line.startswith(cls.start)
    if hasattr(cls, 'starts'):
      for start in cls.starts:
        if line.startswith(start):
          return True
    return False

  def parse(self, reader):
    "Parse a line reader"
    if hasattr(self, 'ending'):
      self.parser.ending = self.ending
    self.parser.factory = self.factory
    self.header = self.parser.parseheader(reader)
    self.begin = self.parser.begin
    self.contents = self.parser.parse(reader)
    self.process()
    self.parser = []

  def process(self):
    "Process contents"
    pass

  def finished(self, reader):
    "Find out if we are at the end"
    return reader.currentline().startswith(self.ending)

  def gethtml(self):
    "Get the resulting HTML"
    return self.output.gethtml(self)

  def __str__(self):
    "Get a description"
    return self.__class__.__name__ + '@' + str(self.begin)

  escapes = {'&':'&amp;', '<':'&lt;', '>':'&gt;'}

  def escape(self, line):
    "Escape a line to appear in HTML"
    pieces = Container.escapes.keys()
    # do the '&' first
    pieces.sort()
    for piece in pieces:
      if piece in line:
        line = line.replace(piece, Container.escapes[piece])
    return line

  def searchfor(self, check):
    "Search for an embedded element recursively"
    return self.searchinside(self.contents, check)

  def searchinside(self, contents, check):
    "Search for an embedded element in a list"
    for element in contents:
      if isinstance(element, Container):
        if check(element):
          return element
        result = self.searchinside(element.contents, check)
        if result:
          return result
    return None

class BlackBox(Container):
  "A container that does not output anything"

  starts = ['\\lyxformat', '\\begin_document', '\\begin_body',
      '\\end_body', '\\end_document', '\\family default', '\\color inherit',
      '\\shape default', '\\series default', '\\emph off',
      '\\bar no', '\\noun off', '\\emph default', '\\bar default',
      '\\noun default', '\\family roman', '\\series medium',
      '\\shape up', '\\size normal', '\\color none', '#LyX', '\\noindent']

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class StringContainer(Container):
  "A container for a single string"

  start = ''

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()
    
  replaces = { '`':u'‘', '\'':u'’', '\n':'', '--':u'—' }
  commands = { '\\SpecialChar \\ldots{}':u'…', '\\InsetSpace ~':'&nbsp;', '\\backslash':'\\' }

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.escape(line)
    replaced = self.changeline(replaced)
    self.contents = [replaced]
    if '\\' in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Error at ' + str(self.parser.begin) + ': ' + replaced.strip())

  def changeline(self, line):
    line = self.replacemap(line, StringContainer.replaces)
    if not '\\' in line:
      return line
    line = self.replacemap(line, StringContainer.commands)
    return line

  def replacemap(self, line, map):
    for piece in map:
      if piece in line:
        line = line.replace(piece, map[piece])
    return line
  
  def __str__(self):
    length = ''
    descr = ''
    if len(self.contents) > 0:
      length = str(len(self.contents[0]))
      descr = self.contents[0].strip()
    return 'StringContainer@' + str(self.begin) + '(' + str(length) + ')'

class Constant(StringContainer):
  "A constant string"

  def __init__(self, text):
    self.contents = [text]
    self.output = MirrorOutput()

  def __str__(self):
    return 'Constant'

class LangLine(Container):
  "A line with language information"

  start = '\\lang'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

  def process(self):
    self.lang = self.header[1]

class ERT(Container):
  "Evil Red Text"

  start = '\\begin_inset ERT'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = EmptyOutput()

class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox, LangLine, StringContainer, ERT]

  def __init__(self):
    self.tree = ParseTree(ContainerFactory.types)

  def create(self, reader):
    "Get the container and parse it"
    # Trace.debug('processing ' + reader.currentline().strip())
    type = self.tree.find(reader)
    container = type.__new__(type)
    container.__init__()
    container.factory = self
    container.parse(reader)
    return container

