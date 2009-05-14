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
# Alex 20090330
# eLyXer commands in formula processing

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from math.formula import *


class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"
 
  def parseparameter(self, pos):
    "Parse a parameter at the current position"
    if not self.factory.detectbit(pos):
      Trace.error('No parameter found at: ' + pos.remaining())
      return
    parameter = self.factory.parsebit(pos)
    self.add(parameter)
    return parameter

  def findcommand(self, pos, map):
    "Find any type of command in a map"
    command = self.findalphacommand(pos)
    if command and command in map:
      self.command = command
      return command
    command = self.findsymbolcommand(pos)
    if command and command in map:
      self.command = command
      return command
    return None

  def findalphacommand(self, oldpos):
    "Find a command with \\alpha"
    commandstart = FormulaConfig.starts['FormulaCommand']
    pos = oldpos.clone()
    if pos.current() != commandstart:
      return None
    pos.skip(commandstart)
    if pos.isout():
      return None
    if not pos.current().isalpha():
      return None
    command = self.glob(pos, lambda(p): p.current().isalpha())
    return commandstart + command

  def findsymbolcommand(self, oldpos):
    "Find a command made with optional \\alpha and one symbol"
    commandstart = FormulaConfig.starts['FormulaCommand']
    pos = oldpos.clone()
    backslash = ''
    if pos.current() == commandstart:
      backslash = commandstart
      pos.skip(commandstart)
    alpha = self.glob(pos, lambda(p): p.current().isalpha())
    pos.skip(alpha)
    if pos.isout():
      return None
    return backslash + alpha + pos.current()

  def process(self):
    "Process the internals"
    for bit in self.contents:
      bit.process()

class EmptyCommand(FormulaCommand):
  "An empty command (without parameters)"

  def detect(self, pos):
    "Detect the start of an empty command"
    if self.findcommand(pos, FormulaConfig.commands):
      return True
    if self.findcommand(pos, FormulaConfig.alphacommands):
      return True
    return False

  def parse(self, pos):
    "Parse a command without parameters"
    command = self.findcommand(pos, FormulaConfig.commands)
    if command:
      self.addtranslated(command, FormulaConfig.commands, pos)
      return
    command = self.findcommand(pos, FormulaConfig.alphacommands)
    if command:
      self.addtranslated(command, FormulaConfig.alphacommands, pos)
      self.type = 'alpha'
      return
    Trace.error('No command found in ' + pos.remaining())
    return

  def addtranslated(self, command, map, pos):
    "Add a command and find its translation"
    translated = map[command]
    self.addoriginal(command, pos)
    self.contents = [FormulaConstant(translated)]

class OneParamFunction(FormulaCommand):
  "A function of one parameter"

  functions = FormulaConfig.onefunctions

  def detect(self, pos):
    "Detect the start of the function"
    if self.findcommand(pos, self.functions):
      return True
    return False

  def parse(self, pos):
    "Parse a function with one parameter"
    command = self.findcommand(pos, self.functions)
    self.addoriginal(command, pos)
    self.output = TaggedOutput().settag(self.functions[command])
    self.parseparameter(pos)

class LiteralFunction(FormulaCommand):
  "A function with one parameter which is not parsed"

  functions = FormulaConfig.literalfunctions

  def detect(self, pos):
    "Detect the start of the function"
    if self.findcommand(pos, self.functions):
      return True
    return False

  def parse(self, pos):
    "Parse a function with one parameter"
    command = self.findcommand(pos, self.functions)
    self.addoriginal(command, pos)
    self.output = TaggedOutput().settag(self.functions[command])
    self.parseparameter(pos, True)

class FontFunction(OneParamFunction):
  "A function of one parameter that changes the font"

  functions = FormulaConfig.fontfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  functions = FormulaConfig.decoratingfunctions

  def parse(self, pos):
    "Parse a decorating function"
    command = self.findcommand(pos, FormulaConfig.decoratingfunctions)
    self.addoriginal(command, pos)
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.type = 'alpha'
    symbol = FormulaConfig.decoratingfunctions[command]
    tagged = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.contents.append(tagged)
    parameter = self.parseparameter(pos)
    parameter.output = TaggedOutput().settag('span class="undersymbol"')
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = [FormulaConfig.alphacommands[self.original]]

class FractionFunction(FormulaCommand):
  "A fraction with two parameters"

  def detect(self, pos):
    "Detect the start of the function"
    if self.findcommand(pos, FormulaConfig.fractionfunctions):
      return True
    return False

  def parse(self, pos):
    "Parse a function of two parameters"
    command = self.findcommand(pos, FormulaConfig.fractionfunctions)
    self.addoriginal(command, pos)
    whole = FormulaConfig.fractionspans['whole']
    first = FormulaConfig.fractionspans['first']
    second = FormulaConfig.fractionspans['second']
    self.output = TaggedOutput().settag(whole)
    parameter1 = self.parseparameter(pos)
    if not parameter1:
      return
    parameter1.output = TaggedOutput().settag(first)
    parameter2 = self.parseparameter(pos)
    if not parameter2:
      return
    parameter2.output = TaggedOutput().settag(second)

FormulaFactory.bits += [
    EmptyCommand(), OneParamFunction(), DecoratingFunction(),
    FractionFunction(), FontFunction(), LiteralFunction(),
    ]

