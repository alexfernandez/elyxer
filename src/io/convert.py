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
        self.processcontents(lambda container: self.writetoc(container))
      else:
        # generate converted document
        self.processcontents(lambda container: self.writer.write(container.gethtml()))
    except (Exception):
      Trace.error('Conversion failed at ' + self.reader.currentline())
      raise

  def writetoc(self, container):
    "Write the table of contents for a container"
    if hasattr(container, 'number'):
      self.writer.write(container.type + ' ' + container.number + '\n')
    floats = container.searchall(Float)
    for float in floats:
      self.writer.write(float.type + ' ' + float.number + '\n')

  def processcontents(self, process):
    "Parse the contents and process it by containers"
    factory = ContainerFactory()
    postproc = Postprocessor()
    while not self.reader.finished():
      containers = factory.createsome(self.reader)
      for container in containers:
        container = postproc.postprocess(container)
        process(container)

