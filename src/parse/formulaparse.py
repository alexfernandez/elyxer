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
# Alex 20090503
# eLyXer formula parsing

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *


class FormulaParser(Parser):
  "Parses a formula"

  def parseheader(self, reader):
    "See if the formula is inlined"
    self.begin = reader.linenumber + 1
    if reader.currentline().find('$') > 0:
      return ['inline']
    else:
      return ['block']
  
  def parse(self, reader):
    "Parse the formula"
    if '$' in reader.currentline():
      rest = reader.currentline().split('$', 1)[1]
      if '$' in rest:
        # formula is $...$
        formula = reader.currentline().split('$')[1]
        reader.nextline()
      else:
        # formula is multiline $...$
        formula = self.parsemultiliner(reader, '$', '$')
    elif '\\[' in reader.currentline():
      # formula of the form \[...\]
      formula = self.parsemultiliner(reader, '\\[', '\\]')
    elif '\\begin{' in reader.currentline() and reader.currentline().endswith('}\n'):
      current = reader.currentline().strip()
      endsplit = current.split('\\begin{')[1].split('}')
      startpiece = '\\begin{' + endsplit[0] + '}'
      endpiece = '\\end{' + endsplit[0] + '}'
      formula = self.parsemultiliner(reader, startpiece, endpiece)
    else:
      Trace.error('Formula beginning ' + reader.currentline().strip +
          ' is unknown')
    while not reader.currentline().startswith(self.ending):
      stripped = reader.currentline().strip()
      if len(stripped) > 0:
        Trace.error('Unparsed formula line ' + stripped)
      reader.nextline()
    reader.nextline()
    return [formula]

  def parsemultiliner(self, reader, start, ending):
    "Parse a formula in multiple lines"
    formula = ''
    if not start in reader.currentline():
      Trace.error('Line ' + reader.currentline().strip() +
          ' does not contain formula start ' + start)
      return ''
    index = reader.currentline().index(start)
    formula = reader.currentline()[index + len(start):].strip()
    reader.nextline()
    while not reader.currentline().endswith(ending + '\n'):
      formula += reader.currentline()
      reader.nextline()
    formula += reader.currentline()[:-len(ending) - 1]
    reader.nextline()
    return formula

class Position(object):
  "A position in a formula to parse"

  def __init__(self, text):
    self.text = text
    self.pos = 0

  def skip(self, string):
    "Skip a string"
    self.pos += len(string)

  def remaining(self):
    "Return the text remaining for parsing"
    return self.text[self.pos:]

  def isout(self):
    "Find out if we are out of the formula yet"
    return self.pos >= len(self.text)

  def current(self):
    "Return the current character"
    return self.text[self.pos]

  def checkfor(self, string):
    "Check for a string at the given position"
    if self.pos + len(string) > len(self.text):
      return False
    return self.text[self.pos : self.pos + len(string)] == string

  def clone(self):
    "Return a copy of self"
    clone = Position(self.text)
    clone.pos = self.pos
    return clone


