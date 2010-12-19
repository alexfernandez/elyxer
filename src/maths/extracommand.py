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

class BracketCommand(OneParamFunction):
  "A command which defines a bracket."

  commandmap = FormulaConfig.bracketcommands

  def parsebit(self, pos):
    "Parse the bracket."
    OneParamFunction.parsebit(self, pos)

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
    return TaggedBit().constant(piece, 'span class="binombracket align-' + align + '"')


FormulaCommand.types += [
    DecoratingFunction, CombiningFunction, LimitCommand, BracketCommand,
    BinomialFunction,
    ]

