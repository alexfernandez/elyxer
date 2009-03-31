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


import sys
import codecs
from trace import Trace
from fileline import *
from styles import *
from link import *
from formula import *
from command import *
from table import *
from image import *
from structure import *
from container import *
from options import *
from postprocess import *


class Book(object):
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    factory = ContainerFactory()
    postproc = Postprocessor()
    while not reader.finished():
      container = factory.create(reader)
      result = postproc.postprocess(container)
      writer.write(result.gethtml())

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
    filein = codecs.open(args[0], 'r', "utf-8")
    del args[0]
  if len(args) > 0:
    fileout = codecs.open(args[0], 'w', "utf-8")
    del args[0]
  if len(args) > 0:
    usage('Too many arguments')
    return
  reader = LineReader(filein)
  writer = HtmlWriter(fileout)
  book = Book()
  book.parsecontents(reader, writer)

def usage(error):
  "Show an error message and correct usage"
  if not error:
    return
  Trace.error(error)
  Trace.error('Usage: eLyXer [filein] [fileout].')
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

