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
# Alex 20090919
# eLyXer converter
# http://www.nongnu.org/elyxer/


from io.fileline import *
from util.options import *
from gen.factory import *
from gen.structure import *
from post.postprocess import *
from post.postlist import *
from post.posttable import *
from math.postformula import *


class eLyXerConverter(object):
  "Converter for a document in a lyx file"

  def __init__(self, filein, fileout):
    "Create the converter"
    self.reader = LineReader(filein)
    self.writer = LineWriter(fileout)

  def convert(self):
    "Perform the conversion for the document"
    try:
      if Options.toc:
        # generate TOC
        writer = TOCWriter(self.writer)
        self.processcontents(lambda container: writer.writetoc(container))
      else:
        # generate converted document
        self.processcontents(lambda container: self.writer.write(container.gethtml()))
    except (Exception):
      Trace.error('Conversion failed at ' + self.reader.currentline())
      raise

  def processcontents(self, write):
    "Parse the contents and write it by containers"
    factory = ContainerFactory()
    postproc = Postprocessor()
    while not self.reader.finished():
      containers = factory.createsome(self.reader)
      for container in containers:
        container = postproc.postprocess(container)
        write(container)

class TOCWriter(object):
  "A class to write the TOC of a document."

  def __init__(self, writer):
    self.writer = writer
    self.depth = 0
    Options.nocopy = True

  def writetoc(self, container):
    "Write the table of contents for a container."
    if container.__class__ in [LyxHeader, LyxFooter]:
      self.writeheaderfooter(container)
      return
    if not hasattr(container, 'number'):
      return
    self.indent(container)
    title = TranslationConfig.constants[container.type] + ' ' + container.number
    title += ': ' + self.gettitle(container) + '\n'
    url = Options.toc + '#toc-' + container.type + '-' + container.number
    link = Link().complete(title, url=url)
    toc = TaggedText().complete([link], 'div class="toc"', True)
    self.writer.write(toc.gethtml())
    for float in container.searchall(Float):
      self.writer.writeline(float.type + ' ' + float.number + '\n')

  def indent(self, container):
    "Indent the line according to the container type."
    if container.type in NumberingConfig.layouts['unique']:
      depth = 0
    elif container.type in NumberingConfig.layouts['ordered']:
      depth = NumberingConfig.layouts['ordered'].index(container.type) + 1
    else:
      Trace.error('Unknown numbered container ' + container)
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
    index = 1
    while len(container.contents[index].gethtml()) == 0:
      index += 1
    text = ''
    for line in container.contents[index].gethtml():
      text += line
    return text

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

