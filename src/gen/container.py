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

from util.trace import Trace
from parse.parser import *
from io.output import *
from conf.config import *


class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  def process(self):
    "Process contents"
    pass

  def gethtml(self):
    "Get the resulting HTML"
    html = self.output.gethtml(self)
    if isinstance(html, basestring):
      Trace.error('Raw string ' + html)
    if Options.html:
      for index, piece in enumerate(html):
        piece = piece.replace('/>', '>')
        html[index] = piece
    return html

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

  def searchall(self, type):
    "Search for all embedded containers of a given type"
    list = []
    for element in self.contents:
      if isinstance(element, Container):
        if isinstance(element, type):
          list.append(element)
        list += element.searchall(type)
    return list

  def restyle(self, type, restyler):
    "Restyle contents with a restyler function"
    for index, element in enumerate(self.contents):
      if isinstance(element, type):
        restyler(self, index)
      if isinstance(element, Container):
        element.restyle(type, restyler)

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

  def debug(self, level = 0):
    "Show the contents in debug mode"
    #if not Trace.debugmode:
    #  return
    Trace.debug('  ' * level + unicode(self))
    for element in self.contents:
      if isinstance(element, Container):
        element.debug(level + 1)

class BlackBox(Container):
  "A container that does not output anything"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()
    self.contents = []

class StringContainer(Container):
  "A container for a single string"

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.escape(line)
    replaced = self.changeline(replaced)
    self.contents = [replaced]
    if ContainerConfig.string['startcommand'] in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Unknown command at ' + str(self.parser.begin) + ': '
          + replaced.strip())

  def changeline(self, line):
    line = self.replacemap(line, ContainerConfig.replaces)
    if not ContainerConfig.string['startcommand'] in line:
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

class TaggedText(Container):
  "Text inside a tag"

  def __init__(self):
    ending = None
    if self.__class__.__name__ in ContainerConfig.endings:
      ending = ContainerConfig.endings[self.__class__.__name__]
    self.parser = TextParser(ending)
    self.output = TaggedOutput()

  def complete(self, contents, tag, breaklines=False):
    "Complete the tagged text and return it"
    self.contents = contents
    self.output.tag = tag
    self.output.breaklines = breaklines
    return self

  def constant(self, text, tag, breaklines=False):
    "Complete the tagged text with a constant"
    constant = Constant(text)
    return self.complete([constant], tag, breaklines)

  def __str__(self):
    return 'Tagged <' + self.output.tag + '>'

