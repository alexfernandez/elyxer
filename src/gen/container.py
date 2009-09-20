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
      html = [html]
    if Options.html:
      self.escapeall(html, EscapeConfig.html)
    if not Options.unicode:
      self.escapeall(html, EscapeConfig.nonunicode)
    return html

  def escapeall(self, lines, replacements):
    "Escape all lines in an array with the replacements"
    for index, line in enumerate(lines):
      lines[index] = self.escape(line, replacements)

  def escape(self, line, replacements = EscapeConfig.entities):
    "Escape a line with replacements from a map"
    pieces = replacements.keys()
    # do them in order
    pieces.sort()
    for piece in pieces:
      if piece in line:
        line = line.replace(piece, replacements[piece])
    return line

  def searchall(self, type):
    "Search for all embedded containers of a given type"
    list = []
    self.searchprocess(type,
        lambda contents, index: list.append(contents[index]))
    return list

  def searchremove(self, type):
    "Search for all containers of a type and remove them"
    list = []
    self.searchprocess(type,
        lambda contents, index: self.appendremove(list, contents, index))
    return list

  def appendremove(self, list, contents, index):
    "Append to a list and remove from contents"
    list.append(contents[index])
    del contents[index]

  def searchprocess(self, type, process):
    "Search for all embedded containers and process them"
    for index, element in enumerate(self.contents):
      if isinstance(element, Container):
        element.searchprocess(type, process)
      if isinstance(element, type):
        process(self.contents, index)

  def extracttext(self):
    "Search for all the strings and extract the text they contain"
    text = ''
    strings = self.searchall(StringContainer)
    for string in strings:
      text += string.string
    return text

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
    if not Trace.debugmode:
      return
    Trace.debug('  ' * level + unicode(self))
    for element in self.contents:
      if isinstance(element, Container):
        element.debug(level + 1)

  def __unicode__(self):
    "Get a description"
    if not hasattr(self, 'begin'):
      return self.__class__.__name__
    return self.__class__.__name__ + '@' + unicode(self.begin)

class BlackBox(Container):
  "A container that does not output anything"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()
    self.contents = []

class LyXFormat(BlackBox):
  "Read the lyxformat command"

  def process(self):
    "Show warning if version < 276"
    version = int(self.header[1])
    if version < 276:
      Trace.error('Warning: unsupported format version ' + str(version))

class StringContainer(Container):
  "A container for a single string"

  def __init__(self):
    self.parser = StringParser()
    self.output = StringOutput()
    self.string = ''

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    self.contents = []
    replaced = self.escape(line, EscapeConfig.entities)
    replaced = self.changeline(replaced)
    self.string = replaced
    if ContainerConfig.string['startcommand'] in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Unknown command at ' + unicode(self.parser.begin) + ': '
          + replaced.strip())

  def changeline(self, line):
    line = self.escape(line, EscapeConfig.chars)
    if not ContainerConfig.string['startcommand'] in line:
      return line
    line = self.escape(line, EscapeConfig.commands)
    return line
  
  def __unicode__(self):
    result = 'StringContainer@' + unicode(self.begin)
    return result + '(' + unicode(len(self.string)) + ')'

class Constant(StringContainer):
  "A constant string"

  def __init__(self, text):
    self.contents = []
    self.string = text
    self.output = StringOutput()

  def __unicode__(self):
    return 'Constant: ' + self.string

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

  def __unicode__(self):
    return 'Tagged <' + self.output.tag + '>'

