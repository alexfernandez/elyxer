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
# Alex 20090422
# eLyXer postprocessor for formulae

from util.trace import Trace
from math.command import *
from math.array import *
from post.postprocess import *
from ref.link import *
from ref.label import *


class PostFormula(object):
  "Postprocess a formula"

  processedclass = Formula

  def postprocess(self, last, formula, next):
    "Postprocess any formulae"
    self.postnumbering(formula)
    self.postcontents(formula.contents)
    self.posttraverse(formula)
    return formula

  def postnumbering(self, formula):
    "Check if it's a numbered equation, insert number."
    if formula.header[0] != 'numbered':
      return
    functions = formula.searchremove(LabelFunction)
    if len(functions) == 0:
      label = self.createlabel(formula)
    elif len(functions) == 1:
      label = self.createlabel(formula, functions[0])
    if len(functions) <= 1:
      label.parent = formula
      formula.contents.insert(0, label)
      return
    for function in functions:
      label = self.createlabel(formula, function)
      row = self.searchrow(function)
      label.parent = row
      row.contents.insert(0, label)

  def createlabel(self, formula, function = None):
    "Create a new label for a formula."
    "Add a label to a formula."
    number = NumberGenerator.instance.generatechaptered('formula')
    entry = '(' + number + ')'
    if not hasattr(formula, number) or not formula.number:
      formula.number = number
      formula.entry = entry
    if not function:
      label = Label()
      label.create(entry + ' ', 'eq-' + number, type="eqnumber")
    else:
      label = function.label
      label.complete(entry + ' ')
    return label

  def searchrow(self, function):
    "Search for the row that contains the label function."
    if isinstance(function.parent, Formula) or isinstance(function.parent, FormulaRow):
      return function.parent
    return self.searchrow(function.parent)

  def postcontents(self, contents):
    "Search for sum or integral"
    for index, bit in enumerate(contents):
      self.checklimited(contents, index)
      if isinstance(bit, FormulaBit):
        self.postcontents(bit.contents)

  def checklimited(self, contents, index):
    "Check for a command with limits"
    bit = contents[index]
    if not isinstance(bit, EmptyCommand):
      return
    if not bit.command in FormulaConfig.limits['commands']:
      return
    limits = self.findlimits(contents, index + 1)
    limits.reverse()
    if len(limits) == 0:
      return
    tagged = TaggedBit().complete(limits, 'span class="limits"')
    contents.insert(index + 1, tagged)

  def findlimits(self, contents, index):
    "Find the limits for the command"
    limits = []
    while index < len(contents):
      if not self.checklimits(contents, index):
        return limits
      limits.append(contents[index])
      del contents[index]
    return limits

  def checklimits(self, contents, index):
    "Check for a command making the limits"
    bit = contents[index]
    if not isinstance(bit, SymbolFunction):
      return False
    if not bit.command in FormulaConfig.limits['operands']:
      return False
    bit.output.tag += ' class="bigsymbol"'
    return True

  def posttraverse(self, formula):
    "Traverse over the contents to alter variables and space units."
    flat = self.flatten(formula)
    last = None
    for bit, contents in self.traverse(flat):
      if bit.type == 'alpha':
        self.italicize(bit, contents)
      elif bit.type == 'font' and last and last.type == 'number':
        bit.contents.insert(0, FormulaConstant(u' '))
        # last.contents.append(FormulaConstant(u' '))
      last = bit

  def flatten(self, bit):
    "Return all bits as a single list of (bit, list) pairs."
    flat = []
    for element in bit.contents:
      if element.type:
        flat.append((element, bit.contents))
      elif isinstance(element, FormulaBit):
        flat += self.flatten(element)
    return flat

  def traverse(self, flattened):
    "Traverse each (bit, list) pairs of the formula."
    for element in flattened:
      yield element

  def italicize(self, bit, contents):
    "Italicize the given bit of text."
    index = contents.index(bit)
    contents[index] = TaggedBit().complete([bit], 'i')

Postprocessor.stages.append(PostFormula)

