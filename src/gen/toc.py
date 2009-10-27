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


class TOCWriter(object):
  "A class to write the TOC of a document."

  def __init__(self, writer):
    self.writer = writer
    self.depth = 0
    Options.nocopy = True

  def clone(self, filterheader):
    "Return a cloned copy."
    clone = TOCWriter()
    clone.writer = self.writer
    return clone

  def write(self, container):
    "Write the table of contents for a container."
    if container.__class__ in [LyxHeader, LyxFooter]:
      self.writeheaderfooter(container)
      return
    if not hasattr(container, 'number'):
      return
    self.indent(container.type)
    self.createlink(container.type, container.number, self.gettitle(container))

  def createlink(self, type, number, title):
    "Create the actual link for the TOC."
    text = TranslationConfig.constants[type] + ' ' + number
    text += ':' + title + '\n'
    url = Options.toc + '#toc-' + type + '-' + number
    link = Link().complete(text, url=url)
    toc = TaggedText().complete([link], 'div class="toc"', True)
    self.writer.write(toc.gethtml())

  def indent(self, type):
    "Indent the line according to the container type."
    if type in NumberingConfig.layouts['unique']:
      depth = 0
    elif type in NumberingConfig.layouts['ordered']:
      depth = NumberingConfig.layouts['ordered'].index(type) + 1
    elif not type:
      Trace.error('Empty type')
      return
    else:
      Trace.error('Unknown numbered container type ' + type)
      return
    if depth > self.depth:
      self.openindent(depth - self.depth)
    elif depth < self.depth:
      self.closeindent(self.depth - depth)
    self.depth = depth

  def gettitle(self, container):
    "Get the title of the container."
    if len(container.contents) < 2:
      return '-'
    withoutlabel = TaggedText().complete(container.contents[1:], 'x')
    return withoutlabel.extracttext()

  def writeheaderfooter(self, container):
    "Write the header or the footer."
    if isinstance(container, LyxFooter):
      self.closeindent(self.depth)
    self.writer.write(container.gethtml())

  def openindent(self, times):
    "Open the indenting div a few times."
    for i in range(times):
      self.writer.writeline('<div class="tocindent">')

  def closeindent(self, times):
    "Close the indenting div a few times."
    for i in range(times):
      self.writer.writeline('</div>')

