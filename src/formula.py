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
    self.output = TagOutput()

  def process(self):
    "Convert the formula to tags"
    text = self.contents[0]
    original, result = self.convert(text, 0)
    #Trace.debug('Formula ' + original + ' -> ' + result)
    self.contents = result
    # self.restyle(TaggedText, self.restyletagged)
    if self.header[0] == 'inline':
      self.tag = 'span class="formula"'
      self.breaklines = False
    else:
      self.tag = 'div class="formula"'
      self.breaklines = True
  
  def convert(self, text, pos):
    "Convert a bit of text to HTML"
    processed = ''
    result = list()
    while pos < len(text) and text[pos] != '}':
      original, converted = self.convertchars(text, pos)
      processed += original
      pos += len(original)
      result += converted
    return processed, result

  def convertchars(self, text, pos):
    "Convert one or more characters, return the conversion"
    for reader in Formula.readers:
      bit, result = reader(self, text, pos)
      if bit:
        return bit, result
    if text[pos] == '{':
      bracket, result = self.readbracket(text, pos)
      return bracket, [Constant('{')] + result + [Constant('}')]
    Trace.error('Unrecognized function at ' + str(self.parser.begin) + ' in ' +
        unicode(text[pos:]))
    return text[pos], [Constant(text[pos])]

  def readvariable(self, text, pos):
    "Read a variable"
    alpha, result = self.extractalpha(text, pos)
    if not alpha or len(alpha) == 0:
      return None, None
    return alpha, [TaggedText().constant(alpha, 'i')]

  def extractalpha(self, text, pos):
    "Read alphabetic sequence"
    alpha = unicode()
    result = []
    while pos < len(text):
      bit, bitresult = self.extractalphabit(text, pos)
      if not bit or len(bit) == 0:
        return alpha, result
      alpha += bit
      result += bitresult
      pos += len(bit)
    return alpha, result

  def extractalphabit(self, text, pos):
    "Find out if there is an alphabetic sequence"
    if text[pos].isalpha():
      alpha = self.extractpurealpha(text, pos)
      return alpha, alpha
    if text[pos] == '\\':
      command, result = self.findcommand(text, pos, FormulaConfig.alphacommands)
      if command:
        return command, result
    return None, None

  def extractpurealpha(self, text, pos):
    "Extract a pure alphabetic sequence"
    alpha = unicode()
    while pos < len(text) and text[pos].isalpha():
      alpha += text[pos]
      pos += 1
    return alpha

  def extractcommand(self, text, pos):
    "Extract a whole command"
    if pos == len(text) or text[pos] != '\\':
      return None
    return '\\' + self.extractpurealpha(text, pos + 1)

  def readsymbols(self, text, pos):
    "Read a string of symbols"
    symbols = unicode()
    result = unicode()
    while pos + len(symbols) < len(text):
      char = text[pos + len(symbols)]
      if char.isdigit() or char in FormulaConfig.unmodified:
        symbols += char
        result += char
      elif char in FormulaConfig.modified:
        symbols += char
        result += FormulaConfig.modified[char]
      else:
        break
    if len(symbols) == 0:
      return None, None
    return symbols, [Constant(result)]

  def readcommand(self, text, pos):
    "read a command"
    command, translated = self.findcommand(text, pos, FormulaConfig.commands)
    if command:
      return command, [Constant(translated)]
    return None, None

  def extractsymbolcommand(self, text, pos):
    "Extract a command made with alpha and one symbol"
    backslash = ''
    if text[pos] == '\\' and pos + 1 < len(text):
      backslash = '\\'
      pos += 1
    alpha = self.extractpurealpha(text, pos)
    pos += len(alpha)
    if pos == len(text):
      return None
    symbol = backslash + alpha + text[pos]
    return symbol

  def readone(self, text, pos):
    "read a one-parameter function"
    function, value = self.findcommand(text, pos, FormulaConfig.onefunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket, result = self.readbracket(text, pos)
    if len(value) == 0:
      return function + bracket, []
    if value.startswith('*'):
      value = value.replace('*', '')
      Trace.debug('Combining ' + value + ' with ' + str(result))
      tagover = TaggedText().constant(value, 'span class="symbolover"')
      tagunder = TaggedText().complete(result, 'span class="undersymbol"')
      result = [tagover, tagunder]
      realresult = [TaggedText().complete(result, 'span class="withsymbol"')]
      return function + bracket, realresult
    return function + bracket, [TaggedText().complete(result, value)]

  def readtwo(self, text, pos):
    "read a two-parameter function"
    function, tags = self.findcommand(text, pos, FormulaConfig.twofunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket1, result1 = self.readbracket(text, pos)
    pos += len(bracket1)
    bracket2, result2 = self.readbracket(text, pos)
    original =  function + bracket1 + bracket2
    tagged1 = TaggedText().complete(result1, tags[1])
    tagged2 = TaggedText().complete(result2, tags[2])
    tagged0 = TaggedText().complete([tagged1, tagged2], tags[0])
    return original, [tagged0]

  def readbracket(self, text, pos):
    "Read a bracket as {result}"
    if text[pos] != u'{':
      Trace.error(u'Missing { in ' + text + '@' + str(pos))
      return '', [Constant('')]
    original, converted = self.convert(text, pos + 1)
    if text[pos + 1 + len(original)] != u'}':
      Trace.error(u'Missing } in ' + text + '@' + str(pos))
    return '{' + original + '}', converted

  def findcommand(self, text, pos, map):
    "Find a command (alphanumeric or with a symbol) in a map"
    command = self.extractcommand(text, pos)
    command, translated = self.locatecommand(command, map)
    if command:
      return command, translated
    command = self.extractsymbolcommand(text, pos)
    command, translated = self.locatecommand(command, map)
    if command:
      return command, translated
    return None, None

  def locatecommand(self, command, map):
    "Locate a command in a map"
    if not command or len(command) == 0:
      return None, None
    if not command in map:
      return None, None
    return command, map[command]

  readers = [ readvariable, readsymbols, readcommand, readone, readtwo ]

class OldFormula(Container):
  "The old LaTeX formula"
  
  def convert(self, text, pos):
    "Convert a bit of text to HTML"
    processed = ''
    result = list()
    while pos < len(text) and text[pos] != '}':
      original, converted = self.convertchars(text, pos)
      processed += original
      pos += len(original)
      result += converted
    return processed, result

  def convertchars(self, text, pos):
    "Convert one or more characters, return the conversion"
    for reader in Formula.readers:
      bit, result = reader(self, text, pos)
      if bit:
        return bit, result
    Trace.error('Unrecognized function at ' + str(self.parser.begin) + ' in ' +
        unicode(text[pos:]))
    return '\\', [Constant('\\')]

  def readsymbols(self, text, pos):
    "Read a string of symbols"
    symbols = unicode()
    result = unicode()
    while pos + len(symbols) < len(text):
      char = text[pos + len(symbols)]
      if char.isdigit() or char in FormulaConfig.unmodified:
        symbols += char
        result += char
      elif char in FormulaConfig.modified:
        symbols += char
        result += FormulaConfig.modified[char]
      else:
        break
    if len(symbols) == 0:
      return None, None
    return symbols, [Constant(result)]

  def restyletagged(self, container, index):
    "Restyle tagged text"
    tagged = container.contents[index]
    if tagged.tag == 'span class="mathsf"' or tagged.tag == 'span class="text"':
      tagged.restyle(TaggedText, self.removeitalics)
      first = tagged.contents[0]
      if self.mustspaceunits(container.contents, index):
        first.contents[0] = u' ' + first.contents[0]
    elif tagged.tag == 'span class="sqrt"':
      tagged.tag = 'span class="root"'
      radical = TaggedText().constant(u'√', 'span class="radical"')
      container.contents.insert(index, radical)
    elif tagged.tag == 'i':
      group = TaggedText().complete([], 'i')
      self.group(index, group, self.isalpha)
      group.restyle(TaggedText, self.removeitalics)

  def removeitalics(self, container, index):
    "Remove italics tag"
    if container.contents[index].tag == 'i':
      container.remove(index)

  def isalpha(self, element):
    "Check if the element is all text"
    if isinstance(element, StringContainer):
      return element.contents[0].isalpha()
    for item in element.contents:
      if not self.isalpha(item):
        return False
    return True

  def mustspaceunits(self, contents, index):
    "Check if units must be spaced"
    if index == 0:
      return False
    first = contents[index].contents[0]
    if not isinstance(first, Constant):
      return False
    last = contents[index - 1]
    if isinstance(last, Constant):
      string = last.contents[-1]
      if len(string) == 0:
        return False
      if string[-1].isdigit():
        return True
    return False

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

ContainerFactory.types.append(Formula)

