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
from container import *
from util.trace import Trace
from general import *
from formula import *


class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"
 
  def parsebracket(self, pos):
    "Parse a bracket at the current position"
    bracket = Bracket()
    if not bracket.detect(pos):
      Trace.error('Expected {} at: ' + pos.remaining())
      return
    bracket.parse(pos)
    self.add(bracket)
    return bracket

  def findcommand(self, pos, map):
    "Find any type of command in a map"
    command = self.findalphacommand(pos)
    if command and command in map:
      return command
    command = self.findsymbolcommand(pos)
    if command and command in map:
      return command
    return None

  def findalphacommand(self, oldpos):
    "Find a command with \\alpha"
    pos = oldpos.clone()
    if pos.current() != '\\':
      return None
    pos.skip('\\')
    if pos.isout():
      return None
    if not pos.current().isalpha():
      return None
    command = self.glob(pos, lambda(p): p.current().isalpha())
    return '\\' + command

  def findsymbolcommand(self, oldpos):
    "Find a command made with optional \\alpha and one symbol"
    pos = oldpos.clone()
    backslash = ''
    if pos.current() == '\\':
      backslash = '\\'
      pos.skip('\\')
    alpha = self.glob(pos, lambda(p): p.current().isalpha())
    pos.skip(alpha)
    if pos.isout():
      return None
    return backslash + alpha + pos.current()

  def process(self):
    "Process the internals"
    for bit in self.contents:
      bit.process()

class EmptyCommand(FormulaCommand):
  "An empty command (without parameters)"

  def detect(self, pos):
    "Detect the start of an empty command"
    if self.findcommand(pos, FormulaConfig.commands):
      return True
    if self.findcommand(pos, FormulaConfig.alphacommands):
      return True
    return False

  def parse(self, pos):
    "Parse a command without parameters"
    command = self.findcommand(pos, FormulaConfig.commands)
    if command:
      self.addtranslated(command, FormulaConfig.commands, pos)
      return
    command = self.findcommand(pos, FormulaConfig.alphacommands)
    if command:
      self.addtranslated(command, FormulaConfig.alphacommands, pos)
      self.type = 'alpha'
      return
    Trace.error('No command found in ' + pos.remaining())
    return

  def addtranslated(self, command, map, pos):
    "Add a command and find its translation"
    translated = map[command]
    self.addoriginal(command, pos)
    self.contents = [FormulaConstant(translated)]

class OneParamFunction(FormulaCommand):
  "A function of one parameter"

  functions = FormulaConfig.onefunctions

  def detect(self, pos):
    "Detect the start of the function"
    if self.findcommand(pos, self.functions):
      return True
    return False

  def parse(self, pos):
    "Parse a function with one parameter"
    command = self.findcommand(pos, self.functions)
    self.addoriginal(command, pos)
    self.output = TaggedOutput().settag(self.functions[command])
    self.parsebracket(pos)

class FontFunction(OneParamFunction):
  "A function of one parameter that changes the font"

  functions = FormulaConfig.fontfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  functions = FormulaConfig.decoratingfunctions

  def parse(self, pos):
    "Parse a decorating function"
    command = self.findcommand(pos, FormulaConfig.decoratingfunctions)
    self.addoriginal(command, pos)
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.type = 'alpha'
    symbol = FormulaConfig.decoratingfunctions[command]
    tagged = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.contents.append(tagged)
    bracket = self.parsebracket(pos)
    bracket.output = TaggedOutput().settag('span class="undersymbol"')
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = FormulaConfig.alphacommands[self.original]

class TwoParamFunction(FormulaCommand):
  "A function of two parameters"

  def detect(self, pos):
    "Detect the start of the function"
    if self.findcommand(pos, FormulaConfig.twofunctions):
      return True
    return False

  def parse(self, pos):
    "Parse a function of two parameters"
    command = self.findcommand(pos, FormulaConfig.twofunctions)
    self.addoriginal(command, pos)
    tags = FormulaConfig.twofunctions[command]
    self.output = TaggedOutput().settag(tags[0])
    bracket1 = self.parsebracket(pos)
    if not bracket1:
      return
    bracket1.output = TaggedOutput().settag(tags[1])
    bracket2 = self.parsebracket(pos)
    if not bracket2:
      return
    bracket2.output = TaggedOutput().settag(tags[2])

class Bracket(FormulaBit):
  "A {} bracket inside a formula"

  def detect(self, pos):
    "Detect the start of a bracket"
    return pos.checkfor('{')

  def parse(self, pos):
    "Parse the bracket"
    self.addoriginal('{', pos)
    self.inside = WholeFormula()
    if not self.inside.detect(pos):
      Trace.error('Dangling {')
      return
    self.inside.parse(pos)
    self.add(self.inside)
    if pos.isout() or pos.current() != '}':
      Trace.error('Missing } in ' + pos.remaining())
      return
    self.addoriginal('}', pos)

  def process(self):
    "Process the bracket"
    self.inside.process()

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

  start = '\\begin{array}'
  ending = '\\end{array}'

  def __init__(self):
    FormulaCommand.__init__(self)
    self.output = TaggedOutput().settag('table class="formula"', True)
    self.valign = 'c'

  def detect(self, pos):
    "Detect an array"
    if not pos.checkfor(FormulaArray.start):
      return False
    return True

  def parse(self, pos):
    "Parse the array"
    self.addoriginal(FormulaArray.start, pos)
    self.parsealignments(pos)
    self.contents.pop()
    while not pos.isout():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      self.add(row)
      if pos.checkfor(FormulaArray.ending):
        self.addoriginal(FormulaArray.ending, pos)
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

WholeFormula.bits += [
    EmptyCommand(), OneParamFunction(), DecoratingFunction(),
    TwoParamFunction(), FormulaArray(), FontFunction(), 
    ]

