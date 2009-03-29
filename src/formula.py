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
    text = self.contents[0]
    whole = WholeFormula()
    pos = 0
    if not whole.detect(text, pos):
      return
    self.contents = [whole]
    whole.parse(text, pos)
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

  def __init__(self, text, pos):
    self.text = text
    self.pos = pos

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    self.alpha = False
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def glob(self, text, pos, check):
    "Glob a bit of text that satisfies a check"
    glob = ''
    while not self.out(text, pos) and check((text, pos)):
      glob += text[pos]
      pos += 1
    return glob

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

  def out(self, text, pos):
    "Check if we have got outside the formula"
    return pos >= len(text)

  def addconstant(self, string):
    "add a constant string"
    self.add(FormulaConstant(string))

  def add(self, bit):
    "Add any kind of formula bit"
    self.original += bit.original
    self.contents.append(bit)

  def checkfor(self, string, text, pos):
    "Check for a string at the given pos"
    if pos + len(string) > len(text):
      return False
    return text[pos : pos + len(string)] == string

  def __str__(self):
    "Get a string representation"
    return self.__class__.__name__ + ' in formula ' + self.original

  def parsebracket(self, text, pos):
    "Parse a bracket at the current position"
    bracket = Bracket()
    if not bracket.detect(text, pos):
      Trace.error('Expected {} at: ' + text[pos:])
      return
    bracket.parse(text, pos)
    self.add(bracket)
    return bracket

  def findcommand(self, text, pos):
    "Find a command with \\alpha"
    if text[pos] != '\\':
      return None
    pos += 1
    if self.out(text, pos):
      return None
    if not text[pos].isalpha():
      return None
    command = self.glob(text, pos, lambda(t, p): t[p].isalpha())
    return '\\' + command

  def findsymbolcommand(self, text, pos):
    "Find a command made with optional \\alpha and one symbol"
    backslash = ''
    if text[pos] == '\\' and pos + 1 < len(text):
      backslash = '\\'
      pos += 1
    alpha = self.glob(text, pos, lambda(t, p): t[p].isalpha())
    pos += len(alpha)
    if pos == len(text):
      return None
    symbol = backslash + alpha + text[pos]
    return symbol

class FormulaConstant(FormulaBit):
  "A constant string in a formula"

  def __init__(self, string):
    "Set the constant string"
    self.original = string
    self.output = FixedOutput()
    self.html = [string]

class RawText(FormulaBit):
  "A bit of text inside a formula"

  def detect(self, text, pos):
    "Detect a bit of raw text"
    return text[pos].isalpha()

  def parse(self, text, pos):
    "Parse alphabetic text"
    self.addconstant(self.glob(text, pos, lambda(t, p): t[p].isalpha()))
    self.alpha = True

  def process(self):
    self.contents = [Constant(self.original)]

class FormulaSymbol(FormulaBit):
  "A symbol inside a formula"

  def detect(self, text, pos):
    "Detect a symbol"
    symbol = text[pos]
    return symbol in FormulaConfig.unmodified + FormulaConfig.modified.keys()

  def parse(self, text, pos):
    "Parse the symbol"
    self.addconstant(text[pos])

class Number(FormulaBit):
  "A string of digits in a formula"

  def detect(self, text, pos):
    "Detect a digit"
    return text[pos].isdigit()

  def parse(self, text, pos):
    "Parse a bunch of digits"
    self.addconstant(self.glob(text, pos, lambda(t, p): t[p].isdigit()))

  def process(self):
    self.contents = [Constant(self.original)]

class Bracket(FormulaBit):
  "A {} bracket inside a formula"

  def detect(self, text, pos):
    "Detect the start of a bracket"
    return self.checkfor('{', text, pos)

  def parse(self, text, pos):
    "Parse the bracket"
    self.original += '{'
    pos += 1
    self.inside = WholeFormula()
    if not self.inside.detect(text, pos):
      Trace.error('Dangling {')
      return
    self.inside.parse(text, pos)
    self.add(self.inside)
    pos += len(self.inside.original)
    if self.out(text, pos) or text[pos] != '}':
      Trace.error('Missing }')
      return
    self.original += '}'

  def process(self):
    "Process the bracket"
    self.inside.process()

