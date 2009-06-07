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
# File line management for eLyXer

import sys
import codecs
from util.trace import Trace


class LineReader(object):
  "Reads a file line by line"

  def __init__(self, filename):
    if isinstance(filename, file):
      self.file = filename
    else:
      self.file = codecs.open(filename, 'r', "utf-8")
    self.linenumber = 0
    self.current = None
    self.split = None

  def currentline(self):
    "Get the current line"
    if not self.current:
      self.readline()
    return self.current

  def currentsplit(self):
    "Get the current nonblank line, split into words"
    if not self.split:
      self.split = self.currentline().split()
    return self.split

  def nextline(self):
    "Go to next line"
    if self.finished():
      Trace.fatal('Read beyond file end')
    self.current = None
    self.split = None

  def readline(self):
    "Read a line from file"
    self.current = self.file.readline()
    if self.file == sys.stdin:
      self.current = self.current.decode('utf-8')
    self.linenumber += 1
    Trace.prefix = 'Line ' + unicode(self.linenumber) + ': '
    if self.linenumber % 1000 == 0:
      Trace.message('Parsing')

  def finished(self):
    "Have we finished reading the file"
    if len(self.currentline()) == 0:
      return True
    return False

  def close(self):
    self.file.close()

class LineWriter(object):
  "Writes a file as a series of lists"

  def __init__(self, filename):
    if isinstance(filename, file):
      self.file = filename
    else:
      self.file = codecs.open(filename, 'w', "utf-8")

  def write(self, strings):
    "Write a list of strings"
    for string in strings:
      if not isinstance(string, basestring):
        Trace.error('Not a string: ' + unicode(string) + ' in ' + unicode(strings))
        return
      self.writestring(string)

  def writestring(self, string):
    "Write a string"
    if self.file == sys.stdout:
      string = string.encode('utf-8')
    self.file.write(string)

  def writeline(self, line):
    "Write a line to file"
    self.writestring(line + '\n')

  def close(self):
    self.file.close()

