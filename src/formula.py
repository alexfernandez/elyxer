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
from container import *
from trace import Trace
from general import *


class Formula(Container):
  "A LaTeX formula"

  start = '\\begin_inset Formula'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TagOutput().settag('span class="formula"')

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
        formula = self.parsemultiliner(reader, '$')
    elif '\\[' in reader.currentline():
      # formula of the form \[...\]
      formula = self.parsemultiliner(reader, '\\]')
    elif '\\begin{' in reader.currentline() and reader.currentline().endswith('}\n'):
      current = reader.currentline().strip()
      endsplit = current.split('\\begin{')[1].split('}')
      endpiece = '\\end{' + endsplit[0] + '}'
      formula = self.parsemultiliner(reader, endpiece)
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

  def parsemultiliner(self, reader, ending):
    "Parse a formula in multiple lines"
    reader.nextline()
    formula = ''
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

  def skipbit(self, bit):
    "Skip a formula bit"
    self.pos += len(bit.original)

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

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    self.alpha = False
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def glob(self, pos, check):
    "Glob a bit of text that satisfies a check"
    glob = ''
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
    self.add(FormulaConstant(string), pos)

  def add(self, bit, pos):
    "Add any kind of formula bit"
    self.original += bit.original
    self.contents.append(bit)
    pos.skipbit(self)

  def addoriginal(self, string, pos):
    "Add a constant to the original formula only"
    self.original += string
    pos.skipbit(self)

  def __str__(self):
    "Get a string representation"
    return self.__class__.__name__ + ' in formula ' + self.original
 
  def parsebracket(self, pos):
    "Parse a bracket at the current position"
    bracket = Bracket()
    if not bracket.detect(pos):
      Trace.error('Expected {} at: ' + pos.remaining())
      return
    bracket.parse(pos)
    self.add(bracket)
    return bracket

  def findcommand(self, pos):
    "Find a command with \\alpha"
    if pos.current() != '\\':
      return None
    pos.skip('\\')
    if pos.isout():
      return None
    if not pos.current().isalpha():
      return None
    command = self.glob(pos, lambda(p): p.current().isalpha())
    return '\\' + command

  def findsymbolcommand(self, pos):
    "Find a command made with optional \\alpha and one symbol"
    backslash = ''
    if pos.current() == '\\':
      backslash = '\\'
      pos.skip('\\')
    alpha = self.glob(pos, lambda(p): p.current().isalpha())
    pos.skip(alpha)
    if pos.isout():
      return None
    return backslash + alpha + pos.current()

class FormulaConstant(FormulaBit):
  "A constant string in a formula"

  def __init__(self, string):
    "Set the constant string"
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
    self.alpha = True

  def process(self):
    self.contents = [Constant(self.original)]

class FormulaSymbol(FormulaBit):
  "A symbol inside a formula"

  keys = FormulaConfig.unmodified + FormulaConfig.modified.keys()

  def detect(self, pos):
    "Detect a symbol"
    return pos.current() in FormulaSymbol.keys

  def parse(self, pos):
    "Parse the symbol"
    self.addconstant(pos.current(), pos)

class Number(FormulaBit):
  "A string of digits in a formula"

  def detect(self, pos):
    "Detect a digit"
    return pos.current().isdigit()

  def parse(self, pos):
    "Parse a bunch of digits"
    digits = self.glob(pos, lambda(p): p.current().isdigit())
    self.addconstant(digits, pos)

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
    self.add(self.inside, pos)
    if pos.isout() or pos.current() != '}':
      Trace.error('Missing }')
      return
    self.addoriginal('}', pos)

  def process(self):
    "Process the bracket"
    self.inside.process()

class FormulaArray(FormulaBit):
  "An array within a formula"

  ending = '\\end'
  bracket = '{array}'

  def detect(self, pos):
    "Detect an array"
    bracket = Bracket()
    if not bracket.detect(pos):
      return False
    bracket.parse(pos)
    if bracket.original != FormulaArray.bracket:
      return False
    return True

  def parse(self, pos):
    "Parse the array (after the command has been entered)"
    bracket1 = self.parsebracket(pos)
    if not bracket1 or bracket1.original != '{array}':
      Trace.error('{array} has disappeared! at ' + pos.remaining())
      return
    if not self.parsealignments(pos):
      return
    while not pos.isout():
      row = FormulaRow(self.alignments)
      row.parse(pos)
      Trace.debug('Row parsed: ' + row.original)
      self.add(row)
      if self.detectarrayend(pos):
        self.parsearrayend(pos)
        Trace.debug('Array parsed: ' + self.original)
        return
      self.parserowend(pos)

  def parsealignments(self, pos):
    "Parse the different alignments"
    bracket = self.parsebracket(pos)
    if not bracket:
      Trace.error('No alignments for array in ' + pos.remaining())
      return
    Trace.debug('Alignments: ' + bracket.original[1:-1])
    self.alignments = []
    for l in bracket.original[1:-1]:
      self.alignments.append(l)
    return len(bracket.original)

  def detectarrayend(self, pos):
    "Parse the end of the array"
    command = self.findcommand(pos)
    if command and command == FormulaArray.ending:
      return True
    return False

  def parsearrayend(self, pos):
    "Parse the end of the array"
    if not pos.checkfor(FormulaArray.ending):
      Trace.error('End of array disappeared! from ' + pos.remaining())
      return
    self.addoriginal(FormulaArray.ending)
    if not pos.checkfor(FormulaArray.bracket):
      Trace.error('End but not of array! in ' + pos.remaining())
      return
    self.addoriginal(FormulaArray.bracket)

  def parserowend(self, pos):
    "Parse the end of a row"
    if not pos.checkfor('\\\\'):
      Trace.error('No row end at ' + pos.remaining())
      return 0
    return 2