class FormulaArray(FormulaBit):
  "An array within a formula"

  ending = '\\end'
  bracket = '{array}'

  def detect(self, text, pos):
    "Detect an array"
    bracket = Bracket()
    if not bracket.detect(text, pos):
      return False
    bracket.parse(text, pos)
    if bracket.original != FormulaArray.bracket:
      return False
    return True

  def parse(self, text, pos):
    "Parse the array (after the command has been entered)"
    bracket1 = self.parsebracket(text, pos)
    if not bracket1 or bracket1.original != '{array}':
      Trace.error('{array} has disappeared! at ' + text[pos:])
      return False
    pos += len(bracket1.original)
    pos += self.parsealignments(text, pos)
    while not self.out(text, pos):
      row = FormulaRow(self.alignments)
      row.parse(text, pos)
      Trace.debug('Row parsed: ' + row.original)
      self.add(row)
      pos += len(row.original)
      if self.detectarrayend(text, pos):
        pos += self.parsearrayend(text, pos)
        Trace.debug('Array parsed: ' + self.original)
        return
      pos += self.parserowend(text, pos)

  def parsealignments(self, text, pos):
    "Parse the different alignments"
    bracket = self.parsebracket(text, pos)
    if not bracket:
      Trace.error('No alignments for array in ' + text[pos:])
      return 0
    Trace.debug('Alignments: ' + bracket.original[1:-1])
    self.alignments = []
    for l in bracket.original[1:-1]:
      self.alignments.append(l)
    return len(bracket.original)

  def detectarrayend(self, text, pos):
    "Parse the end of the array"
    command = self.findcommand(text, pos)
    if command and command == FormulaArray.ending:
      return True
    return False

  def parsearrayend(self, text, pos):
    "Parse the end of the array"
    if not self.checkfor(FormulaArray.ending, text, pos):
      Trace.error('End of array disappeared! from ' + text[pos:])
      return 0
    self.original += FormulaArray.ending
    parsed = len(FormulaArray.ending)
    if not self.checkfor(FormulaArray.bracket, text, pos + parsed):
      Trace.error('End but not of array! in ' + text[pos+parsed:])
      return parsed
    self.original += FormulaArray.bracket
    parsed += len(FormulaArray.bracket)
    return parsed

  def parserowend(self, text, pos):
    "Parse the end of a row"
    if not self.checkfor('\\\\', text, pos):
      Trace.error('No row end at ' + text[pos:])
      return 0
    return 2

