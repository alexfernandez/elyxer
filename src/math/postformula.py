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

  limited = ['\\sum', '\\int', '\\intop']
  limits = ['^', '_']

  def postprocess(self, current, last):
    "Postprocess any formulae"
    for formula in current.searchall(Formula):
      self.postcontents(formula.contents)
    return current

  def postcontents(self, contents):
    "Search for sum or integral"
    for index, bit in enumerate(contents):
      self.checklimited(contents, index)
      self.checkroot(contents, index)
      if isinstance(bit, FormulaBit):
        self.postcontents(bit.contents)

  def checklimited(self, contents, index):
    "Check for a command with limits"
    bit = contents[index]
    if not hasattr(bit, 'command'):
      return
    if not bit.command in PostFormula.limited:
      return
    limits = self.findlimits(contents, index + 1)
    limits.reverse()
    if len(limits) == 0:
      return
    tagged = TaggedText().complete(limits, 'span class="limits"')
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
      return False
    if not bit.command in PostFormula.limits:
      return False
    bit.output.tag += ' class="bigsymbol"'
    return True

  def checkroot(self, contents, index):
    "Check for a root, insert the radical in front"
    bit = contents[index]
    if not hasattr(bit, 'original'):
      return
    if not bit.original.startswith('\\sqrt'):
      return
    tagged = TaggedText().constant(u'√', 'span class="radical"')
    group = Group().contents([tagged, bit])
    contents[index] = group

Postprocessor.unconditional.append(PostFormula)

