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
from config import *


class Formula(Container):
  "A LaTeX formula"

  start = '\\begin_inset Formula'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TaggedOutput().settag('span class="formula"')

  def process(self):
    "Convert the formula to tags"
    pos = Position(self.contents[0])
    whole = WholeFormula()
    if not whole.detect(pos):
      return
    self.contents = [whole]
    whole.parse(pos)
    whole.process()
    if self.header[0] != 'inline':
      self.output.settag('div class="formula"', True)

class FormulaParser(Parser):
  "Parses a formula"

  def parseheader(self, reader):
    "See if the formula is inlined"
    self.begin = reader.linenumber + 1
    if reader.currentline().find('$') > 0:
      return ['inline']
    else:
      return ['block']
  
  def parse(self, reader):
    "Parse the formula"
    if '$' in reader.currentline():
      rest = reader.currentline().split('$', 1)[1]
      if '$' in rest:
        # formula is $...$
        formula = reader.currentline().split('$')[1]
        reader.nextline()
      else:
        # formula is multiline $...$
        formula = self.parsemultiliner(reader, '$', '$')
    elif '\\[' in reader.currentline():
      # formula of the form \[...\]
      formula = self.parsemultiliner(reader, '\\[', '\\]')
    elif '\\begin{' in reader.currentline() and reader.currentline().endswith('}\n'):
      current = reader.currentline().strip()
      endsplit = current.split('\\begin{')[1].split('}')
      startpiece = '\\begin{' + endsplit[0] + '}'
      endpiece = '\\end{' + endsplit[0] + '}'
      formula = self.parsemultiliner(reader, startpiece, endpiece)
    else:
      Trace.error('Formula beginning ' + reader.currentline().strip +
          ' is unknown')
    while not reader.currentline().startswith(self.ending):
      stripped = reader.currentline().strip()
      if len(stripped) > 0:
        Trace.error('Unparsed formula line ' + stripped)
      reader.nextline()
    reader.nextline()
    return [formula]

  def parsemultiliner(self, reader, start, ending):
    "Parse a formula in multiple lines"
    formula = ''
    if not start in reader.currentline():
      Trace.error('Line ' + reader.currentline().strip() +
          ' does not contain formula start ' + start)
      return ''
    index = reader.currentline().index(start)
    formula = reader.currentline()[index + len(start):].strip()
    reader.nextline()
    while not reader.currentline().endswith(ending + '\n'):
      formula += reader.currentline()
      reader.nextline()
    formula += reader.currentline()[:-len(ending) - 1]
    reader.nextline()
    return formula

class Position(object):
  "A position in a formula to parse"

  def __init__(self, text):
    self.text = text
    self.pos = 0

  def skip(self, string):
    "Skip a string"
    self.pos += len(string)

  def remaining(self):
    "Return the text remaining for parsing"
    return self.text[self.pos:]

  def isout(self):
    "Find out if we are out of the formula yet"
    return self.pos >= len(self.text)

  def current(self):
    "Return the current character"
    return self.text[self.pos]

  def checkfor(self, string):
    "Check for a string at the given position"
    if self.pos + len(string) > len(self.text):
      return False
    return self.text[self.pos : self.pos + len(string)] == string

  def clone(self):
    "Return a copy of self"
    clone = Position(self.text)
    clone.pos = self.pos
    return clone

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

  def __str__(self):
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

  def detect(self, pos):
    "Detect a symbol"
    if pos.current() in FormulaConfig.unmodified:
      return True
    if pos.current() in FormulaConfig.modified:
      return True
    return False

  def parse(self, pos):
    "Parse the symbol"
    if pos.current() in FormulaConfig.unmodified:
      self.addconstant(pos.current(), pos)
      return
    if pos.current() in FormulaConfig.modified:
      symbol = FormulaConfig.modified[pos.current()]
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

  # more bits may be appended later
  bits = [ FormulaSymbol(), RawText(), Number() ]

  def __init__(self):
    FormulaBit.__init__(self)
    self.arraymode = False

  def detect(self, pos):
    "Check if inside bounds"
    return not pos.isout()

  def parse(self, pos):
    "Parse with any formula bit"
    while not pos.isout() and not pos.checkfor('}'):
      if self.parsearrayend(pos):
        return
      bit = self.parsebit(pos)
      #Trace.debug(bit.original + ' -> ' + str(bit.gethtml()))
      self.add(bit)

  def parsebit(self, pos):
    "Parse a formula bit"
    for bit in WholeFormula.bits:
      if bit.detect(pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.parse(pos)
        return newbit
    Trace.error('Unrecognized formula at ' + pos.remaining())
    constant = FormulaConstant(pos.current())
    pos.skip(pos.current())
    return constant

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
    if pos.checkfor('&'):
      return True
    if pos.checkfor('\\\\'):
      return True
    if pos.checkfor('\\end'):
      return True
    return False

ContainerFactory.types.append(Formula)

