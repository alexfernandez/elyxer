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
    if self.smalllimit():
      pieces = self.translated[0:1]
    self.output = TaggedOutput().settag('span class="limits"')
    for piece in pieces:
      self.contents.append(TaggedBit().constant(piece, 'span class="limit"'))

  def smalllimit(self):
    "Decide if the limit should be a small, one-line symbol."
    if not DocumentParameters.displaymode:
      return True
    if len(self.translated) == 1:
      return True
    return Options.simplemath

class LimitsProcessor(MathsProcessor):
  "A processor for limits inside an element."

  def process(self, contents, index):
    "Process the limits for an element."
    if Options.simplemath:
      return
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

  def process(self, contents, index):
    "Convert the bracket using Unicode pieces, if possible."
    if Options.simplemath:
      return
    if self.checkleft(contents, index):
      return self.processleft(contents, index)
    if self.checkright(contents, index):
      return self.processright(contents, index)

  def processleft(self, contents, index):
    "Process a left bracket."
    if self.checkarray(contents, index, 1):
      return
    rightindex = self.findright(contents, index + 1)
    if not rightindex:
      return
    size = self.findmax(contents, index, rightindex)
    self.resize(contents[index], size)
    self.resize(contents[rightindex], size)

  def processright(self, contents, index):
    "Process a right bracket."
    if self.checkarray(contents, index, -1):
      return

  def checkleft(self, contents, index):
    "Check if the command at the given index is left."
    return self.checkdirection(contents[index], '\\left')
  
  def checkright(self, contents, index):
    "Check if the command at the given index is right."
    return self.checkdirection(contents[index], '\\right')

  def checkdirection(self, bit, command):
    "Check if the given bit is the desired bracket command."
    if not isinstance(bit, BracketCommand):
      return False
    return bit.command == command

  def checkarray(self, contents, index, direction):
    "Check for an array in the given direction, process it."
    command = contents[index]
    newindex = index + direction
    if newindex < 0 or newindex >= len(contents):
      return False
    begin = contents[newindex]
    if not isinstance(begin, BeginCommand):
      return False
    array = begin.array
    if not isinstance(array, MultiRowFormula):
      Trace.error('BeginCommand does not contain a MultiRowFormula')
      return False
    self.processarray(command, array, direction)
    return True

  def processarray(self, command, array, direction):
    "Process a bracket command with an array next to it."
    character = command.extracttext()
    command.output = EmptyOutput()
    bracket = BigBracket(len(array.rows), character)
    alignment = command.command.replace('\\', '')
    for index, row in enumerate(array.rows):
      cell = bracket.getcell(index, alignment)
      if direction == 1:
        row.contents.insert(0, cell)
      else:
        row.contents.append(cell)

  def findright(self, contents, index):
    "Find the right bracket starting at the given index, or 0."
    depth = 1
    while index < len(contents):
      if self.checkleft(contents, index):
        depth += 1
      if self.checkright(contents, index):
        depth -= 1
      if depth == 0:
        return index
      index += 1
    return None

  def findmax(self, contents, leftindex, rightindex):
    "Find the max size of the contents between the two given indices."
    return 1

  def resize(self, command, size):
    "Resize a bracket command to the given size."
    character = command.extracttext()
    bracket = BigBracket(size, character)
    alignment = command.command.replace('\\', '')
    command.output = ContentsOutput()
    command.contents = [bracket.getarray(alignment)]

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

  def complete(self, contents):
    "Set the row contents."
    self.output = TaggedOutput().settag('span class="binomrow"', True)
    self.contents = contents
    return self

class BinomialFunction(CommandBit):
  "A binomial function which needs pretty decorating."

  commandmap = FormulaConfig.binomialfunctions

  def parsebit(self, pos):
    "Parse two parameters and decorate them."
    self.add(BigBracket(1, self.translated[0]).getsinglebracket())
    self.rows = []
    for index in range(3):
      cell = self.factory.create(BinomialCell)
      if index == 1:
        cell.constant(u' ')
      else:
        cell.parsebit(pos)
      self.rows.append(self.factory.create(BinomialRow).complete([cell]))
    self.add(TaggedBit().complete(self.rows, 'span class="binomial"', True))
    self.add(BigBracket(1, self.translated[1]).getsinglebracket())

class BinomialProcessor(MathsProcessor):
  "A processor for binomial functions."

  def process(self, contents, index):
    "Convert the binomial using Unicode brackets."
    if Options.simplemath:
      return
    binom = contents[index]
    if not isinstance(binom, BinomialFunction):
      return
    leftbracket = BigBracket(3, binom.translated[0])
    rightbracket = BigBracket(3, binom.translated[1])
    for index, row in enumerate(binom.rows):
      left = leftbracket.getcell(index, 'l')
      right = rightbracket.getcell(index, 'r')
      row.contents.insert(0, left)
      row.contents.append(right)
    binom.contents = binom.contents[1:-1]


FormulaCommand.types += [
    DecoratingFunction, CombiningFunction, LimitCommand, BracketCommand,
    BinomialFunction,
    ]

FormulaProcessor.processors += [
    LimitsProcessor(), BracketProcessor(), BinomialProcessor(),
    ]

