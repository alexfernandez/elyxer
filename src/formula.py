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

  def __str__(self):
    "Get a string representation"
    return self.__class__.__name__ + ' in formula ' + self.original

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

class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  keys = FormulaConfig.commands.keys() + FormulaConfig.alphacommands.keys() + \
      FormulaConfig.onefunctions.keys() + FormulaConfig.decoratingfunctions.keys() + \
      FormulaConfig.twofunctions.keys()

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

  def parsecommand(self, command, text, pos):
    "Parse a command with or without parameters"
    Trace.debug('Parsing command ' + command + ' at ' + text[pos:])
    self.original += command
    pos += len(command)
    if command in FormulaConfig.commands:
      self.addtranslated(command, FormulaConfig.commands)
      return
    if command in FormulaConfig.alphacommands:
      self.addtranslated(command, FormulaConfig.alphacommands)
      self.alpha = True
      return
    if command in FormulaConfig.onefunctions:
      self.output = TagOutput().settag(FormulaConfig.onefunctions[command])
      self.parsebracket(text, pos)
      return
    if command in FormulaConfig.decoratingfunctions:
      self.parsedecorating(command, text, pos)
      return
    if command in FormulaConfig.twofunctions:
      self.parsetwofunction(command, text, pos)
      return
    Trace.error('Internal error: command ' + command + ' not found')

  def addtranslated(self, command, map):
    "Add a command and find its translation"
    translated = map[command]
    self.contents.append(FormulaConstant(translated))

  def parsedecorating(self, command, text, pos):
    "Parse a decorating function"
    self.output = TagOutput().settag('span class="withsymbol"')
    tagged = TaggedText().constant(FormulaConfig.decoratingfunctions[command],
        'span class="symbolover"')
    self.contents.append(tagged)
    bracket = self.parsebracket(text, pos)
    bracket.output = TagOutput()
    bracket.tag = 'span class="undersymbol"'

  def parsebracket(self, text, pos):
    "Parse a bracket at the current position"
    bracket = Bracket()
    if not bracket.detect(text, pos):
      Trace.error('Expected {} at: ' + text[pos:])
      return
    bracket.parse(text, pos)
    self.add(bracket)
    return bracket

  def parsetwofunction(self, command, text, pos):
    "Parse a function of two parameters"
    tags = FormulaConfig.twofunctions[command]
    self.output = TagOutput().settag(tags[0])
    bracket1 = self.parsebracket(text, pos)
    bracket1.output = TagOutput().settag(tags[1])
    bracket2 = self.parsebracket(text, pos)
    bracket2.output = TagOutput().settag(tags[2])

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
    return text[pos] == '{'

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

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  formulabit = [ FormulaSymbol(), RawText(), Number(), FormulaCommand(), Bracket() ]

  def detect(self, text, pos):
    "Check if inside bounds"
    return not self.out(text, pos)

  def parse(self, text, pos):
    "Parse with any formula bit"
    while not self.out(text, pos) and text[pos] != '}':
      bit = self.parsebit(text, pos)
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

ContainerFactory.types.append(Formula)

