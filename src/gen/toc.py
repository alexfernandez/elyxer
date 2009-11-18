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

  copied = [StringContainer, Constant, Space]
  allowed = [
      TextFamily, EmphaticText, VersalitasText, BarredText,
      SizeText, ColorText, LangLine, Formula
      ]

  def header(self, container):
    "Create a TOC entry for header and footer (0 depth)."
    self.depth = 0
    self.output = EmptyOutput()
    return self

  def create(self, container):
    "Create the TOC entry for a container, consisting of a single link."
    text = container.entry + ':'
    labels = container.searchall(Label)
    if len(labels) == 0 or Options.toc:
      url = Options.toctarget + '#toc-' + container.type + '-' + container.number
      link = Link().complete(text, url=url)
    else:
      label = labels[0]
      link = Link().complete(text)
      link.setdestination(label)
    self.contents = [link]
    link.contents += self.gettitlecontents(container)
    self.output = TaggedOutput().settag('div class="toc"', True)
    if hasattr(container, 'level'):
      self.depth = container.level
    else:
      self.depth = 0
    return self

  def gettitlecontents(self, container):
    "Get the title of the container."
    shorttitles = container.searchall(ShortTitle)
    if len(shorttitles) > 0:
      contents = [Constant(u' ')]
      for shorttitle in shorttitles:
        contents += shorttitle.contents
      return contents
    return self.safeclone(container).contents

  def safeclone(self, container):
    "Return a new container with contents only in a safe list, recursively."
    clone = Cloner.clone(container)
    clone.output = container.output
    clone.contents = []
    for element in container.contents:
      if element.__class__ in TOCEntry.copied:
        clone.contents.append(element)
      elif element.__class__ in TOCEntry.allowed:
        clone.contents.append(self.safeclone(element))
    return clone

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

