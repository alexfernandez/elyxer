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
from conf.javatopyconf import *
from parse.position import *


class Declaration(object):
  "A grammar declaration consisting of several pieces."

  pieces = []

  def __init__(self, grammar):
    self.pieces = []
    self.grammar = grammar

  def parse(self, value):
    "Parse the given value."
    pos = TextPosition(value)
    while not pos.finished():
      if pos.current() == '$':
        self.parsevariable(pos)
      elif pos.current().isalnum() or pos.current() == '_':
        self.parseconstant(pos)
      elif pos.current() == ' ':
        self.parseblank(pos)
      else:
        self.parsesymbol(pos)

  def parsevariable(self, pos):
    "Parse a variable."
    pos.checkskip('$')
    name = '$' + pos.globvariable()
    if not name in self.grammar.declarations:
      Trace.error('Unknown variable ' + name)
      return
    self.pieces.append(self.grammar.declarations[name])

  def parseconstant(self, pos):
    "Parse a constant value."
    constant = pos.globvariable()
    if constant in self.grammar.constants:
      Trace.error('Repeated constant ' + constant)
      return
    Trace.debug('New constant: ' + constant)
    self.pieces.append(constant)

  def parseblank(self, pos):
    "Parse a blank character."
    self.pieces.append(pos.currentskip())

  def parsesymbol(self, pos):
    "Parse a symbol."
    self.pieces.append(pos.currentskip())

class Grammar(object):
  "Read a complete grammar into memory."

  def __init__(self):
    "Read all declarations into variables."
    self.variables = dict()
    self.declarations = dict()
    self.constants = dict()
    for key in JavaToPyConfig.declarations:
      self.parse(key, JavaToPyConfig.declarations[key])
    self.process()

  def parse(self, key, value):
    "Parse a single key-value pair."
    if isinstance(value, list):
      value = ','.join(value)
    Trace.debug('Read ' + key + ': ' + value)
    self.variables[key] = value

  def process(self):
    "Process the grammar and create all necessary structures."
    for key in self.variables:
      self.declarations[key] = Declaration(self)
    for key in self.variables:
      self.declarations[key].parse(self.variables[key])


