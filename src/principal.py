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
# Alex 20090308
# eLyXer main script
# http://www.nongnu.org/elyxer/


import sys
import os.path
from util.trace import Trace
from io.fileline import *
from gen.styles import *
from ref.link import *
from ref.label import *
from ref.biblio import *
from math.formula import *
from math.command import *
from gen.table import *
from gen.image import *
from gen.structure import *
from gen.container import *
from util.options import *
from post.postprocess import *
from post.posttable import *
from math.postformula import *
from math.array import *


class Book(object):
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    types = ContainerConfig.starts
    for start, typename in types.iteritems():
      types[start] = globals()[typename]
    factory = ContainerFactory(types)
    postproc = Postprocessor()
    while not reader.finished():
      container = factory.create(reader)
      container = postproc.postprocess(container)
      writer.write(container.gethtml())

def createbook(args):
  "Read a whole book, write it"
  filein = sys.stdin
  fileout = sys.stdout
  if len(args) < 2:
    Options.quiet = True
  if len(args) > 0:
    Options.directory = os.path.dirname(args[0])
    if Options.directory == '':
      Options.directory = '.'
    filein = args[0]
    del args[0]
  if len(args) > 0:
    fileout = args[0]
    del args[0]
  if len(args) > 0:
    usage('Too many arguments')
    return
  reader = LineReader(filein)
  writer = LineWriter(fileout)
  book = Book()
  try:
    book.parsecontents(reader, writer)
  except (BaseException, Exception):
    Trace.error('Failed at ' + reader.currentline())
    raise

def usage(error):
  "Show an error message and correct usage"
  if not error:
    return
  Trace.error(error)
  Trace.error('Usage: elyxer.py [filein] [fileout].')
  Trace.error('  Options:')
  Trace.error('    --nocopy: disables the copyright notice at the bottom')
  Trace.error('    --quiet: disables all runtime messages')
  Trace.error('    --debug: enable debugging messages (for developers)')
  Trace.error('    --title <title>: set the generated page title')
  Trace.error('    --css <file.css>: use a custom CSS file')
  exit()

biblio = dict()
args = sys.argv
del args[0]
error = Options().parseoptions(args)
if error:
  usage(error)
  exit()
createbook(args)

