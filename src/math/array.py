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
    formula = WholeFormula().setarraymode()
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
    for i in self.alignments:
      cell = FormulaCell(i)
      cell.parse(pos)
      self.add(cell)
      if pos.checkfor('&'):
        self.addoriginal('&', pos)

class FormulaArray(FormulaCommand):
  "An array within a formula"

  def __init__(self):
    FormulaCommand.__init__(self)
    self.output = TaggedOutput().settag('table class="formula"', True)
    self.valign = 'c'

  def detect(self, pos):
    "Detect an array"
    if not pos.checkfor(FormulaConfig.starts[FormulaArray.__name__]):
      return False
    return True

  def parse(self, pos):
    "Parse the array"
    self.addoriginal(FormulaConfig.starts[FormulaArray.__name__], pos)
    self.parsealignments(pos)
    self.contents.pop()
    while not pos.isout():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      self.add(row)
      if pos.checkfor(ContainerConfig.endings[FormulaArray.__name__]):
        self.addoriginal(ContainerConfig.endings[FormulaArray.__name__], pos)
        return
      self.parserowend(pos)

  def parsealignments(self, pos):
    "Parse the different alignments"
    # vertical
    if pos.checkfor('['):
      self.addoriginal('[', pos)
      self.valign = pos.current()
      self.addoriginal(self.valign, pos)
      if not pos.checkfor(']'):
        Trace.error('Vertical alignment ' + self.valign + ' not closed')
      self.addoriginal(']', pos)
    # horizontal
    bracket = self.parsebracket(pos)
    if not bracket:
      Trace.error('No alignments for array in ' + pos.remaining())
      return
    self.alignments = []
    for l in bracket.original[1:-1]:
      self.alignments.append(l)

  def parserowend(self, pos):
    "Parse the end of a row"
    if not pos.checkfor('\\\\'):
      Trace.error('No row end at ' + pos.remaining())
      self.addoriginal(pos.current(), pos)
      return
    self.addoriginal('\\\\', pos)

class FormulaCases(FormulaArray):
  "A cases statement"

  def __init__(self):
    FormulaCommand.__init__(self)
    self.output = TaggedOutput().settag('table class="cases"', True)
    self.alignments = ['l', 'l']

  def detect(self, pos):
    "Detect a cases statement"
    if not pos.checkfor(FormulaConfig.starts[FormulaCases.__name__]):
      return False
    return True

  def parse(self, pos):
    "Parse the cases"
    self.addoriginal(FormulaConfig.starts[FormulaCases.__name__], pos)
    while not pos.isout():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      self.add(row)
      if pos.checkfor(ContainerConfig.endings[FormulaCases.__name__]):
        self.addoriginal(ContainerConfig.endings[FormulaCases.__name__], pos)
        return
      self.parserowend(pos)

WholeFormula.bits += [FormulaArray(), FormulaCases()]

