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
# Alex 20090131
# eLyXer containers for Lyx data that output HTML

from trace import Trace
from parse import *
from output import *
from general import *


class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

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

  comesnext = classmethod(comesnext)

  def parse(self, reader):
    "Parse by lines"
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
    if not hasattr(self, 'begin'):
      return self.__class__.__name__
    return self.__class__.__name__ + '@' + str(self.begin)

  def escape(self, line, escapes = ContainerConfig.escapes):
    "Escape a line to appear in HTML"
    pieces = escapes.keys()
    # do the '&' first
    pieces.sort()
    for piece in pieces:
      if piece in line:
        line = line.replace(piece, escapes[piece])
    return line

  def searchfor(self, type):
    "Search for an embedded container of a given type recursively"
    for element in self.contents:
      if isinstance(element, Container):
        if isinstance(element, type):
          return element
        result = element.searchfor(type)
        if result:
          return result
    return None

  def restyle(self, type, restyler):
    "Restyle contents with a restyler function"
    i = 0
    while i < len(self.contents):
      element = self.contents[i]
      if isinstance(element, type):
        restyler(self, i)
      if isinstance(element, Container):
        element.restyle(type, restyler)
      i += 1

  def group(self, index, group, isingroup):
    "Group some adjoining elements into a group"
    if index >= len(self.contents):
      return
    if hasattr(self.contents[index], 'grouped'):
      return
    while index < len(self.contents) and isingroup(self.contents[index]):
      self.contents[index].grouped = True
      group.contents.append(self.contents[index])
      self.contents.pop(index)
    self.contents.insert(index, group)

  def remove(self, index):
    "Remove a container but leave its contents"
    container = self.contents[index]
    self.contents.pop(index)
    while len(container.contents) > 0:
      self.contents.insert(index, container.contents.pop())

class BlackBox(Container):
  "A container that does not output anything"

  starts = BlackBoxConfig.starts

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class StringContainer(Container):
  "A container for a single string"

  start = ''

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.escape(line)
    replaced = self.changeline(replaced)
    self.contents = [replaced]
    if '\\' in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Unknown command at ' + str(self.parser.begin) + ': '
          + replaced.strip())

  def changeline(self, line):
    line = self.replacemap(line, ContainerConfig.replaces)
    if not '\\' in line:
      return line
    line = self.replacemap(line, ContainerConfig.commands)
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
    self.parser = InsetParser()
    self.output = EmptyOutput()

class TaggedText(Container):
  "Text inside a tag"

  def __init__(self):
    self.parser = TextParser()
    self.output = TaggedOutput()

  def complete(self, contents, tag, breaklines=False):
    "Complete the tagged text and return it"
    self.contents = contents
    self.tag = tag
    self.breaklines = breaklines
    return self

  def constant(self, text, tag):
    "Complete the tagged text with a constant"
    constant = Constant(text)
    return self.complete([constant], tag)

  def __str__(self):
    return 'Tagged <' + self.tag + '>'

class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox, LangLine, StringContainer, ERT]

  def __init__(self):
    self.tree = ParseTree(ContainerFactory.types)

  def create(self, reader):
    "Get the container and parse it"
    #Trace.debug('processing "' + reader.currentline() + '"')
    type = self.tree.find(reader)
    container = type.__new__(type)
    container.__init__()
    container.factory = self
    container.parse(reader)
    return container

