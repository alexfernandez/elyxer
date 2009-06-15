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
# Alex 20090207
# eLyXer formula processing

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from parse.formulaparse import *


class Formula(Container):
  "A LaTeX formula"

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TaggedOutput().settag('span class="formula"')

  def process(self):
    "Convert the formula to tags"
    pos = Position(self.contents[0])
    whole = WholeFormula()
    if not whole.detect(pos):
      Trace.error('Unknown formula at: ' + pos.remaining())
      constant = TaggedBit().constant(pos.remaining(), 'span class="unknown"')
      self.contents = [constant]
      return
    whole.parsebit(pos)
    whole.process()
    self.contents = [whole]
    if self.header[0] != 'inline':
      self.output.settag('div class="formula"', True)

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    # type can be 'alpha', 'number', 'font'
    self.type = None
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def glob(self, pos, check):
    "Glob a bit of text that satisfies a check"
    glob = ''
    while not pos.finished() and check(pos):
      glob += pos.current()
      pos.skip(pos.current())
    return glob

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

  def add(self, bit):
    "Add any kind of formula bit already processed"
    self.contents.append(bit)
    self.original += bit.original

  def skiporiginal(self, string, pos):
    "Skip a string and add it to the original formula"
    self.original += string
    if not pos.checkfor(string):
      Trace.error('String ' + string + ' not at ' + pos.remaining())
    pos.skip(string)

  def __unicode__(self):
    "Get a string representation"
    return self.__class__.__name__ + ' read in ' + self.original

class TaggedBit(FormulaBit):
  "A tagged string in a formula"

  def constant(self, constant, tag):
    "Set the constant and the tag"
    self.output = TaggedOutput().settag(tag)
    self.add(FormulaConstant(constant))
    return self

  def complete(self, contents, tag):
    "Set the constant and the tag"
    self.contents = contents
    self.output = TaggedOutput().settag(tag)
    return self

class FormulaConstant(FormulaBit):
  "A constant string in a formula"

  def __init__(self, string):
    "Set the constant string"
    FormulaBit.__init__(self)
    self.original = string
    self.output = FixedOutput()
    self.html = [string]

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  def __init__(self):
    FormulaBit.__init__(self)
    self.factory = FormulaFactory()

  def detect(self, pos):
    "Check in the factory"
    return self.factory.detectbit(pos)

  def parsebit(self, pos):
    "Parse with any formula bit"
    while self.factory.detectbit(pos):
      bit = self.factory.parsebit(pos)
      #Trace.debug(bit.original + ' -> ' + unicode(bit.gethtml()))
      self.add(bit)

  def process(self):
    "Process the whole formula"
    for index, bit in enumerate(self.contents):
      bit.process()
      if bit.type == 'alpha':
        # make variable
        self.contents[index] = TaggedBit().complete([bit], 'i')
      elif bit.type == 'font' and index > 0:
        last = self.contents[index - 1]
        if last.type == 'number':
          #separate
          last.contents.append(FormulaConstant(u' '))

class FormulaFactory(object):
  "Construct bits of formula"

  # bits will be appended later
  bits = []

  def detectbit(self, pos):
    "Detect if there is a next bit"
    if pos.finished():
      return False
    for bit in FormulaFactory.bits:
      if bit.detect(pos):
        return True
    return False

  def parsebit(self, pos):
    "Parse just one formula bit."
    for bit in FormulaFactory.bits:
      if bit.detect(pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.factory = self
        returnedbit = newbit.parsebit(pos)
        if returnedbit:
          return returnedbit
        return newbit
    Trace.error('Unrecognized formula at ' + pos.remaining())
    constant = FormulaConstant(pos.current())
    pos.skip(pos.current())
    return constant

