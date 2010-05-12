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
from ref.label import *
from util.trace import Trace
from util.clone import *
from conf.config import *
from math.formula import *
from math.bits import *


class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  commandbits = []
  start = FormulaConfig.starts['command']
  preambling = False

  def detect(self, pos):
    "Find the current command"
    return pos.checkfor(FormulaCommand.start)

  def parsebit(self, pos):
    "Parse the command"
    command = self.extractcommand(pos)
    for bit in FormulaCommand.commandbits:
      if bit.recognize(command):
        newbit = Cloner.clone(bit)
        newbit.factory = self.factory
        newbit.setcommand(command)
        newbit.parsebit(pos)
        self.add(newbit)
        return newbit
    if not self.preambling:
      Trace.error('Unknown command ' + command)
    self.output = TaggedOutput().settag('span class="unknown"')
    self.add(FormulaConstant(command))
    return None

  def extractcommand(self, pos):
    "Extract the command from the current position"
    if not pos.checkskip(FormulaCommand.start):
      Trace.error('Missing command start ' + start)
      return
    if pos.current().isalpha():
      # alpha command
      return FormulaCommand.start + pos.globalpha()
    # symbol command
    return FormulaCommand.start + pos.currentskip()

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
      Trace.error('No parameter found at: ' + pos.identifier())
      return None
    parameter = self.factory.parsebit(pos)
    self.add(parameter)
    return parameter

  def parsesquare(self, pos):
    "Parse a square bracket"
    bracket = SquareBracket()
    if not bracket.detect(pos):
      return None
    bracket.parsebit(pos)
    self.add(bracket)
    return bracket

  def parseliteral(self, pos):
    "Parse a literal bracket."
    bracket = Bracket()
    if not bracket.detect(pos):
      Trace.error('No literal parameter found at: ' + pos.identifier())
      return None
    self.add(bracket.parseliteral(pos))
    return bracket.literal

  def parsesquareliteral(self, pos):
    "Parse a square bracket literally."
    bracket = SquareBracket()
    if not bracket.detect(pos):
      return None
    self.add(bracket.parseliteral(pos))
    return bracket.literal

class EmptyCommand(CommandBit):
  "An empty command (without parameters)"

  commandmap = FormulaConfig.commands

  def parsebit(self, pos):
    "Parse a command without parameters"
    self.contents = [FormulaConstant(self.translated)]

class AlphaCommand(EmptyCommand):
  "A command without paramters whose result is alphabetical"

  commandmap = FormulaConfig.alphacommands

  def parsebit(self, pos):
    "Parse the command and set type to alpha"
    EmptyCommand.parsebit(self, pos)
    self.type = 'alpha'

class OneParamFunction(CommandBit):
  "A function of one parameter"

  commandmap = FormulaConfig.onefunctions

  def parsebit(self, pos):
    "Parse a function with one parameter"
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)
    self.simplifyifpossible()

  def simplifyifpossible(self):
    "Try to simplify to a single character."
    if self.original in self.commandmap:
      self.output = FixedOutput()
      self.html = [self.commandmap[self.original]]

class SymbolFunction(CommandBit):
  "Find a function which is represented by a symbol (like _ or ^)"

  commandmap = FormulaConfig.symbolfunctions

  def detect(self, pos):
    "Find the symbol"
    return pos.current() in SymbolFunction.commandmap

  def parsebit(self, pos):
    "Parse the symbol"
    self.setcommand(pos.current())
    pos.skip(self.command)
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)

class TextFunction(CommandBit):
  "A function where parameters are read as text."

  commandmap = FormulaConfig.textfunctions

  def parsebit(self, pos):
    "Parse a text parameter"
    self.output = TaggedOutput().settag(self.translated)
    bracket = Bracket().parsetext(pos)
    self.add(bracket)

  def process(self):
    "Set the type to font"
    self.type = 'font'

class LabelFunction(CommandBit):
  "A function that acts as a label"

  commandmap = FormulaConfig.labelfunctions

  def parsebit(self, pos):
    "Parse a literal parameter"
    self.key = self.parseliteral(pos)

  def process(self):
    "Add an anchor with the label contents."
    self.type = 'font'
    self.label = Label().create(' ', self.key, type = 'eqnumber')
    self.contents = [self.label]
    # store as a Label so we know it's been seen
    Label.names[self.key] = self.label

class FontFunction(OneParamFunction):
  "A function of one parameter that changes the font"

  commandmap = FormulaConfig.fontfunctions

  def process(self):
    "Simplify if possible using a single character."
    self.type = 'font'
    self.simplifyifpossible()

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  commandmap = FormulaConfig.decoratingfunctions

  def parsebit(self, pos):
    "Parse a decorating function"
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.type = 'alpha'
    symbol = self.translated
    self.symbol = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.contents.append(self.symbol)
    self.parameter = self.parseparameter(pos)
    self.parameter.output = TaggedOutput().settag('span class="undersymbol"')
    self.simplifyifpossible()

class UnderDecoratingFunction(DecoratingFunction):
  "A function that decorates some bit of text from below."

  commandmap = FormulaConfig.underdecoratingfunctions

  def parsebit(self, pos):
    "Parse an under-decorating function."
    DecoratingFunction.parsebit(self, pos)
    self.symbol.output.settag('span class="symbolunder"')
    self.parameter.output.settag('span class="oversymbol"')

FormulaFactory.bits += [FormulaCommand(), SymbolFunction()]
FormulaCommand.commandbits = [
    EmptyCommand(), AlphaCommand(), OneParamFunction(), DecoratingFunction(),
    FontFunction(), LabelFunction(), TextFunction(), UnderDecoratingFunction(),
    ]

