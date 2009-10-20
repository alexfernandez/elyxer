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
from gen.toc import *
from gen.structure import *
from post.postprocess import *
from post.postlist import *
from post.posttable import *
from math.postformula import *


class eLyXerConverter(object):
  "Converter for a document in a lyx file"

  latestwriter = None

  def setio(self, ioparser):
    "Set the InOutParser"
    self.reader = LineReader(ioparser.filein)
    self.writer = LineWriter(ioparser.fileout)
    eLyXerConverter.latestwriter = self.writer
    return self

  def reusewriter(self, filein):
    "Convert a new input file, reusing the latest output file."
    "Useful for embedding one document inside another."
    self.reader = LineReader(filein)
    self.writer = eLyXerConverter.latestwriter
    return self

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

class InOutParser(object):
  "Parse in and out arguments"

  def __init__(self):
    self.filein = sys.stdin
    self.parsedin = False
    self.fileout = sys.stdout
    self.parsedout = False

  def parse(self, args):
    "Parse command line arguments"
    self.filein = sys.stdin
    self.fileout = sys.stdout
    if len(args) < 2:
      Trace.quietmode = True
    if len(args) > 0:
      self.filein = args[0]
      del args[0]
      self.parsedin = True
    if len(args) > 0:
      self.fileout = args[0]
      del args[0]
      self.parsedout = True
    if len(args) > 0:
      raise Exception('Unused arguments: ' + unicode(args))
    return self

