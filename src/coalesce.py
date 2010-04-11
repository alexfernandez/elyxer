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
# Coalesces (unifies) all into one file to generate an executable

import sys
import os.path
from io.fileline import *
from util.trace import Trace


class Coalescer(object):

  def __init__(self):
    self.comments = True
    self.files = []
    self.directory = ''
  
  def getreader(self, filename, directory = ''):
    "Get a reader for lines"
    if filename in self.files:
      # already parsed; skip
      return None
    self.files.append(filename)
    if not os.path.exists(filename):
      filename = os.path.join(self.directory, filename)
      if not os.path.exists(filename):
        Trace.error('Missing file ' + filename)
        return None
    return LineReader(filename)

  def readargs(self, args):
    "Read arguments from the command line"
    del args[0]
    if len(args) == 0:
      self.usage()
      return
    self.reader = self.getreader(args[0])
    self.directory = os.path.dirname(args[0])
    del args[0]
    fileout = sys.stdout
    if len(args) > 0:
      fileout = args[0]
      del args[0]
    if len(args) > 0:
      usage()
      return
    self.writer = LineWriter(fileout)

  def usage():
    Trace.error('Usage: coalesce.py filein [fileout]')
    return

  def coalesceall(self):
    "Coalesce all files from the root reader."
    self.coalesce(self.reader, self.writer)
    self.writer.close()

  def coalesce(self, reader, writer):
    "Coalesce all Python files used in filein to fileout"
    if not reader:
      return
    while not reader.finished():
      line = reader.currentline()
      if line.startswith('from'):
        self.comments = False
        filename = line.split()[1].replace('.', '/') + '.py'
        newreader = self.getreader(filename)
        self.coalesce(newreader, writer)
      elif line.startswith('#'):
        if self.comments:
          writer.writeline(line)
      else:
        writer.writeline(line)
      reader.nextline()
    reader.close()

coalescer = Coalescer()
coalescer.readargs(sys.argv)
coalescer.coalesceall()

  

