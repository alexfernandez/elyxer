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
from util.options import *
from post.postprocess import *
from post.posttable import *
from math.postformula import *
from post.postlist import *
from gen.factory import *


class Book(object):
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    factory = ContainerFactory()
    postproc = Postprocessor()
    while not reader.finished():
      containers = factory.createsome(reader)
      for container in containers:
        container = postproc.postprocess(container)
        writer.write(container.gethtml())

def createbook(args):
  "Read a whole book, write it"
  filein = sys.stdin
  fileout = sys.stdout
  if len(args) < 2:
    Trace.quietmode = True
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

biblio = dict()
args = sys.argv
del args[0]
Options().parseoptions(args)
createbook(args)

