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
# Alex 20100615
# eLyXer macro processing

from util.trace import Trace
from conf.config import *
from parse.formulaparse import *
from parse.headerparse import *
from maths.formula import *
from maths.hybrid import *


class MathMacro(object):
  "A math macro: command, parameters, default values, definition."

  macros = dict()

  def __init__(self):
    self.newcommand = None
    self.parameternumber = 0
    self.defaults = []
    self.definition = None

  def instantiate(self):
    "Return an instance of the macro."
    return self.definition.clone()

class MacroParameter(FormulaBit):
  "A parameter from a macro."

  def detect(self, pos):
    "Find a macro parameter: #n."
    return pos.checkfor('#')

  def parsebit(self, pos):
    "Parse the parameter: #n."
    if not pos.checkskip('#'):
      Trace.error('Missing parameter start #.')
      return
    self.number = int(pos.skipcurrent())
    self.original = '#' + unicode(self.number)
    self.contents = [TaggedBit().constant('#' + unicode(self.number), 'span class="unknown"')]

class DefiningFunction(ParameterFunction):
  "Read a function that defines a new command (a macro)."

  commandmap = FormulaConfig.definingfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    if self.factory.detecttype(Bracket, pos):
      newcommand = self.parseliteral(pos)
    elif self.factory.detecttype(FormulaCommand, pos):
      newcommand = self.factory.create(FormulaCommand).extractcommand(pos)
    else:
      Trace.error('Unknown formula bit in defining function at ' + pos.identifier())
      return
    template = self.translated
    self.factory.defining = True
    self.readparams(template, pos)
    self.factory.defining = False
    self.contents = []
    macro = MathMacro()
    macro.newcommand = newcommand
    macro.parameternumber = self.getintvalue('$n')
    Trace.debug('New command ' + newcommand + ' (' + \
        unicode(macro.parameternumber) + ' parameters)')
    macro.definition = self.getvalue('$d')
    self.extractdefaults(macro)
    MathMacro.macros[newcommand] = macro

  def extractdefaults(self, macro):
    "Extract the default values for existing parameters."
    for index in range(9):
      value = self.extractdefault(index + 1)
      if value:
        macro.defaults.append(value)
      else:
        return

  def extractdefault(self, index):
    "Extract the default value for parameter index."
    value = self.getvalue('$' + unicode(index))
    if not value:
      return None
    if len(value.contents) == 0:
      return FormulaConstant('')
    return value.contents[0]

class MacroFunction(CommandBit):
  "A function that was defined using a macro."

  commandmap = MathMacro.macros

  def parsebit(self, pos):
    "Parse a number of input parameters."
    self.values = []
    macro = self.translated
    self.parseparameters(pos, macro)
    self.completemacro(macro)

  def parseparameters(self, pos, macro):
    "Parse as many parameters as are needed."
    self.parseoptional(pos, list(macro.defaults))
    while self.factory.detecttype(Bracket, pos):
      self.values.append(self.parseparameter(pos))
    remaining = macro.parameternumber - len(self.values)
    if remaining > 0:
      self.parsenumbers(remaining, pos)
    if len(self.values) < macro.parameternumber:
      Trace.error('Missing parameters in macro ' + unicode(self))

  def parseoptional(self, pos, defaults):
    "Parse optional parameters."
    optional = []
    while self.factory.detecttype(SquareBracket, pos):
      optional.append(self.parsesquare(pos))
      if len(optional) > len(defaults):
        break
    for value in optional:
      default = defaults.pop()
      if len(value.contents) > 0:
        self.values.append(value)
      else:
        self.values.append(default)
    self.values += defaults

  def parsenumbers(self, remaining, pos):
    "Parse the remaining parameters as a running number."
    "For example, 12 would be {1}{2}."
    if pos.finished():
      return
    if not self.factory.detecttype(FormulaNumber, pos):
      return
    number = self.factory.parsetype(FormulaNumber, pos)
    if not len(number.original) == remaining:
      self.values.append(number)
      return
    for digit in number.original:
      value = self.factory.create(FormulaNumber)
      value.add(FormulaConstant(digit))
      value.type = number
      self.values.append(value)

  def completemacro(self, macro):
    "Complete the macro with the parameters read."
    self.contents = [macro.instantiate()]
    for parameter in self.searchall(MacroParameter):
      index = parameter.number - 1
      if index >= len(self.values):
        Trace.error('Macro parameter index out of bounds: ' + unicode(index))
        return
      parameter.contents = [self.values[index].clone()]

class FormulaMacro(Formula):
  "A math macro defined in an inset."

  def __init__(self):
    self.parser = MacroParser()
    self.output = EmptyOutput()

  def __unicode__(self):
    "Return a printable representation."
    return 'Math macro'

FormulaFactory.types += [ MacroParameter ]

FormulaCommand.types += [
    DefiningFunction, MacroFunction,
    ]

