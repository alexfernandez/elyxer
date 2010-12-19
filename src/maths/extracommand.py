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
# Alex 20101218
# eLyXer extra commands for unusual things.

from util.trace import Trace
from util.clone import *
from conf.config import *
from maths.command import *
from maths.symbol import *
from maths.array import *


class CombiningFunction(OneParamFunction):

  commandmap = FormulaConfig.combiningfunctions

  def parsebit(self, pos):
    "Parse a combining function."
    self.type = 'alpha'
    combining = self.translated
    parameter = self.parsesingleparameter(pos)
    if len(parameter.extracttext()) != 1:
      Trace.error('Applying combining function ' + self.command + ' to invalid string "' + parameter.extracttext() + '"')
    self.contents.append(Constant(combining))

  def parsesingleparameter(self, pos):
    "Parse a parameter, or a single letter."
    if self.factory.detecttype(Bracket, pos) \
        or self.factory.detecttype(FormulaCommand, pos):
      return self.parseparameter(pos)
    letter = FormulaConstant(pos.skipcurrent())
    self.add(letter)
    return letter

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  commandmap = FormulaConfig.decoratingfunctions

  def parsebit(self, pos):
    "Parse a decorating function"
    self.type = 'alpha'
    symbol = self.translated
    self.symbol = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.parameter = self.parseparameter(pos)
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.contents.insert(0, self.symbol)
    self.parameter.output = TaggedOutput().settag('span class="undersymbol"')
    self.simplifyifpossible()

class LimitCommand(EmptyCommand):
  "A command which accepts limits above and below, in display mode."

  commandmap = FormulaConfig.limitcommands

  def parsebit(self, pos):
    "Parse a limit command."
    pieces = self.translated[1:]
    if not DocumentParameters.displaymode or len(self.translated) == 1:
      pieces = self.translated[0:1]
    self.output = TaggedOutput().settag('span class="limits"')
    for piece in pieces:
      self.contents.append(TaggedBit().constant(piece, 'span class="limit"'))

class LimitsProcessor(MathsProcessor):
  "A processor for limits inside an element."

  def process(self, contents, index):
    "Process the limits for an element."
    if self.checklimits(contents, index):
      self.modifylimits(contents, index)
    if self.checkscript(contents, index) and self.checkscript(contents, index + 1):
      self.modifyscripts(contents, index)

  def checklimits(self, contents, index):
    "Check if the current position has a limits command."
    if not DocumentParameters.displaymode:
      return False
    if not isinstance(contents[index], LimitCommand):
      return False
    return self.checkscript(contents, index + 1)

  def modifylimits(self, contents, index):
    "Modify a limits commands so that the limits appear above and below."
    limited = contents[index]
    subscript = self.getlimit(contents, index + 1)
    limited.contents.append(subscript)
    if self.checkscript(contents, index + 1):
      superscript = self.getlimit(contents, index  + 1)
    else:
      superscript = TaggedBit().constant(u' ', 'sup class="limit"')
    limited.contents.insert(0, superscript)

  def getlimit(self, contents, index):
    "Get the limit for a limits command."
    limit = self.getscript(contents, index)
    limit.output.tag = limit.output.tag.replace('script', 'limit')
    return limit

  def modifyscripts(self, contents, index):
    "Modify the super- and subscript to appear vertically aligned."
    subscript = self.getscript(contents, index)
    # subscript removed so instead of index + 1 we get index again
    superscript = self.getscript(contents, index)
    scripts = TaggedBit().complete([superscript, subscript], 'span class="scripts"')
    contents.insert(index, scripts)

  def checkscript(self, contents, index):
    "Check if the current element is a sub- or superscript."
    if len(contents) <= index:
      return False
    return isinstance(contents[index], SymbolFunction)

  def getscript(self, contents, index):
    "Get the sub- or superscript."
    bit = contents[index]
    bit.output.tag += ' class="script"'
    del contents[index]
    return bit

