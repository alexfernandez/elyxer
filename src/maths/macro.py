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
from parse.headerparse import *
from maths.formula import *
from maths.hybrid import *


class LyXPreamble(Container):
  "The preamble at the beginning of a LyX file. Parsed for macros."

  def __init__(self):
    self.parser = PreambleParser()
    self.output = EmptyOutput()

  def process(self):
    "Parse the LyX preamble, if needed."
    if len(PreambleParser.preamble) == 0:
      return
    FormulaCommand.preambling = True
    pos = TextPosition('\n'.join(PreambleParser.preamble))
    while not pos.finished():
      if self.detectdefinition(pos):
        self.parsedefinition(pos)
      else:
        pos.globincluding('\n')
    PreambleParser.preamble = []
    FormulaCommand.preambling = False

  def detectdefinition(self, pos):
    "Detect a macro definition."
    for function in FormulaConfig.definingfunctions:
      if pos.checkfor(function):
        return True
    return False

  def parsedefinition(self, pos):
    "Parse a macro definition."
    command = FormulaCommand()
    command.factory = FormulaFactory()
    bit = command.parsebit(pos)
    if not isinstance(bit, DefiningFunction):
      Trace.error('Did not define a macro with ' + unicode(bit))

class MathMacro(object):
  "A math macro: command, parameters, default values, definition."

  macros = dict()

  def __init__(self):
    self.newcommand = None
    self.parameters = 0
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
    self.number = int(pos.currentskip())
    self.original = '#' + unicode(self.number)
    self.contents = [TaggedBit().constant('#' + unicode(self.number), 'span class="unknown"')]

class DefiningFunction(HybridFunction):
  "Read a function that defines a new command (a macro)."

  commandmap = FormulaConfig.definingfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    if self.factory.detecttype(Bracket, pos):
      newcommand = self.parseliteral(pos)
    elif self.factory.detecttype(FormulaCommand, pos):
      newcommand = FormulaCommand().extractcommand(pos)
    else:
      Trace.error('Unknown formula bit in defining function at ' + pos.identifier())
      return
    Trace.debug('New command: ' + newcommand)
    HybridFunction.parsebit(self, pos)
    macro = MathMacro()
    macro.newcommand = newcommand
    macro.parameters = self.readparameters()
    macro.definition = self.params['$d'].value
    self.extractdefaults(macro)
    MathMacro.macros[newcommand] = macro

  def readparameters(self):
    "Read the number of parameters in the macro."
    if not self.params['$n'].literalvalue:
      return 0
    return int(self.params['$n'].literalvalue)

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
    value = self.params['$' + unicode(index)].value
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
    while self.factory.detectany(pos):
      self.values.append(self.parseparameter(pos))
    defaults = list(macro.defaults)
    while len(self.values) < macro.parameters and len(defaults) > 0:
      self.values.insert(0, defaults.pop())
    if len(self.values) < macro.parameters:
      Trace.error('Missing parameters in macro ' + unicode(self))
    self.completemacro(macro)

  def completemacro(self, macro):
    "Complete the macro with the parameters read."
    self.contents = [macro.instantiate()]
    for parameter in self.searchall(MacroParameter):
      index = parameter.number - 1
      if index >= len(self.values):
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

FormulaCommand.commandbits += [
    DefiningFunction(), MacroFunction(),
    ]

FormulaFactory.types += [ MacroParameter ]

