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

from gen.container import *
from util.trace import Trace
from util.clone import *
from conf.config import *
from parse.formulaparse import *


class Formula(Container):
  "A LaTeX formula"

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TaggedOutput().settag('span class="formula"')

  def process(self):
    "Convert the formula to tags"
    if self.header[0] != 'inline':
      self.output.settag('div class="formula"', True)
    if Options.jsmath:
      if self.header[0] != 'inline':
        self.output = TaggedOutput().settag('div class="math"')
      else:
        self.output = TaggedOutput().settag('span class="math"')
      self.contents = [Constant(self.parsed)]
      return
    if Options.mathjax:
      self.output.tag = 'span class="MathJax_Preview"'
      tag = 'script type="math/tex'
      if self.header[0] != 'inline':
        tag += ';mode=display'
      self.contents = [TaggedText().constant(self.parsed, tag + '"', True)]
      return
    whole = FormulaFactory().parseformula(self.parsed)
    self.processcontents(whole)
    whole.parent = self
    self.contents = [whole]

  def processcontents(self, bit):
    "Process the contents of every formula bit."
    bit.process()
    for element in bit.contents:
      if isinstance(element, FormulaBit):
        self.processcontents(element)

  def __unicode__(self):
    "Return a printable representation."
    if self.partkey and self.partkey.number:
      return 'Formula (' + self.partkey.number + ')'
    return 'Unnumbered formula'

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    # type can be 'alpha', 'number', 'font'
    self.type = None
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def setfactory(self, factory):
    "Set the internal formula factory."
    self.factory = factory
    return self

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

  def clone(self):
    "Return a copy of itself."
    return self.factory.parseformula(self.original)

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

  def clone(self):
    "Return a copy of itself."
    return FormulaConstant(self.original)

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  def detect(self, pos):
    "Check in the factory"
    return self.factory.detectany(pos)

  def parsebit(self, pos):
    "Parse with any formula bit"
    while self.factory.detectany(pos):
      bit = self.factory.parseany(pos)
      #Trace.debug(bit.original + ' -> ' + unicode(bit.gethtml()))
      self.add(bit)

class FormulaFactory(object):
  "Construct bits of formula"

  # bit types will be appended later
  types = []
  ignoredtypes = []
  defining = False

  def __init__(self):
    "Initialize the map of instances."
    self.instances = dict()

  def detectany(self, pos):
    "Detect if there is a next bit"
    if pos.finished():
      return False
    for type in FormulaFactory.types:
      if self.detecttype(type, pos):
        return True
    return False

  def detecttype(self, type, pos):
    "Detect a bit of a given type."
    self.clearignored(pos)
    if pos.finished():
      return False
    return self.instance(type).detect(pos)

  def instance(self, type):
    "Get an instance of the given type."
    if not type in self.instances or not self.instances[type]:
      self.instances[type] = self.create(type)
    return self.instances[type]

  def create(self, type):
    "Create a new formula bit of the given type."
    return Cloner.create(type).setfactory(self)

  def clearignored(self, pos):
    "Clear all ignored types."
    while not pos.finished():
      if not self.clearany(pos):
        return

  def clearany(self, pos):
    "Cleary any ignored type."
    for type in self.ignoredtypes:
      if self.instance(type).detect(pos):
        self.parsetype(type, pos)
        return True
    return False

  def parseany(self, pos):
    "Parse any formula bit at the current location."
    for type in FormulaFactory.types:
      if self.detecttype(type, pos):
        return self.parsetype(type, pos)
    Trace.error('Unrecognized formula at ' + pos.identifier())
    return FormulaConstant(pos.skipcurrent())

  def parsetype(self, type, pos):
    "Parse the given type and return it."
    bit = self.instance(type)
    self.instances[type] = None
    returnedbit = bit.parsebit(pos)
    if returnedbit:
      return returnedbit.setfactory(self)
    return bit

  def parseformula(self, formula):
    "Parse a string of text that contains a whole formula."
    pos = TextPosition(formula)
    whole = self.create(WholeFormula)
    if whole.detect(pos):
      whole.parsebit(pos)
      return whole
    # no formula found
    if not pos.finished():
      Trace.error('Unknown formula at: ' + pos.identifier())
      whole.add(TaggedBit().constant(formula, 'span class="unknown"'))
    return whole

