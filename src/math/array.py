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

class FormulaArray(CommandBit):
  "An array within a formula"

  piece = 'array'

  def __init__(self):
    self.output = TaggedOutput().settag('table class="formula"', True)
    self.valign = 'c'

  def parse(self, pos):
    "Parse the array"
    self.parsealignments(pos)
    while not pos.finished():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      self.add(row)
      self.parserowend(pos)

  def parsealignments(self, pos):
    "Parse the different alignments"
    # vertical
    vbracket = SquareBracket()
    if vbracket.detect(pos):
      vbracket.parseliteral(pos)
      self.original += vbracket.original
      self.valign = vbracket.contents
    # horizontal
    bracket = Bracket().parseliteral(pos)
    self.alignments = []
    for l in bracket.contents:
      self.alignments.append(l)
    self.original += bracket.original

  def parserowend(self, pos):
    "Parse the end of a row"
    endline = FormulaConfig.endings['Row']
    if not pos.checkfor(endline):
      Trace.error('No row end at ' + pos.remaining())
      self.addoriginal(pos.current(), pos)
      return
    self.addoriginal(endline, pos)

class FormulaCases(FormulaArray):
  "A cases statement"

  piece = 'cases'

  def __init__(self):
    FormulaCommand.__init__(self)
    self.output = TaggedOutput().settag('table class="cases"', True)
    self.alignments = ['l', 'l']

  def parse(self, pos):
    "Parse the cases"
    while not pos.finished():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      self.add(row)
      if pos.checkfor(ContainerConfig.endings['FormulaCases']):
        self.addoriginal(ContainerConfig.endings['FormulaCases'], pos)
        return
      self.parserowend(pos)

class BeginCommand(CommandBit):
  "A \\begin command and what it entails (array or cases)"

  commandmap = {FormulaConfig.array['begin']:''}

  innerbits = [FormulaArray(), FormulaCases()]

  def parse(self, pos):
    "Parse the begin command"
    bracket = Bracket().parseliteral(pos)
    self.original += bracket.original
    bit = self.findbit(bracket.contents)
    if not bit:
      return
    ending = FormulaConfig.array['ending'] + '{' + bracket.contents + '}'
    pos.pushending(ending)
    bit.parse(pos)
    self.add(bit)
    if not pos.checkfor(ending):
      Trace.error('No ending for ' + ending)
      return
    self.addoriginal(ending)
    return

  def findbit(self, piece):
    "Find the command bit corresponding to the \\begin{piece}"
    for bit in BeginCommand.innerbits:
      if bit.piece == piece:
        newbit = bit.clone()
        return newbit
    Trace.error('Unknown command \\begin{' + piece + '}')
    return None

FormulaFactory.bits += [BeginCommand()]

