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
# Alex 20090427
# eLyXer arrays in formulae

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from math.formula import *
from math.command import *


class FormulaCell(FormulaCommand):
  "An array cell inside a row"

  def __init__(self, alignment):
    FormulaCommand.__init__(self)
    self.alignment = alignment
    self.output = TaggedOutput().settag('td class="formula-' + alignment +'"', True)

  def parse(self, pos):
    formula = WholeFormula()
    if not formula.detect(pos):
      Trace.error('Unexpected end of array cell at ' + pos.remaining())
      return
    formula.parse(pos)
    self.add(formula)

class FormulaRow(FormulaCommand):
  "An array row inside an array"

  def __init__(self, alignments):
    FormulaCommand.__init__(self)
    self.alignments = alignments
    self.output = TaggedOutput().settag('tr', True)

  def parse(self, pos):
    "Parse a whole row"
    for cell in self.parsecells(pos):
      cell.parse(pos)
      self.add(cell)

  def parsecells(self, pos):
    "Parse all cells, finish when count ends"
    cellseparator = FormulaConfig.array['cellseparator']
    for index, alignment in enumerate(self.alignments):
      if self.anybutlast(index):
        pos.pushending(cellseparator)
      yield FormulaCell(alignment)
      if self.anybutlast(index):
        if not pos.checkfor(cellseparator):
          Trace.error('No cell separator ' + cellseparator)
        else:
          self.original += pos.popending(cellseparator)

  def anybutlast(self, index):
    "Return true for all cells but the last"
    return index < len(self.alignments) - 1

class FormulaArray(CommandBit):
  "An array within a formula"

  piece = 'array'

  def parse(self, pos):
    "Parse the array"
    self.output = TaggedOutput().settag('table class="formula"', True)
    self.parsealignments(pos)
    for row in self.parserows(pos):
      row.parse(pos)
      self.add(row)

  def parserows(self, pos):
    "Parse all rows, finish when no more row ends"
    rowseparator = FormulaConfig.array['rowseparator']
    while True:
      pos.pushending(rowseparator, True)
      yield FormulaRow(self.alignments)
      if pos.checkfor(rowseparator):
        self.original += pos.popending(rowseparator)
      else:
        return

  def parsealignments(self, pos):
    "Parse the different alignments"
    # vertical
    self.valign = 'c'
    vbracket = SquareBracket()
    if vbracket.detect(pos):
      vbracket.parseliteral(pos)
      self.valign = vbracket.literal
      self.add(vbracket)
    # horizontal
    bracket = Bracket().parseliteral(pos)
    self.add(bracket)
    self.alignments = []
    for l in bracket.literal:
      self.alignments.append(l)

class FormulaCases(FormulaArray):
  "A cases statement"

  piece = 'cases'

  def parse(self, pos):
    "Parse the cases"
    self.output = TaggedOutput().settag('table class="cases"', True)
    self.alignments = ['l', 'l']
    for row in self.parserows(pos):
      row.parse(pos)
      self.add(row)

class BeginCommand(CommandBit):
  "A \\begin command and what it entails (array or cases)"

  commandmap = {FormulaConfig.array['begin']:''}

  innerbits = [FormulaArray(), FormulaCases()]

  def parse(self, pos):
    "Parse the begin command"
    bracket = Bracket().parseliteral(pos)
    self.original += bracket.literal
    Trace.debug('Remaining: ' + pos.remaining())
    bit = self.findbit(bracket.literal)
    if not bit:
      return
    ending = FormulaConfig.array['end'] + '{' + bracket.literal + '}'
    pos.pushending(ending)
    bit.parse(pos)
    self.add(bit)
    self.original += pos.popending(ending)

  def findbit(self, piece):
    "Find the command bit corresponding to the \\begin{piece}"
    for bit in BeginCommand.innerbits:
      if bit.piece == piece:
        newbit = bit.clone()
        return newbit
    Trace.error('Unknown command \\begin{' + piece + '}')
    return None

FormulaCommand.commandbits += [BeginCommand()]

