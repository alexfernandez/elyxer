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
# Alex 20091006
# eLyXer TOC generation
# http://www.nongnu.org/elyxer/


from gen.factory import *
from gen.structure import *


class TOCEntry(Container):
  "A container for a TOC entry."

  ordered = NumberingConfig.layouts['ordered']
  unique = NumberingConfig.layouts['unique']
  allowed = [Constant, StringContainer]

  def create(self, container):
    "Create the TOC entry for a container, consisting of a single link."
    text = TranslationConfig.constants[container.type] + ' ' + container.number + ':'
    url = Options.toctarget + '#toc-' + container.type + '-' + container.number
    link = Link().complete(text, url=url)
    self.contents = [link]
    link.contents += self.gettitlecontents(container)
    self.output = TaggedOutput().settag('div class="toc"', True)
    self.depth = 0
    if container.type in TOCEntry.ordered:
      self.depth = TOCEntry.ordered.index(container.type) + 1
    elif not container.type in TOCEntry.unique:
      Trace.error('Unknown numbered container type ' + container.type)
    return self

  def gettitlecontents(self, container):
    "Get the title of the container."
    if len(container.contents) < 2:
      return '-'
    newcontents = []
    for element in container.contents:
      if element.__class__ in TOCEntry.allowed:
        newcontents.append(element)
    return newcontents

class Indenter(object):
  "Manages and writes indentation for the TOC."

  def __init__(self):
    self.depth = 0

  def setwriter(self, writer):
    self.writer = writer

  def indent(self, depth):
    "Indent the line according to the given depth."
    indents = self.getindent(depth)
    for line in indents:
      self.writer.write(line)

  def getindent(self, depth):
    indent = ''
    if depth > self.depth:
      indent = self.openindent(depth - self.depth)
    elif depth < self.depth:
      indent = self.closeindent(self.depth - depth)
    self.depth = depth
    return Constant(indent)

  def openindent(self, times):
    "Open the indenting div a few times."
    indent = ''
    for i in range(times):
      indent += '<div class="tocindent">\n'
    return indent

  def closeindent(self, times):
    "Close the indenting div a few times."
    indent = ''
    for i in range(times):
      indent += '</div>\n'
    return indent

