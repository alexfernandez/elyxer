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
from trace import Trace


class LineReader(object):
  "Reads a file line by line"

  def __init__(self, file):
    self.file = file
    self.linenumber = 0
    self.current = None
    self.split = None

  def currentline(self):
    "Get the current line"
    if not self.current:
      self.readline()
    return self.current

  def currentnonblank(self):
    "Get the current nonblank line"
    while (self.currentline() == '\n'):
      self.nextline()
    return self.currentline()

  def currentsplit(self):
    "Get the current nonblank line, split into words"
    if not self.split:
      self.split = self.currentnonblank().split()
    return self.split

  def nextline(self):
    "Go to next line"
    self.current = None
    self.split = None

  def readline(self):
    "Read a line from file"
    self.current = self.file.readline()
    if self.file == sys.stdin:
      self.current = self.current.decode('utf-8')
    self.linenumber += 1
    Trace.prefix = 'Line ' + str(self.linenumber) + ': '
    if self.linenumber % 1000 == 0:
      Trace.message('Parsing')

  def finished(self):
    "Have we finished reading the file"
    if len(self.currentline()) == 0:
      return True
    return False

  def close(self):
    self.file.close()

class HtmlWriter(object):
  "Writes an HTML file as a series of lists"

  def __init__(self, file):
    self.file = file

  def write(self, html):
    "Write a list of lines"
    for line in html:
      self.writeline(line)

  def writeline(self, line):
    "Write a line to file"
    if self.file == sys.stdout:
      line = line.encode('utf-8')
    self.file.write(line)

  def close(self):
    self.file.close()

