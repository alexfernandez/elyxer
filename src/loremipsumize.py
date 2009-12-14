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
# Alex 20091210
# Lorem-ipsumize a document: replace all alphanumeric texts longer than two words with "Lorem ipsum" and leave the symbols.

import sys
from io.fileline import *
from parse.position import *
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
    usage()
    return
  reader = getreader(args[0])
  del args[0]
  fileout = sys.stdout
  if len(args) > 0:
    fileout = args[0]
    del args[0]
  if len(args) > 0:
    usage()
    return
  writer = LineWriter(fileout)
  return reader, writer

def usage():
  Trace.error('Usage: loremipsumize.py filein [fileout]')
  return

class LoremIpsumizer(object):

  starts = '@\\'

  def loremipsumize(self, reader, writer):
    "Convert all texts longer than two words to 'lorem ipsum'."
    if not reader:
      return
    while not reader.finished():
      line = self.processline(reader.currentline())
      writer.writeline(line)
      reader.nextline()
    reader.close()

  def processline(self, line):
    "Process a single line and return the result."
    if len(line) == 0:
      return ''
    if line[0] in LoremIpsumizer.starts:
      return line
    pos = Position(line)
    result = ''
    while not pos.finished():
      result += self.parsepos(pos)
    return result

  def parsepos(self, pos):
    "Parse the current position, return the result."
    if pos.current().isalpha() or pos.current().isdigit():
      alpha = pos.glob(lambda current: current.isalpha() or current.isspace() or current.isdigit())
      if len(alpha.split()) > 2:
        return "lorem ipsum"
      return alpha
    if pos.current().isspace():
      return pos.skipspace()
    return pos.currentskip()

reader, writer = readargs(sys.argv)
if reader:
  LoremIpsumizer().loremipsumize(reader, writer)
  writer.close()