class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  keys = FormulaConfig.commands.keys() + FormulaConfig.alphacommands.keys() + \
      FormulaConfig.onefunctions.keys() + FormulaConfig.decoratingfunctions.keys() + \
      FormulaConfig.twofunctions.keys() + ['\\begin']

  array = FormulaArray()

  def detect(self, pos):
    "Detect a command"
    if pos.current() == '\\':
      return True
    if pos.current() in FormulaCommand.keys:
      return True
    return False

  def parse(self, pos):
    "Parse the command"
    command = self.findcommand(pos)
    if command and command in FormulaCommand.keys:
      self.parsecommand(command, pos)
      return
    command = self.findsymbolcommand(pos)
    if command and command in FormulaCommand.keys:
      self.parsecommand(command, pos)
      return
    Trace.error('Invalid command in ' + pos.remaining())
    self.addconstant('\\', pos)

  def parsecommand(self, command, pos):
    "Parse a command with or without parameters"
    self.addoriginal(command, pos)
    if self.parsenonecommand(command, pos):
      return
    if self.parseonefunction(command, pos):
      return
    if self.parsedecorating(command, pos):
      return
    if self.parsetwofunction(command, pos):
      return
    if self.parsearray(command, pos):
      return
    Trace.error('Internal error: command ' + command + ' not found')

  def parsenonecommand(self, command, pos):
    "Parse a command without parameters"
    if command in FormulaConfig.commands:
      self.addtranslated(command, FormulaConfig.commands)
      return True
    if command in FormulaConfig.alphacommands:
      self.addtranslated(command, FormulaConfig.alphacommands)
      self.alpha = True
      return True
    return False

  def addtranslated(self, command, map):
    "Add a command and find its translation"
    translated = map[command]
    self.contents.append(FormulaConstant(translated))

  def parseonefunction(self, command, pos):
    "Parse a function with one parameter"
    if not command in FormulaConfig.onefunctions:
      return False
    self.output = TagOutput().settag(FormulaConfig.onefunctions[command])
    self.parsebracket(pos)
    return True

  def parsedecorating(self, command, pos):
    "Parse a decorating function"
    if not command in FormulaConfig.decoratingfunctions:
      return False
    self.output = TagOutput().settag('span class="withsymbol"')
    self.alpha = True
    tagged = TaggedText().constant(FormulaConfig.decoratingfunctions[command],
        'span class="symbolover"')
    self.contents.append(tagged)
    bracket = self.parsebracket(pos)
    if not bracket:
      Trace.error('Bracket missing at ' + pos.remaining())
      return False
    bracket.output = TagOutput()
    bracket.tag = 'span class="undersymbol"'
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = FormulaConfig.alphacommands[self.original]
    return True

  def parsetwofunction(self, command, pos):
    "Parse a function of two parameters"
    if not command in FormulaConfig.twofunctions:
      return False
    tags = FormulaConfig.twofunctions[command]
    self.output = TagOutput().settag(tags[0])
    bracket1 = self.parsebracket(pos)
    if not bracket1:
      Trace.error('Bracket missing at ' + pos.remaining())
      return False
    bracket1.output = TagOutput().settag(tags[1])
    bracket2 = self.parsebracket(pos)
    if not bracket2:
      Trace.error('Bracket missing at ' + pos.remaining())
      return False
    bracket2.output = TagOutput().settag(tags[2])
    return True

  def parsearray(self, command, pos):
    "Parse an array"
    if command != '\\begin':
      return False
    array = FormulaArray()
    if not array.detect(pos):
      return False
    array.parse(pos)
    self.add(array)
    return True

class FormulaRow(FormulaCommand):
  "An array row inside an array"

  def __init__(self, alignments):
    FormulaCommand.__init__(self)
    self.alignments = alignments

  def parse(self, pos):
    for i in self.alignments:
      formula = WholeFormula().setarraymode()
      if not formula.detect(pos):
        Trace.error('Unexpected end of array at ' + pos.remaining())
        return
      formula.parse(pos)
      self.add(formula)
      if self.checkfor('&', pos):
        self.addoriginal('&')

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  formulabit = [ FormulaSymbol(), RawText(), Number(), FormulaCommand(), Bracket() ]

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
      self.add(bit, pos)

  def parsebit(self, pos):
    "Parse a formula bit"
    for bit in WholeFormula.formulabit:
      if bit.detect(pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.parse(pos)
        return newbit
    Trace.error('Unrecognized formula at ' + pos.remaining())
    return FormulaConstant(pos.current())

  def process(self):
    "Process the whole formula"
    for bit in self.contents:
      bit.process()

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
