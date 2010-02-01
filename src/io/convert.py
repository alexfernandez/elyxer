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


import os.path
from io.fileline import *
from util.options import *
from gen.factory import *
from gen.toc import *
from gen.inset import *
from gen.basket import *
from gen.integral import *
from post.postprocess import *
from post.postlist import *
from post.posttable import *
from ref.postlink import *
from math.postformula import *


class eLyXerConverter(object):
  "Converter for a document in a lyx file. Places all output in a given basket."

  def __init__(self):
    self.filtering = False

  def setio(self, ioparser):
    "Set the InOutParser"
    self.reader = ioparser.getreader()
    self.basket = self.getbasket()
    self.basket.setwriter(ioparser.getwriter())
    return self

  def getbasket(self):
    "Get the appropriate basket for the current options."
    if Options.toc:
      return TOCBasket()
    if Options.splitpart:
      return SplittingBasket()
    if Options.memory:
      return MemoryBasket()
    return WriterBasket()

  def embed(self, reader):
    "Embed the results from a reader into a memory basket."
    "Header and footer are ignored. Useful for embedding one document inside another."
    self.filtering = True
    self.reader = reader
    self.basket = MemoryBasket()
    self.writer = NullWriter()
    return self

  def convert(self):
    "Perform the conversion for the document"
    try:
      self.processcontents()
    except (Exception):
      version = '[eLyXer version ' + GeneralConfig.version['number']
      version += ' (' + GeneralConfig.version['date'] + ') in '
      version += Options.location + '] '
      Trace.error(version)
      Trace.error('Conversion failed at ' + self.reader.currentline())
      raise

  def processcontents(self):
    "Parse the contents and write it by containers"
    factory = ContainerFactory()
    self.postproc = Postprocessor()
    while not self.reader.finished():
      container = factory.createcontainer(self.reader)
      if container and not self.filtered(container):
        result = self.postproc.postprocess(container)
        if result:
          self.basket.write(result)
    # last round: clear the pipeline
    result = self.postproc.postprocess(None)
    if result:
      self.basket.write(result)
    if not self.filtering:
      self.basket.finish()

  def filtered(self, container):
    "Find out if the container is a header or footer and must be filtered."
    if not self.filtering:
      return False
    if container.__class__ in [LyXHeader, LyXFooter]:
      return True
    return False

  def getcontents(self):
    "Return the contents of the basket."
    return self.basket.contents

  def __unicode__(self):
    "Printable representation."
    string = 'Converter with filtering ' + unicode(self.filtering)
    string += ' and basket ' + unicode(self.basket)
    return string

class InOutParser(object):
  "Parse in and out arguments"

  def __init__(self):
    self.filein = sys.stdin
    self.fileout = sys.stdout

  def parse(self, args):
    "Parse command line arguments"
    self.filein = sys.stdin
    self.fileout = sys.stdout
    if len(args) < 2:
      Trace.quietmode = True
    if len(args) > 0:
      self.filein = args[0]
      del args[0]
      self.readdir(self.filein, 'directory')
    else:
      Options.directory = '.'
    if len(args) > 0:
      self.fileout = args[0]
      del args[0]
      self.readdir(self.fileout, 'destdirectory')
    else:
      Options.destdirectory = '.'
    if len(args) > 0:
      raise Exception('Unused arguments: ' + unicode(args))
    return self

  def getreader(self):
    "Get the resulting reader."
    return LineReader(self.filein)

  def getwriter(self):
    "Get the resulting writer."
    return LineWriter(self.fileout)

  def readdir(self, filename, diroption):
    "Read the current directory if needed"
    if getattr(Options, diroption) != None:
      return
    setattr(Options, diroption, os.path.dirname(filename))
    if getattr(Options, diroption) == '':
      setattr(Options, diroption, '.')

class NullWriter(object):
  "A writer that goes nowhere."

  def write(self, list):
    "Do nothing."
    pass

class ConverterFactory(object):
  "Create a converter fit for converting a filename and embedding the result."

  def create(self, container):
    "Create a converter for a given container, with filename"
    " and possibly other parameters."
    fullname = os.path.join(Options.directory, container.filename)
    reader = LineReader(container.filename)
    if 'firstline' in container.lstparams:
      reader.setstart(int(container.lstparams['firstline']))
    if 'lastline' in container.lstparams:
      reader.setend(int(container.lstparams['lastline']))
    return eLyXerConverter().embed(reader)

IncludeInset.converterfactory = ConverterFactory()