class BracketCommand(OneParamFunction):
  "A command which defines a bracket."

  commandmap = FormulaConfig.bracketcommands

  def parsebit(self, pos):
    "Parse the bracket."
    OneParamFunction.parsebit(self, pos)

class BracketProcessor(MathsProcessor):
  "A processor for bracket commands."

  directions = {'left': 1, 'right': -1}

  def process(self, contents, index):
    "Convert the bracket using Unicode pieces, if possible."
    if not isinstance(contents[index], BracketCommand):
      return
    self.checkarray(contents, index, 'left')
    self.checkarray(contents, index, 'right')

  def checkarray(self, contents, index, direction):
    "Check for the right command, and an array in the given direction."
    command = contents[index]
    if command.command != '\\' + direction:
      return
    newindex = index + self.directions[direction]
    if newindex < 0 or newindex >= len(contents):
      return
    begin = contents[newindex]
    if not isinstance(begin, BeginCommand):
      return
    array = begin.array
    if not isinstance(array, MultiRowFormula):
      Trace.error('BeginCommand does not contain a MultiRowFormula')
      return False
    self.processarray(command, array, direction)

  def processarray(self, command, array, direction):
    "Process a bracket command with an array next to it."
    character = command.extracttext()
    command.output = EmptyOutput()
    Trace.debug('Character: ' + character)
    bracket = BigBracket(len(array.contents) - 1, character)
    for index, row in enumerate(array.rows):
      Trace.debug('Row: ' + unicode(row))
      cell = self.getbracketcell(bracket, index, direction)
      if self.directions[direction] == 1:
        row.contents.insert(0, cell)
      else:
        row.contents.append(cell)
      Trace.debug('Inserted ' + unicode(cell))

  def getbracketcell(self, bracket, index, align):
    "Get a piece of a bracket, already formatted."
    piece = bracket.getpiece(index)
    return TaggedBit().constant(piece, 'span class="bracket align-' + align + '"')

class BinomialCell(CommandBit):
  "A cell in a binomial function."

  def setfactory(self, factory):
    "Set the factory."
    self.output = TaggedOutput().settag('span class="binomcell"', True)
    return CommandBit.setfactory(self, factory)

  def parsebit(self, pos):
    "Parse a parameter and make it into a binomial cell."
    self.parseparameter(pos)

  def constant(self, constant):
    "Set a constant as only contents."
    self.contents = [FormulaConstant(constant)]

class BinomialRow(CommandBit):
  "A row for a binomial function."

  def create(self, left, middle, right):
    "Set the row contents."
    self.output = TaggedOutput().settag('span class="binomrow"', True)
    self.contents = [left, middle, right]
    return self

class BinomialFunction(CommandBit):
  "A binomial function which needs pretty decorating."

  commandmap = FormulaConfig.binomialfunctions

  def parsebit(self, pos):
    "Parse two parameters and decorate them."
    self.output = TaggedOutput().settag('span class="binomial"', True)
    leftbracket = BigBracket(3, self.translated[0])
    rightbracket = BigBracket(3, self.translated[1])
    for index in range(3):
      left = self.getpiece(leftbracket, index, 'left')
      right = self.getpiece(rightbracket, index, 'right')
      cell = BinomialCell().setfactory(self.factory)
      if index == 1:
        cell.constant(u' ')
      else:
        cell.parsebit(pos)
      self.add(BinomialRow().create(left, cell, right))

  def getpiece(self, bracket, index, align):
    "Get a piece of a bracket, already formatted."
    piece = bracket.getpiece(index)
    return TaggedBit().constant(piece, 'span class="bracket align-' + align + '"')


FormulaCommand.types += [
    DecoratingFunction, CombiningFunction, LimitCommand, BracketCommand,
    BinomialFunction,
    ]

FormulaProcessor.processors += [
    LimitsProcessor(), BracketProcessor(),
    ]

