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

  def create(self, container):
    "Create the TOC entry for a container, consisting of a single link."
    text = TranslationConfig.constants[container.type] + ' ' + container.number
    text += ':' + self.gettitle(container) + '\n'
    url = Options.toctarget + '#toc-' + container.type + '-' + container.number
    self.contents = [Link().complete(text, url=url)]
    self.output = TaggedOutput().settag('div class="toc"', True)
    self.depth = 0
    if container.type in TOCEntry.ordered:
      self.depth = TOCEntry.ordered.index(container.type) + 1
      Trace.debug('Depth: ' + unicode(self.depth))
    elif not container.type in TOCEntry.unique:
      Trace.error('Unknown numbered container type ' + container.type)
    return self

  def gettitle(self, container):
    "Get the title of the container."
    if len(container.contents) < 2:
      return '-'
    withoutlabel = TaggedText().complete(container.contents[1:], 'x')
    return withoutlabel.extracttext()

class Indenter(object):
  "Manages and writes indentation for the TOC."

  def __init__(self, writer):
    self.depth = 0
    self.writer = writer

  def indent(self, depth):
    "Indent the line according to the given depth."
    if depth > self.depth:
      self.openindent(depth - self.depth)
    elif depth < self.depth:
      self.closeindent(self.depth - depth)
    self.depth = depth

  def openindent(self, times):
    "Open the indenting div a few times."
    for i in range(times):
      self.writer.writeline('<div class="tocindent">')

  def closeindent(self, times):
    "Close the indenting div a few times."
    for i in range(times):
      self.writer.writeline('</div>')

