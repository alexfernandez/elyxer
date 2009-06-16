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
# Alex 20090617
# eLyXer import configuration file

import codecs
from util.trace import Trace
from util.options import *
from io.fileline import *
from conf.fileconfig import *


class ImportCommands(object):
  "Import a LyX unicodesymbols file"

  escapes = [
      ('\\', '\\\\')
      ]

  def __init__(self, filename):
    self.reader = LineReader(filename)
    self.objects = dict()
    self.section = 'FormulaConfig.commands'
    self.objects[self.section] = dict()
    self.sectionobject = self.objects[self.section]
    self.serializer = ConfigSerializer(ImportCommands.escapes)

  def parse(self):
    "Parse the whole file"
    while not self.reader.finished():
      self.parseline(self.reader.currentline())
      self.reader.nextline()
    return self

  def parseline(self, line):
    "Parse a single line"
    if line == '':
      return
    if line.startswith('#'):
      return
    if '#' in line:
      line = line.split('#')[0]
    self.parseparam(line)

  def parseparam(self, line):
    "Parse a parameter line"
    line = line.strip()
    if len(line) == 0:
      return
    pieces = line.split()
    if len(pieces) < 5:
      return
    unicode = pieces[0]
    if not unicode.startswith('0x'):
      Trace.error('Invalid unicode ' + unicode)
      return
    unicode = unicode.replace('0x', '')
    unicodechar = unichr(int(unicode, 16))
    command = pieces[4].replace('"', '')
    if not command.startswith('\\'):
      #Trace.error('Invalid command ' + command)
      return
    command = self.serializer.unescape(command)
    if command.count('\\') > 1:
      #Trace.error('Too many commands ' + command)
      return
    Trace.message(unicodechar + ': ' + command)
    self.sectionobject[command] = unicodechar

