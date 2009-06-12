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
    whole.parse(pos)
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

  def glob(self, oldpos, check):
    "Glob a bit of text that satisfies a check"
    glob = ''
    pos = oldpos.clone()
    while not pos.isout() and check(pos):
      glob += pos.current()
      pos.skip(pos.current())
    return glob

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

  def addconstant(self, string, pos):
    "add a constant string"
    self.contents.append(FormulaConstant(string))
    self.addoriginal(string, pos)

  def add(self, bit):
    "Add any kind of formula bit already processed"
    self.contents.append(bit)
    self.original += bit.original

  def addoriginal(self, string, pos):
    "Add a constant to the original formula only"
    self.original += string
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

class RawText(FormulaBit):
  "A bit of text inside a formula"

  def detect(self, pos):
    "Detect a bit of raw text"
    return pos.current().isalpha()

  def parse(self, pos):
    "Parse alphabetic text"
    alpha = self.glob(pos, lambda(p): p.current().isalpha())
    self.addconstant(alpha, pos)
    self.type = 'alpha'

class FormulaSymbol(FormulaBit):
  "A symbol inside a formula"

  modified = FormulaConfig.modified
  unmodified = FormulaConfig.unmodified['characters']

  def detect(self, pos):
    "Detect a symbol"
    if pos.current() in FormulaSymbol.unmodified:
      return True
    if pos.current() in FormulaSymbol.modified:
      return True
    return False

  def parse(self, pos):
    "Parse the symbol"
    if pos.current() in FormulaSymbol.unmodified:
      self.addconstant(pos.current(), pos)
      return
    if pos.current() in FormulaSymbol.modified:
      symbol = FormulaSymbol.modified[pos.current()]
      self.addoriginal(pos.current(), pos)
      self.contents.append(FormulaConstant(symbol))
      return
    Trace.error('Symbol ' + pos.current() + ' not found')

class Number(FormulaBit):
  "A string of digits in a formula"

  def detect(self, pos):
    "Detect a digit"
    return pos.current().isdigit()

  def parse(self, pos):
    "Parse a bunch of digits"
    digits = self.glob(pos, lambda(p): p.current().isdigit())
    self.addconstant(digits, pos)
    self.type = 'number'

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  def __init__(self):
    FormulaBit.__init__(self)
    self.factory = FormulaFactory()
    self.arraymode = False

  def detect(self, pos):
    "Check in the factory"
    return self.factory.detectbit(pos)

  def parse(self, pos):
    "Parse with any formula bit"
    while self.factory.detectbit(pos):
      if self.parsearrayend(pos):
        return
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

  def setarraymode(self):
    "Set array mode for parsing"
    self.arraymode = True
    return self

  def parsearrayend(self, pos):
    "Parse the end of a formula in array mode"
    if not self.arraymode:
      return False
    if pos.checkfor(FormulaConfig.endings['Cell']):
      return True
    if pos.checkfor(FormulaConfig.endings['Row']):
      return True
    if pos.checkfor(FormulaConfig.endings['common']):
      return True
    return False

class Bracket(FormulaBit):
  "A {} bracket inside a formula"

  start = FormulaConfig.starts['bracket']
  ending = FormulaConfig.endings['bracket']

  def __init__(self):
    "Create a (possibly literal) new bracket"
    FormulaBit.__init__(self)
    self.inner = None

  def detect(self, pos):
    "Detect the start of a bracket"
    return pos.checkfor(self.start)

  def parse(self, pos):
    "Parse the bracket"
    self.parsecomplete(pos, self.innerformula)

  def parseliteral(self, pos):
    "Parse a literal bracket"
    self.parsecomplete(pos, self.innerliteral)
    return self

  def parsecomplete(self, pos, innerparser):
    if not pos.checkfor(self.start):
      Trace.error('Bracket should start with ' + self.start)
      return
    self.addoriginal(self.start, pos)
    innerparser(pos)
    if pos.isout() or pos.current() != self.ending:
      Trace.error('Missing ' + self.ending + ' in ' + pos.remaining())
      return
    self.addoriginal(self.ending, pos)

  def innerformula(self, pos):
    "Parse a whole formula inside the bracket"
    self.inner = WholeFormula()
    if self.inner.detect(pos):
      self.inner.parse(pos)
      self.add(self.inner)
      return
    if pos.isout():
      Trace.error('Unexpected end of bracket')
      return
    if pos.current() != self.ending:
      Trace.error('No formula in bracket at ' + pos.remaining())
    return

  def innerliteral(self, pos):
    "Parse a literal inside the bracket, which cannot generate html"
    literal = self.glob(pos, lambda(p): p.current() != self.ending)
    self.addoriginal(literal, pos)
    self.contents = literal

  def process(self):
    "Process the bracket"
    if self.inner:
      self.inner.process()

class SquareBracket(Bracket):
  "A [] bracket inside a formula"

  start = FormulaConfig.starts['squarebracket']
  ending = FormulaConfig.endings['squarebracket']

class FormulaFactory(object):
  "Construct bits of formula"

  # more bits may be appended later
  bits = [ FormulaSymbol(), RawText(), Number(), Bracket() ]
  unknownbits = []

  def detectbit(self, pos):
    "Detect if there is a next bit"
    if pos.isout():
      return False
    for bit in FormulaFactory.bits + FormulaFactory.unknownbits:
      if bit.detect(pos):
        return True
    return False

  def parsebit(self, pos):
    "Parse just one formula bit"
    for bit in FormulaFactory.bits + FormulaFactory.unknownbits:
      if bit.detect(pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.factory = self
        newbit.parse(pos)
        return newbit
    Trace.error('Unrecognized formula at ' + pos.remaining())
    constant = FormulaConstant(pos.current())
    pos.skip(pos.current())
    return constant

