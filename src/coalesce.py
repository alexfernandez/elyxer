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
  "Coalesce a set of Python files into a single Python file,"
  "so that it can be distributed and directly executed."

  def __init__(self):
    self.comments = True
    self.files = []
    self.directory = ''
    self.writer = None
  
  def convert(self, filename, directory = ''):
    "Convert the filename adding the appropriate directories."
    if os.path.exists(filename):
      return filename
    newname = os.path.join(self.directory, filename)
    if os.path.exists(newname):
      return newname
    newname = os.path.join(directory, filename)
    if os.path.exists(newname):
      return newname
    Trace.error('Missing file ' + filename)
    return None

  def getreader(self, filename):
    "Get a line reader."
    if filename in self.files:
      # already parsed; skip
      return None
    self.files.append(filename)
    return LineReader(filename)

  def readargs(self, args):
    "Read arguments from the command line"
    del args[0]
    if len(args) == 0:
      self.usage()
      return
    self.filename = self.convert(args[0])
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

  def usage(self):
    Trace.error('Usage: coalesce.py filein [fileout]')
    return

  def coalesceall(self):
    "Coalesce all files from the root reader."
    if not self.writer:
      return
    self.coalesce(self.filename)
    self.writer.close()

  def coalesce(self, filename):
    "Coalesce all Python files used in filein to fileout"
    reader = self.getreader(filename)
    if not reader:
      return
    while not reader.finished():
      line = reader.currentline()
      if line.startswith('from'):
        self.comments = False
        nextname = line.split()[1].replace('.', '/') + '.py'
        newname = self.convert(nextname, os.path.dirname(filename))
        if newname:
          self.coalesce(newname)
        else:
          # make things like "from socket import gaierror" work
          self.writer.writeline(line)
      elif line.startswith('#'):
        if self.comments:
          self.writer.writeline(line)
      else:
        self.writer.writeline(line)
      reader.nextline()
    reader.close()

coalescer = Coalescer()
coalescer.readargs(sys.argv)
coalescer.coalesceall()

