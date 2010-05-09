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
from util.clone import *
from conf.config import *
from parse.formulaparse import *


class Formula(Container):
  "A LaTeX formula"

  initializations = []

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TaggedOutput().settag('span class="formula"')
    self.initialize()

  def process(self):
    "Convert the formula to tags"
    if self.header[0] != 'inline':
      self.output.settag('div class="formula"', True)
    if Options.jsmath:
      self.output.tag = self.output.tag.replace('formula', 'math')
      self.contents = [Constant(self.contents[0])]
      return
    if Options.mathjax:
      self.output.tag = 'span class="MathJax_Preview"'
      tag = 'script type="math/tex'
      if self.header[0] != 'inline':
        tag += ';mode=display'
      self.contents = [TaggedText().constant(self.contents[0], tag + '"', True)]
      return
    whole = WholeFormula.parse(self.contents[0])
    self.contents = [whole]
    whole.parent = self

  def initialize(self):
    "Perform any necessary initializations."
    "Introduced to process any macros in the preamble."
    for init in Formula.initializations:
      init()

  def __unicode__(self):
    "Return a printable representation."
    if hasattr(self, 'number'):
      return 'Formula (' + self.number + ')'
    return 'Unnumbered formula'

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    # type can be 'alpha', 'number', 'font'
    self.type = None
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def add(self, bit):
    "Add any kind of formula bit already processed"
    self.contents.append(bit)
    self.original += bit.original
    bit.parent = self

  def skiporiginal(self, string, pos):
    "Skip a string and add it to the original formula"
    self.original += string
    if not pos.checkskip(string):
      Trace.error('String ' + string + ' not at ' + pos.identifier())

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

class FormulaConstant(Constant):
  "A constant string in a formula"

  def __init__(self, string):
    "Set the constant string"
    Constant.__init__(self, string)
    self.original = string
    self.type = None

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
      # no units processing
      continue
      if bit.type == 'alpha':
        # make variable
        self.contents[index] = TaggedBit().complete([bit], 'i')
      elif bit.type == 'font' and index > 0:
        last = self.contents[index - 1]
        if last.type == 'number':
          #separate
          last.contents.append(FormulaConstant(u' '))

  def parse(cls, formula):
    "Parse a whole formula and return it."
    pos = TextPosition(formula)
    whole = WholeFormula()
    if not whole.detect(pos):
      Trace.error('Unknown formula at: ' + pos.identifier())
      return TaggedBit().constant(pos.identifier(), 'span class="unknown"')
    whole.parsebit(pos)
    whole.process()
    return whole

  parse = classmethod(parse)

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
        newbit = Cloner.clone(bit)
        newbit.factory = self
        returnedbit = newbit.parsebit(pos)
        if returnedbit:
          return returnedbit
        return newbit
    Trace.error('Unrecognized formula at ' + pos.identifier())
    return FormulaConstant(pos.currentskip())

