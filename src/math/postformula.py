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
from post.postprocess import *


class PostFormula(object):
  "Postprocess a formula"

  processedclass = Formula
  generator = NumberGenerator()

  def postprocess(self, formula, last):
    "Postprocess any formulae"
    self.postcontents(formula.contents)
    self.posttraverse(formula)
    return formula

  def postcontents(self, contents):
    "Search for sum or integral"
    for index, bit in enumerate(contents):
      self.checklimited(contents, index)
      self.checknumber(contents, index)
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

  def checknumber(self, contents, index):
    "Check for equation numbering"
    label = contents[index]
    if not isinstance(label, LabelFunction):
      return
    if len(label.contents) < 1 or not isinstance(label.contents[0], Bracket):
      Trace.error('Wrong contents for label ' + unicode(label))
      return
    bracket = label.contents[0]
    labelname = bracket.literal
    number = '(' + PostFormula.generator.generate(1) + ') '
    Label.names[labelname] = label
    tag = label.output.tag.replace('#', labelname)
    label.output.settag(tag)
    label.contents = [FormulaConstant(number)]
    # place number at the beginning
    del contents[index]
    contents.insert(0, label)

  def posttraverse(self, formula):
    "Traverse over the contents to alter variables and space units."
    flat = self.flatten(formula)
    last = None
    for bit, contents in self.traverse(flat):
      if bit.type == 'alpha':
        self.italicize(bit, contents)
      elif bit.type == 'font' and last and last.type == 'number':
        last.contents.append(FormulaConstant(u' '))
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

