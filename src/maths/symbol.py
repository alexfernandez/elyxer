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
# eLyXer big symbol generation.

from util.trace import Trace
from util.docparams import *
from conf.config import *
from maths.bits import *


class BigSymbol(object):
  "A big symbol generator."

  symbols = FormulaConfig.bigsymbols

  def __init__(self, symbol):
    "Create the big symbol."
    self.symbol = symbol

  def getpieces(self):
    "Get an array with all pieces."
    if not self.symbol in self.symbols:
      return [self.symbol]
    if self.smalllimit():
      return ['<span class="bigsymbol">' + self.symbol + '</span>']
    return self.symbols[self.symbol]

  def smalllimit(self):
    "Decide if the limit should be a small, one-line symbol."
    if not DocumentParameters.displaymode:
      return True
    if len(self.symbols[self.symbol]) == 1:
      return True
    return Options.simplemath

class BigBracket(BigSymbol):
  "A big bracket generator."

  def __init__(self, size, bracket):
    "Set the size and symbol for the bracket."
    self.size = size
    self.original = bracket
    if bracket in FormulaConfig.bigbrackets:
      self.pieces = FormulaConfig.bigbrackets[bracket]
    else:
      self.pieces = [bracket, bracket]

  def getpiece(self, index):
    "Return the nth piece for the bracket."
    if len(self.pieces) == 1:
      return self.pieces[0]
    if index == 0:
      return self.pieces[0]
    if index == self.size - 1:
      return self.pieces[-1]
    return self.pieces[1]

  def getcell(self, index, align):
    "Get the bracket piece as an array cell."
    piece = self.getpiece(index)
    return TaggedBit().constant(piece, 'span class="bracket align-' + align + '"')

  def getarray(self, align):
    "Get the bracket as an array."
    if self.size == 1:
      return self.getsinglebracket()
    rows = []
    for index in range(self.size):
      cell = self.getcell(index, align)
      rows.append(TaggedBit().complete([cell], 'span class="arrayrow"'))
    return TaggedBit().complete(rows, 'span class="array"')

  def getsinglebracket(self):
    "Return the bracket as a single sign."
    if self.original == '.':
      return TaggedBit().constant('', 'span class="emptydot"')
    return TaggedBit().constant(self.original, 'span class="symbol"')

class CasesBrace(BigBracket):
  "A big brace used for a case statement."

  def __init__(self, size):
    "Set the size for the brace."
    self.size = size

  def getpiece(self, index):
    "Get the nth piece for the brace."
    if index == 0:
      return u'⎧'
    if index == self.size - 1:
      return u'⎩'
    if index == (self.size - 1)/2:
      return u'⎨'
    return u'⎪'

