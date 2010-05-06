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

  macros = dict()

  def __init__(self, command):
    self.command = command
    self.parameters = 0
    self.defaults = []
    self.definition = None

class DefiningFunction(HybridFunction):
  "Read a function that defines a new command (a macro)."

  commandmap = FormulaConfig.definingfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    newcommand = Bracket().parseliteral(pos).literal
    Trace.debug('New command: ' + newcommand)
    HybridFunction.parsebit(self, pos)
    macro = MathMacro(newcommand)
    Trace.debug('Params: ' + unicode(self.params))
    macro.parameters = self.readparameters()
    MathMacro.macros[newcommand] = macro

  def readparameters(self):
    "Read the number of parameters in the macro."
    if not self.params['$n']:
      return 0
    return int(self.params['$n'].contents[0].contents[0].contents[0].original)

class MacroFunction(CommandBit):
  "A function that was defined using a macro."

  commandmap = MathMacro.macros

  def parsebit(self, pos):
    "Parse a number of input parameters."
    self.values = []
    macro = self.translated
    for n in range(macro.parameters):
      self.values.append(self.parseparameter(pos))
    self.contents = self.completemacro(pos)

  def completemacro(self, pos):
    "Complete the macro with the parameters read."
    return []

FormulaCommand.commandbits += [
    DefiningFunction(), MacroFunction(),
    ]

class FormulaMacro(Inset):
  "A math macro defined in an inset."

  def __init__(self):
    self.parser = FormulaParser()
    self.output = EmptyOutput()

  def process(self):
    "Convert the formula to tags"
    pass

  def __unicode__(self):
    "Return a printable representation."
    if self.macro.command:
      return 'Macro: \\' + self.macro.command
    return 'Unnamed macro'

