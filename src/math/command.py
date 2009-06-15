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
# Alex 20090330
# eLyXer commands in formula processing

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from math.formula import *
from math.bits import *


class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  commandbits = []

  def detect(self, pos):
    "Find the current command"
    return pos.checkfor(FormulaConfig.starts['command'])

  def parse(self, pos):
    "Parse the command"
    command = self.extractcommand(pos)
    for bit in FormulaCommand.commandbits:
      if bit.recognize(command):
        newbit = bit.clone()
        newbit.factory = self.factory
        newbit.setcommand(command)
        newbit.parse(pos)
        self.add(newbit)
        return newbit
    Trace.error('Unknown command ' + command)
    self.output = TaggedOutput().settag('span class="unknown"')
    self.addconstant(command, pos)

  def extractcommand(self, pos):
    "Extract the command from the current position"
    start = FormulaConfig.starts['command']
    if not pos.checkfor(start):
      Trace.error('Missing command start ' + start)
      return
    pos.skip(start)
    if pos.current().isalpha():
      # alpha command
      return start + self.glob(pos, lambda p: p.current().isalpha())
    # symbol command
    command = start + pos.current()
    pos.skip(pos.current())
    return command

  def process(self):
    "Process the internals"
    for bit in self.contents:
      bit.process()

class CommandBit(FormulaCommand):
  "A formula bit that includes a command"

  def recognize(self, command):
    "Recognize the command as own"
    return command in self.commandmap

  def setcommand(self, command):
    "Set the command in the bit"
    self.command = command
    self.original += command
    self.translated = self.commandmap[self.command]
 
  def parseparameter(self, pos):
    "Parse a parameter at the current position"
    if not self.factory.detectbit(pos):
      Trace.error('No parameter found at: ' + pos.remaining())
      return
    parameter = self.factory.parsebit(pos)
    self.add(parameter)
    return parameter

class EmptyCommand(CommandBit):
  "An empty command (without parameters)"

  commandmap = FormulaConfig.commands

  def parse(self, pos):
    "Parse a command without parameters"
    self.contents = [FormulaConstant(self.translated)]

class AlphaCommand(CommandBit):
  "A command without paramters whose result is alphabetical"

  commandmap = FormulaConfig.alphacommands

  def parse(self, pos):
    "Parse the command and set type to alpha"
    EmptyCommand.parse(self, pos)
    self.type = 'alpha'

class OneParamFunction(CommandBit):
  "A function of one parameter"

  commandmap = FormulaConfig.onefunctions

  def parse(self, pos):
    "Parse a function with one parameter"
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)

class SymbolFunction(CommandBit):
  "Find a function which is represented by a symbol (like _ or ^)"

  commandmap = FormulaConfig.symbolfunctions

  def detect(self, pos):
    "Find the symbol"
    return pos.current() in SymbolFunction.commandmap

  def parse(self, pos):
    "Parse the symbol"
    self.setcommand(pos.current())
    pos.skip(self.command)
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)

class LiteralFunction(CommandBit):
  "A function where parameters are read literally"

  commandmap = FormulaConfig.literalfunctions

  def parse(self, pos):
    "Parse a literal parameter"
    self.output = TaggedOutput().settag(self.translated)
    bracket = Bracket().parseliteral(pos)
    self.add(bracket)
    self.contents.append(FormulaConstant(bracket.literal))

  def process(self):
    "Set the type to font"
    self.type = 'font'

class LabelFunction(LiteralFunction):
  "A function that acts as a label"

  commandmap = FormulaConfig.labelfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class FontFunction(OneParamFunction):
  "A function of one parameter that changes the font"

  commandmap = FormulaConfig.fontfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  commandmap = FormulaConfig.decoratingfunctions

  def parse(self, pos):
    "Parse a decorating function"
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.type = 'alpha'
    symbol = self.translated
    tagged = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.contents.append(tagged)
    parameter = self.parseparameter(pos)
    parameter.output = TaggedOutput().settag('span class="undersymbol"')
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = [FormulaConfig.alphacommands[self.original]]

class HybridFunction(CommandBit):
  "Read a function with two parameters: [] and {}"

  commandmap = FormulaConfig.hybridfunctions

  def parse(self, pos):
    "Parse a function with [] and {} parameters"
    self.parsesquare(pos)
    self.parseparameter(pos)
    self.contents[-1].type = 'font'

  def parsesquare(self, pos):
    "Parse a square bracket"
    bracket = SquareBracket()
    if not bracket.detect(pos):
      return
    bracket.parse(pos)
    self.add(bracket)

class FractionFunction(CommandBit):
  "A fraction with two parameters"

  commandmap = FormulaConfig.fractionfunctions

  def parse(self, pos):
    "Parse a fraction function with two parameters"
    tags = self.translated
    self.output = TaggedOutput().settag(tags[0])
    parameter1 = self.parseparameter(pos)
    if not parameter1:
      return
    parameter1.output = TaggedOutput().settag(tags[1])
    parameter2 = self.parseparameter(pos)
    if not parameter2:
      return
    parameter2.output = TaggedOutput().settag(tags[2])

FormulaFactory.bits += [FormulaCommand(), SymbolFunction()]
FormulaCommand.commandbits = [
    EmptyCommand(), OneParamFunction(), DecoratingFunction(),
    FractionFunction(), FontFunction(), LabelFunction(), LiteralFunction(),
    HybridFunction(),
    ]

