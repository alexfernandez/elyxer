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
# Alex 20100311
# Read a generic grammar.

from util.trace import Trace
from util.clone import *
from conf.javatopyconf import *
from parse.position import *


class Piece(object):
  "Represents a piece (word, bracket... of any type) in a grammar."

  def match(self, tok):
    "Match the piece against the current token and return the match."
    Trace.error('Unmatchable piece ' + unicode(self) + ' in ' + unicode(tok))
    return None

class ConstantWord(Piece):
  "Represents a constant word in a grammar."

  def __init__(self, constant):
    "Initialize the word with the constant."
    self.constant = constant

  def match(self, tok):
    "Just match the current token against the constant."
    if tok.current() == self.constant:
      return self
    return None

  def __unicode__(self):
    "Printable representation."
    return '\'' + self.constant + '\''

class IdentifierWord(Piece):
  "A word made of alphanumeric and _ characters."

  def __init__(self):
    "Just create an empty word."
    self.word = None

  def set(self, word):
    self.word = word
    return self

  def match(self, tok):
    "Match the current token and store in the template."
    if tok.iscurrentidentifier():
      return IdentifierWord().set(tok.current())
    return None

class Bracket(Piece):
  "A bracket consisting of other words (repeated, conditional)."

  quantified = dict()

  def __init__(self):
    "Create an empty bracket."
    self.declaration = None
    self.quantifier = None

  def create(self, declaration, quantifier):
    "Create the bracket for a given declaration."
    self.declaration = declaration
    self.quantifier = quantifier
    return self

  def parse(self, pos):
    "Parse the bracket."
    pos.pushending(']')
    declaration = Declaration('bracket').parse(pos)
    pos.popending(']')
    quantifier = pos.currentskip()
    if not quantifier in self.quantified:
      Trace.error('Unknown quantifier ' + quantifier)
      return self
    bracket = Cloner.clone(self.quantified[quantifier]).create(declaration, quantifier)
    Trace.debug('Bracket: ' + unicode(bracket))
    return bracket
  
  def __unicode__(self):
    "Printable representation."
    return '[' + unicode(self.declaration) + ']' + self.quantifier

class MultipleBracket(Bracket):
  "A bracket present zero or more times (quantifier *)."

class RepeatedBracket(Bracket):
  "A bracket present one or more times (quantifier +)."

class ConditionalBracket(Bracket):
  "A bracket which may or may not be present (quantifier ?)."

Bracket.quantified = {
  '*': MultipleBracket(), '+': RepeatedBracket(), '?': ConditionalBracket()
}

class Alternatives(Piece):
  "A group of alternatives to parse."

  def __init__(self):
    "Create an empty set of alternatives."
    self.alternatives = []

  def add(self, pieces):
    "Add a new set of alternative pieces."
    alternative = Declaration('#' + unicode(len(self.alternatives)))
    alternative.pieces = pieces
    self.alternatives.append(alternative)
    Trace.debug('Alternatives: ' + unicode(self))
    return self

  def __unicode__(self):
    "Printable representation."
    if len(self.alternatives) == 0:
      return 'Empty alternatives'
    result = ''
    for alternative in self.alternatives:
      result += ' | ' + unicode(alternative)
    return result[3:]

class Declaration(Piece):
  "A grammar declaration consisting of several pieces."

  notsymbol = '[]_ |$'
  pieces = []

  def __init__(self, key):
    self.key = key
    self.pieces = []

  def parse(self, pos):
    "Parse the given position."
    while not pos.finished():
      if pos.checkskip('$'):
        self.parsevariable(pos)
      elif pos.checkskip('['):
        self.parsebracket(pos)
      elif pos.checkidentifier():
        self.parseidentifier(pos)
      elif pos.checkskip(' '):
        # ignore blank characters
        pass
      elif pos.checkskip('|'):
        self.parsealternative(pos)
      else:
        self.parsesymbol(pos)
    self.checkalternatives()
    return self

  def parsevariable(self, pos):
    "Parse a variable."
    if pos.checkskip('$'):
      self.pieces.append(IdentifierWord())
      return
    name = '$' + pos.globidentifier()
    if not name in Grammar.instance.declarations:
      Trace.error('Unknown variable ' + name)
      return
    Trace.debug('New variable ' + name)
    self.pieces.append(Grammar.instance.declarations[name])

  def parsebracket(self, pos):
    "Parse a bracket and the quantifier (*+?)."
    self.pieces.append(Bracket().parse(pos))

  def parseidentifier(self, pos):
    "Parse a constant identifier value."
    self.addconstant(pos.globidentifier())

  def parsealternative(self, pos):
    "Parse an alternative in a  group."
    if len(self.pieces) == 0:
      Trace.error('Empty beginning alternative at ' + pos.identifier())
      return
    if self.checkalternatives():
      return
    alt = Alternatives().add(self.pieces)
    self.pieces = [alt]

  def checkalternatives(self):
    "Check if there is a set of alternatives active, and add everything there."
    if len(self.pieces) == 0 or not isinstance(self.pieces[0], Alternatives):
      return False
    if len(self.pieces) == 1:
      Trace.error('Empty alternative')
      return
    self.pieces[0].add(self.pieces[1:])
    self.pieces = [self.pieces[0]]
    return True

  def parsesymbol(self, pos):
    "Parse a symbol."
    symbol = ''
    while self.issymbol(pos):
      symbol += pos.currentskip()
    if symbol == '':
      symbol += pos.currentskip()
      Trace.error('Empty symbol; acquiring ' + symbol)
    self.addconstant(symbol)

  def issymbol(self, pos):
    "Find out if the current character belongs to a larger symbol."
    if pos.finished():
      return False
    if pos.current() in self.notsymbol:
      return False
    if pos.checkidentifier():
      return False
    return True

  def addconstant(self, constant):
    "Add a constant value."
    if constant in Grammar.instance.constants:
      Trace.error('Repeated constant ' + constant)
      return
    Trace.debug('New constant: ' + constant)
    self.pieces.append(ConstantWord(constant))

  def __unicode__(self):
    "Printable representation."
    if len(self.pieces) == 0:
      return 'empty'
    result = ''
    for piece in self.pieces:
      if isinstance(piece, Declaration):
        pieceresult = piece.key
      else:
        pieceresult = unicode(piece)
      result += ', ' + pieceresult
    return result[2:]

class Grammar(object):
  "Read a complete grammar into memory."

  instance = None

  def __init__(self):
    "Read all declarations into variables."
    self.variables = dict()
    self.declarations = dict()
    self.constants = dict()

  def process(self):
    "Process the grammar and create all necessary structures."
    for key in JavaToPyConfig.declarations:
      self.variables[key] = JavaToPyConfig.declarations[key]
    for key in self.variables:
      self.declarations[key] = Declaration(key)
    for key in self.variables:
      Trace.debug('Interpreting ' + self.variables[key])
      pos = TextPosition(self.variables[key])
      self.declarations[key].parse(pos)

  def parse(self, tok):
    "Parse a whole file using a tokenizer."
    filedecl = self.declarations['$file']
    result = filedecl.match(tok)
    if not result:
      Trace.error('Actual file does not match $file.')
      return

Grammar.instance = Grammar()

