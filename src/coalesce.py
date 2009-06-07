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
# Alex 20090309
# conflates (unifies) all into one file to generate an executable

import sys
from io.fileline import *
from util.trace import Trace


files = list()

def getreader(filename):
  "Get a reader for lines"
  if filename in files:
    # already parsed; skip
    return None
  files.append(filename)
  return LineReader(filename)

def readargs(args):
  "Read arguments from the command line"
  del args[0]
  if len(args) == 0:
    Trace.error('Usage: coalesce.py filein [fileout]')
    return
  reader = getreader(args[0])
  del args[0]
  fileout = sys.stdout
  if len(args) > 0:
    fileout = args[0]
    del args[0]
  if len(args) > 0:
    Trace.error('Usage: conflate.py filein [fileout]')
    return
  writer = LineWriter(fileout)
  return reader, writer

def conflate(reader, writer):
  "Conflate all Python files used in filein to fileout"
  if not reader:
    return
  while not reader.finished():
    line = reader.currentline()
    if line.startswith('from'):
      filename = line.split()[1].replace('.', '/') + '.py'
      newreader = getreader(filename)
      conflate(newreader, writer)
    else:
      writer.writeline(line)
    reader.nextline()
  reader.close()

reader, writer = readargs(sys.argv)
if reader:
  conflate(reader, writer)
  writer.close()

  

