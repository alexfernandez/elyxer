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
# Alex 20091214
# eLyXer functions with a variable number of parameters.

import sys
from gen.container import *
from util.trace import Trace
from conf.config import *
from math.bits import *
from math.command import *


class HybridFunction(CommandBit):
  "Read a function with two parameters: [] and {}"
  "The [] parameter is optional"

  commandmap = FormulaConfig.hybridfunctions
  parambrackets = [('[', ']'), ('{', '}')]

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters"
    readtemplate = self.translated[0]
    writetemplate = self.translated[1]
    Trace.debug('Command ' + self.command + ': from ' + readtemplate + ' to ' + writetemplate)
    params = self.readparams(readtemplate, pos)
    self.contents = self.writeparams(params, writetemplate)

  def readparams(self, readtemplate, pos):
    "Read the params according to the template."
    params = dict()
    for paramdef in self.paramdefs(readtemplate):
      if paramdef.startswith('['):
        value = self.parsesquare(pos)
      elif paramdef.startswith('{'):
        value = self.parseparameter(pos)
      else:
        Trace.error('Invalid parameter definition ' + paramdef)
        value = None
      if value:
        Trace.debug('Value for ' + paramdef[1:-1] + ': ' + unicode(value) + ', type ' + unicode(value.type))
      params[paramdef[1:-1]] = value
    return params

  def paramdefs(self, readtemplate):
    "Read each param definition in the template"
    pos = Position(readtemplate)
    while not pos.finished():
      paramdef = self.readparamdef(pos)
      if paramdef:
        if len(paramdef) != 4:
          Trace.error('Parameter definition ' + paramdef + ' has wrong length')
        else:
          yield paramdef

  def readparamdef(self, pos):
    "Read a single parameter definition: [$0], {$x}..."
    Trace.debug('Reading parameter in ' + pos.remaining())
    for (opening, closing) in HybridFunction.parambrackets:
      if pos.checkskip(opening):
        if not pos.checkfor('$'):
          Trace.error('Wrong parameter name ' + pos.current())
          return None
        return opening + pos.globincluding(closing)
    Trace.error('Wrong character in parameter template' + pos.currentskip())
    return None

  def writeparams(self, params, writetemplate):
    "Write all params according to the template"
    Trace.debug('Template: ' + writetemplate)
    return self.writepos(params, Position(writetemplate))

  def writepos(self, params, pos):
    "Write all params as read in the parse position."
    result = []
    while not pos.finished():
      if pos.checkskip('$'):
        param = self.writeparam(params, pos)
        if param:
          result.append(param)
      elif pos.checkskip('f'):
        function = self.writefunction(params, pos)
        if function:
          result.append(function)
      else:
        result.append(FormulaConstant(pos.currentskip()))
    return result

  def writeparam(self, params, pos):
    "Write a single param of the form $0, $x..."
    name = '$' + pos.currentskip()
    if not name in params:
      Trace.error('Unknown parameter ' + name)
      return None
    if not params[name]:
      return None
    Trace.debug('Appending ' + unicode(params[name]))
    if pos.checkskip('.'):
      params[name].type = pos.globalpha()
      Trace.debug('Type of ' + unicode(params[name]) + ': ' + params[name].type)
    return params[name]

  def writefunction(self, params, pos):
    "Write a single function f0,...,fn."
    if not pos.current().isdigit():
      Trace.error('Function should be f0,...,f9: f' + pos.current())
      return None
    index = int(pos.currentskip())
    if 2 + index > len(self.translated):
      Trace.error('Function f' + unicode(index) + ' is not defined')
      return None
    tag = self.translated[2 + index]
    if not pos.checkskip('{'):
      Trace.error('Function should be defined in {}')
      return None
    pos.pushending('}')
    contents = self.writepos(params, pos)
    pos.popending()
    if len(contents) == 0:
      return None
    function = TaggedBit().complete(contents, tag)
    function.type = None
    Trace.debug('Function ' + unicode(function))
    return function

  def sqrt(self, root, radical):
    "A square root -- process the root"
    if root:
      root.output = TaggedOutput().settag('sup')
    radix = TaggedBit().constant(u'√', 'span class="radical"')
    underroot = TaggedBit().complete(radical.contents, 'span class="root"')
    radical.contents = [radix, underroot]

  def unit(self, value, units):
    "A unit -- mark the units as font"
    units.type = 'font'

class FractionFunction(CommandBit):
  "A fraction with two parameters"

  commandmap = FormulaConfig.fractionfunctions

  def parsebit(self, pos):
    "Parse a fraction function with two parameters (optional alignment)"
    self.output = TaggedOutput().settag(self.translated[0])
    firsttag = self.translated[1]
    secondtag = self.translated[2]
    template = self.translated[3]
    align = self.parsesquare(pos)
    if align and self.command == '\\cfrac':
      self.contents.pop()
      firsttag = firsttag[:-1] + '-' + align.contents[0].original + '"'
    parameter1 = self.parseparameter(pos)
    if not parameter1:
      Trace.error('Invalid fraction function ' + self.translated[0] + 
          ': missing first {}')
      return
    parameter1.output = TaggedOutput().settag(firsttag)
    parameter2 = self.parseparameter(pos)
    if not parameter2:
      Trace.error('Invalid fraction function ' + self.translated[0] + 
          ': missing second {}')
      return
    parameter2.output = TaggedOutput().settag(secondtag)
    if align and self.command == '\\unitfrac':
      parameter1.type = 'font'
      parameter2.type = 'font'
    parameters = [parameter1, parameter2]
    self.contents.pop()
    self.contents.pop()
    self.fillin(template, parameters)

  def fillin(self, template, values):
    "Fill in the contents according to a template and some values."
    "If the template is $1-$2 the contents will have: [first value, '-', second value]."
    pos = Position(template)
    while not pos.finished():
      self.contents.append(self.getpiece(pos, values))
      
  def getpiece(self, pos, values):
    "Get the next piece of the template."
    if not pos.checkskip('$'):
      return FormulaConstant(pos.globexcluding('$'))
    if pos.checkskip('$'):
      return FormulaConstant('$')
    if not pos.current().isdigit():
      Trace.error('Invalid template piece $' + pos.current())
      return FormulaConstant('$')
    index = int(pos.current()) - 1
    pos.skip(pos.current())
    return values[index]

class SpacingFunction(CommandBit):
  "A spacing function with two parameters"

  commandmap = FormulaConfig.spacingfunctions

  def parsebit(self, pos):
    "Parse a spacing function with two parameters"
    numparams = int(self.translated[1])
    parameter1 = Bracket().parseliteral(pos)
    if not parameter1:
      Trace.error('Missing first {} in function ' + self.command)
    parameter2 = None
    if numparams == 2:
      parameter2 = self.parseparameter(pos)
      if not parameter2:
        Trace.error('Missing second {} in spacing function ' + self.command)
        return
    else:
      self.add(FormulaConstant(' '))
    tag = self.translated[0].replace('$param', parameter1.literal)
    self.output = TaggedOutput().settag(tag)

FormulaCommand.commandbits += [
    HybridFunction(), FractionFunction(), SpacingFunction(),
    ]

