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

from util.trace import Trace
from util.options import *
from io.fileline import *
from conf.fileconfig import *


class ImportFile(object):
  "Generic import file."

  def __init__(self, filename):
    self.reader = LineReader(filename)
    self.objects = dict()
    self.section = 'FormulaConfig.commands'
    self.objects[self.section] = dict()
    self.sectionobject = self.objects[self.section]
    self.serializer = ConfigSerializer(ImportCommands.escapes)
    self.existing = dict()
    self.existing.update(FormulaConfig.commands)
    self.existing.update(FormulaConfig.alphacommands)

  def parsewhole(self, parseline):
    "Parse the whole file line by line."
    while not self.reader.finished():
      line = self.convertline(self.reader.currentline())
      if line:
        parseline(line)
      self.reader.nextline()

  def convertline(self, line):
    "Convert a single line removing comments."
    if line == '':
      return None
    if line.startswith('#'):
      return None
    if '#' in line:
      line = line.split('#')[0]
    return line

  def setsymbol(self, command, unicodesymbol):
    "Set the unicode symbol for a command."
    if not command.startswith('\\'):
      Trace.error('Invalid command ' + command)
      return
    if command.count('\\') > 1:
      Trace.error('Too many commands ' + command)
      return
    if command in self.existing:
      return
    Trace.message(command + ':' + unicodesymbol)
    self.sectionobject[command] = unicodesymbol

class ImportCommands(ImportFile):
  "Import a LyX unicodesymbols file"

  escapes = [
      ('\\', '\\\\')
      ]

  def parse(self):
    "Parse the whole LyX commands file."
    self.parsewhole(self.parseparam)
    return self

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
    command = self.serializer.unescape(command)
    self.setsymbol(command, unicodechar)

class ImportCsv(ImportFile):
  "Import a file with comma-separated values of the form: \command,unicode."

  def parse(self):
    "Parse the whole CSV file."
    self.parsewhole(self.parsecsv)
    return self

  def parsecsv(self, line):
    "Parse a line \command,unicode."
    line = line.strip()
    if len(line) == 0:
      return
    pieces = line.split(',')
    if len(pieces) != 2:
      return
    self.setsymbol(pieces[0],pieces[1])