class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  keys = FormulaConfig.commands.keys() + FormulaConfig.alphacommands.keys() + \
      FormulaConfig.onefunctions.keys() + FormulaConfig.decoratingfunctions.keys() + \
      FormulaConfig.twofunctions.keys() + ['\\begin']

  array = FormulaArray()

  def detect(self, text, pos):
    "Detect a command"
    if text[pos] == '\\':
      return True
    if text[pos] in FormulaCommand.keys:
      return True
    return False

  def parse(self, text, pos):
    "Parse the command"
    command = self.findcommand(text, pos)
    if command and command in FormulaCommand.keys:
      self.parsecommand(command, text, pos)
      return
    command = self.findsymbolcommand(text, pos)
    if command and command in FormulaCommand.keys:
      self.parsecommand(command, text, pos)
      return
    Trace.error('Invalid command in ' + text[pos:])
    self.addconstant('\\')

  def parsecommand(self, command, text, pos):
    "Parse a command with or without parameters"
    self.original += command
    pos += len(command)
    if self.parsenonecommand(command, text, pos):
      return
    if self.parseonefunction(command, text, pos):
      return
    if self.parsedecorating(command, text, pos):
      return
    if self.parsetwofunction(command, text, pos):
      return
    if self.parsearray(command, text, pos):
      return
    Trace.error('Internal error: command ' + command + ' not found')

  def parsenonecommand(self, command, text, pos):
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

  def parseonefunction(self, command, text, pos):
    "Parse a function with one parameter"
    if not command in FormulaConfig.onefunctions:
      return False
    self.output = TagOutput().settag(FormulaConfig.onefunctions[command])
    self.parsebracket(text, pos)
    return True

  def parsedecorating(self, command, text, pos):
    "Parse a decorating function"
    if not command in FormulaConfig.decoratingfunctions:
      return False
    self.output = TagOutput().settag('span class="withsymbol"')
    self.alpha = True
    tagged = TaggedText().constant(FormulaConfig.decoratingfunctions[command],
        'span class="symbolover"')
    self.contents.append(tagged)
    bracket = self.parsebracket(text, pos)
    if not bracket:
      Trace.error('Bracket missing at ' + text[pos:])
      return False
    bracket.output = TagOutput()
    bracket.tag = 'span class="undersymbol"'
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = FormulaConfig.alphacommands[self.original]
    return True

  def parsetwofunction(self, command, text, pos):
    "Parse a function of two parameters"
    if not command in FormulaConfig.twofunctions:
      return False
    tags = FormulaConfig.twofunctions[command]
    self.output = TagOutput().settag(tags[0])
    bracket1 = self.parsebracket(text, pos)
    if not bracket1:
      Trace.error('Bracket missing at ' + text[pos:])
      return False
    bracket1.output = TagOutput().settag(tags[1])
    pos += len(bracket1.original)
    bracket2 = self.parsebracket(text, pos)
    if not bracket2:
      Trace.error('Bracket missing at ' + text[pos:])
      return False
    bracket2.output = TagOutput().settag(tags[2])
    return True

  def parsearray(self, command, text, pos):
    "Parse an array"
    if command != '\\begin':
      return False
    array = FormulaArray()
    if not array.detect(text, pos):
      return False
    array.parse(text, pos)
    self.add(array)
    return True

class FormulaRow(FormulaCommand):
  "An array row inside an array"

  def __init__(self, alignments):
    FormulaCommand.__init__(self)
    self.alignments = alignments

  def parse(self, text, pos):
    for i in self.alignments:
      formula = WholeFormula().setarraymode()
      if not formula.detect(text, pos):
        Trace.error('Unexpected end of array at ' + text[pos:])
        return
      formula.parse(text, pos)
      self.add(formula)
      pos += len(formula.original)
      if self.checkfor('&', text, pos):
        self.original += '&'
        pos += 1

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  formulabit = [ FormulaSymbol(), RawText(), Number(), FormulaCommand(), Bracket() ]

  def __init__(self):
    FormulaBit.__init__(self)
    self.arraymode = False

  def detect(self, text, pos):
    "Check if inside bounds"
    return not self.out(text, pos)

  def parse(self, text, pos):
    "Parse with any formula bit"
    while not self.out(text, pos) and not self.checkfor('}', text, pos):
      if self.parsearrayend(text, pos):
        return
      bit = self.parsebit(text, pos)
      #Trace.debug(bit.original + ' -> ' + str(bit.gethtml()))
      self.add(bit)
      pos += len(bit.original)

  def parsebit(self, text, pos):
    "Parse a formula bit"
    for bit in WholeFormula.formulabit:
      if bit.detect(text, pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.parse(text, pos)
        return newbit
    Trace.error('Unrecognized formula at ' + text[pos:])
    return FormulaConstant(text[pos])

  def process(self):
    "Process the whole formula"
    for bit in self.contents:
      bit.process()

  def setarraymode(self):
    "Set array mode for parsing"
    self.arraymode = True
    return self

  def parsearrayend(self, text, pos):
    "Parse the end of a formula in array mode"
    if not self.arraymode:
      return False
    if self.checkfor('&', text, pos):
      return True
    if self.checkfor('\\\\', text, pos):
      return True
    if self.checkfor('\\end', text, pos):
      return True
    return False

ContainerFactory.types.append(Formula)

