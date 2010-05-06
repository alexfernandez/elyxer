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
# Alex 20101506
# eLyXer macro processing

from gen.inset import *
from util.trace import Trace
from conf.config import *
from parse.formulaparse import *


class MathMacro(object):
  "A math macro: command, parameters, default values, definition."

  def __init__(self):
    self.command = ''
    self.parameters = []
    self.defaults = []
    self.definition = None

class DefiningFunction(HybridFunction):
  "Read a function that defines a new command (a macro)."

  commandmap = FormulaConfig.definingfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    HybridFunction.parsebit(self, pos)
    readtemplate = self.translated[0]

FormulaCommand.commandbits += [
    DefiningFunction(),
    ]

class FormulaMacro(Inset):
  "A math macro defined in an inset."

  macros = dict()

  def __init__(self):
    self.parser = FormulaParser()
    self.output = EmptyOutput()
    self.macro = MathMacro()

  def process(self):
    "Convert the formula to tags"
    pass

  def __unicode__(self):
    "Return a printable representation."
    if self.macro.command:
      return 'Macro: \\' + self.macro.command
    return 'Unnamed macro'

