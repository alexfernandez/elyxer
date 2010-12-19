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

from gen.container import *
from util.trace import Trace
from util.clone import *
from conf.config import *
from maths.formula import *
from maths.command import *
from maths.symbol import *


class FormulaEquation(CommandBit):
  "A simple numbered equation."

  piece = 'equation'

  def parsebit(self, pos):
    "Parse the array"
    self.output = ContentsOutput()
    self.add(self.factory.parsetype(WholeFormula, pos))

class FormulaCell(FormulaCommand):
  "An array cell inside a row"

  def setalignment(self, alignment):
    self.alignment = alignment
    self.output = TaggedOutput().settag('span class="arraycell align-' + alignment +'"', True)
    return self

  def parsebit(self, pos):
    self.factory.clearignored(pos)
    if pos.finished():
      return
    if not self.factory.detecttype(WholeFormula, pos):
      Trace.error('Unexpected end of array cell at ' + pos.identifier())
      pos.skip(pos.current())
      return
    self.add(self.factory.parsetype(WholeFormula, pos))

class FormulaRow(FormulaCommand):
  "An array row inside an array"

  cellseparator = FormulaConfig.array['cellseparator']

  def setalignments(self, alignments):
    self.alignments = alignments
    self.output = TaggedOutput().settag('span class="arrayrow"', True)
    return self

  def parsebit(self, pos):
    "Parse a whole row"
    index = 0
    pos.pushending(self.cellseparator, optional=True)
    while not pos.finished():
      alignment = self.alignments[index % len(self.alignments)]
      cell = self.factory.create(FormulaCell).setalignment(alignment)
      cell.parsebit(pos)
      self.add(cell)
      index += 1
      pos.checkskip(self.cellseparator)
    if len(self.contents) == 0:
      self.output = EmptyOutput()

class MultiRowFormula(CommandBit):
  "A formula with multiple rows."

  def parserows(self, pos):
    "Parse all rows, finish when no more row ends"
    self.rows = []
    first = True
    for row in self.iteraterows(pos):
      if first:
        first = False
      else:
        # intersparse empty rows
        self.addempty()
      row.parsebit(pos)
      self.addrow(row)

  def iteraterows(self, pos):
    "Iterate over all rows, end when no more row ends"
    rowseparator = FormulaConfig.array['rowseparator']
    while True:
      pos.pushending(rowseparator, True)
      row = self.factory.create(FormulaRow)
      yield row.setalignments(self.alignments)
      if pos.checkfor(rowseparator):
        self.original += pos.popending(rowseparator)
      else:
        return

  def addempty(self):
    "Add an empty row."
    row = FormulaRow().setalignments(self.alignments)
    for alignment in self.alignments:
      cell = self.factory.create(FormulaCell).setalignment(alignment)
      cell.add(FormulaConstant(u' '))
      row.add(cell)
    self.addrow(row)

  def addrow(self, row):
    "Add a row to the contents and to the list of rows."
    self.rows.append(row)
    self.add(row)

class FormulaArray(MultiRowFormula):
  "An array within a formula"

  piece = 'array'

  def parsebit(self, pos):
    "Parse the array"
    self.output = TaggedOutput().settag('span class="array"', True)
    self.parsealignments(pos)
    self.parserows(pos)

  def parsealignments(self, pos):
    "Parse the different alignments"
    # vertical
    self.valign = 'c'
    literal = self.parsesquareliteral(pos)
    if literal:
      self.valign = literal
    # horizontal
    literal = self.parseliteral(pos)
    self.alignments = []
    for l in literal:
      self.alignments.append(l)

class FormulaMatrix(MultiRowFormula):
  "A matrix (array with center alignment)."

  piece = 'matrix'

  def parsebit(self, pos):
    "Parse the matrix, set alignments to 'c'."
    self.output = TaggedOutput().settag('span class="array"', True)
    self.valign = 'c'
    self.alignments = ['c']
    self.parserows(pos)

class FormulaCases(MultiRowFormula):
  "A cases statement"

  piece = 'cases'

  def parsebit(self, pos):
    "Parse the cases"
    self.output = TaggedOutput().settag('span class="bracketcases"', True)
    self.alignments = ['l', 'l']
    self.parserows(pos)
    for row in self.contents:
      for cell in row.contents:
        cell.output.settag('span class="case align-l"', True)
        cell.contents.append(FormulaConstant(u' '))
    brace = CasesBrace(len(self.contents))
    for index, row in enumerate(self.rows):
      row.contents.insert(0, brace.getcell(index, 'l'))

class EquationEnvironment(MultiRowFormula):
  "A \\begin{}...\\end equation environment with rows and cells."

  def parsebit(self, pos):
    "Parse the whole environment."
    self.output = TaggedOutput().settag('span class="environment"', True)
    environment = self.piece.replace('*', '')
    if environment in FormulaConfig.environments:
      self.alignments = FormulaConfig.environments[environment]
    else:
      Trace.error('Unknown equation environment ' + self.piece)
      self.alignments = ['l']
    self.parserows(pos)

class BeginCommand(CommandBit):
  "A \\begin{}...\end command and what it entails (array, cases, aligned)"

  commandmap = {FormulaConfig.array['begin']:''}

  types = [FormulaEquation, FormulaArray, FormulaCases, FormulaMatrix]

  def parsebit(self, pos):
    "Parse the begin command"
    command = self.parseliteral(pos)
    bit = self.findbit(command)
    ending = FormulaConfig.array['end'] + '{' + command + '}'
    pos.pushending(ending)
    bit.parsebit(pos)
    self.add(bit)
    self.array = bit
    self.original += pos.popending(ending)

  def findbit(self, piece):
    "Find the command bit corresponding to the \\begin{piece}"
    for type in BeginCommand.types:
      if piece.replace('*', '') == type.piece:
        return self.factory.create(type)
    bit = self.factory.create(EquationEnvironment)
    bit.piece = piece
    return bit

FormulaCommand.types += [BeginCommand]

