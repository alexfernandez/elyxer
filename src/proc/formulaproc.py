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
# Alex 20101111
# eLyXer formulae processing.

from util.trace import *
from conf.config import *
from maths.bits import *


class FormulaProcessor(object):
  "A processor specifically for formulas."

  def process(self, bit):
    "Process the contents of every formula bit, recursively."
    self.processcontents(bit)
    self.processlimits(bit)
    self.traversewhole(bit)

  def processcontents(self, bit):
    "Process the contents of a formula bit."
    if not isinstance(bit, FormulaBit):
      return
    bit.process()
    for element in bit.contents:
      self.processcontents(element)

  def processlimits(self, bit):
    "Process any limits in a formula bit."
    if not isinstance(bit, FormulaBit):
      return
    for index, element in enumerate(bit.contents):
      self.checklimited(bit.contents, index)
      self.processlimits(element)

  def checklimited(self, contents, index):
    "Check for a command with limits"
    bit = contents[index]
    if not hasattr(bit, 'command'):
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
    if not hasattr(bit, 'command'):
      return
    if not bit.command in FormulaConfig.limits['operands']:
      return False
    bit.output.tag += ' class="bigsymbol"'
    return True

  def traversewhole(self, formula):
    "Traverse over the contents to alter variables and space units."
    last = None
    for bit, contents in self.traverse(formula):
      if bit.type == 'alpha':
        self.italicize(bit, contents)
      elif bit.type == 'font' and last and last.type == 'number':
        bit.contents.insert(0, FormulaConstant(u' '))
      last = bit

  def traverse(self, bit):
    "Traverse a formula and yield a flattened structure of (bit, list) pairs."
    for element in bit.contents:
      if hasattr(element, 'type') and element.type:
        yield (element, bit.contents)
      elif isinstance(element, FormulaBit):
        for pair in self.traverse(element):
          yield pair

  def italicize(self, bit, contents):
    "Italicize the given bit of text."
    index = contents.index(bit)
    contents[index] = TaggedBit().complete([bit], 'i')


