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
# Alex 20090311
# LyX styles in containers

from trace import Trace
from parse import *
from output import *
from container import *


class QuoteContainer(Container):
  "A container for a pretty quote"

  start = '\\begin_inset Quotes'
  ending = '\\end_inset'
  outputs = {
      'eld':u'“', 'erd':u'”', 'els':u'‘', 'ers':u'’',
      'sld':u'”', 'srd':u'”',
      'gld':u'„', 'grd':u'“', 'gls':u'‚', 'grs':u'‘',
      'pld':u'„', 'prd':u'”', 'pls':u'‚', 'prs':u'’',
      'fld':u'«', 'frd':u'»', 'fls':u'‹', 'frs':u'›',
      'ald':u'»', 'ard':u'«', 'als':u'›', 'ars':u'‹'
      }

  def __init__(self):
    self.parser = BoundedParser()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.type = self.header[2]
    if not self.type in QuoteContainer.outputs:
      Trace.error('Quote type ' + self.type + ' not found')
      self.html = '"'
      return
    self.html = QuoteContainer.outputs[self.type]

class LyxLine(Container):
  "A Lyx line"

  start = '\\lyxline'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<hr class="line" />']

class EmphaticText(TaggedText):
  "Text with emphatic mode"

  start = '\\emph on'

  def process(self):
    self.output.tag = 'i'

class ShapedText(TaggedText):
  "Text shaped (italic, slanted)"

  start = '\\shape'

  tags = {'slanted':'i', 'italic':'i', 'smallcaps':'span class="versalitas"'}

  def process(self):
    self.type = self.header[1]
    if not self.type in ShapedText.tags:
      Trace.error('Unrecognized shape ' + self.header[1])
      self.output.tag = 'span'
      return
    self.output.tag = ShapedText.tags[self.type]

class VersalitasText(TaggedText):
  "Text in versalitas"

  start = '\\noun on'

  def process(self):
    self.output.tag = 'span class="versalitas"'

class ColorText(TaggedText):
  "Colored text"

  start = '\\color'

  def process(self):
    self.color = self.header[1]
    self.output.tag = 'span class="' + self.color + '"'

class SizeText(TaggedText):
  "Sized text"

  start = '\\size'

  def process(self):
    self.size = self.header[1]
    self.output.tag = 'span class="' + self.size + '"'

class BoldText(TaggedText):
  "Bold text"

  start = '\\series bold'

  def process(self):
    self.output.tag = 'b'

class TextFamily(TaggedText):
  "A bit of text from a different family"

  start = '\\family'
  typetags = { 'typewriter':'tt', 'sans':'span class="sans"' }

  def process(self):
    "Parse the type of family"
    self.type = self.header[1]
    self.output.tag = TextFamily.typetags[self.type]

class Hfill(TaggedText):
  "Horizontall fill"

  start = '\\hfill'

  def process(self):
    self.output.tag = 'span class="right"'

class BarredText(TaggedText):
  "Text with a bar somewhere"

  start = '\\bar'
  typetags = { 'under':'u' }

  def process(self):
    "Parse the type of bar"
    self.type = self.header[1]
    if not self.type in BarredText.typetags:
      Trace.error('Unknown bar type ' + self.type)
      self.output.tag = 'span'
      return
    self.output.tag = BarredText.typetags[self.type]

class FlexCode(Container):
  "A bit of inset code"

  start = '\\begin_inset Flex CharStyle:Code'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="code"', True)

class ListItem(Container):
  "An element in a list"

  starts = ['\\begin_layout Enumerate', '\\begin_layout Itemize']
  ending = '\\end_layout'

  def __init__(self):
    "Output should be empty until the postprocessor can group items"
    self.contents = list()
    self.parser = BoundedParser()
    self.output = EmptyOutput()

  typetags = {'Enumerate':'ol', 'Itemize':'ul'}

  def process(self):
    "Set the correct type and contents."
    self.type = self.header[1]
    tag = TaggedText().complete(self.contents, 'li', True)
    self.contents = [tag]

class DeeperList(Container):
  "A nested list"

  start = '\\begin_deeper'
  ending = '\\end_deeper'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput()
    self.type = None
    self.sublist = True

  def process(self):
    "Create the deeper list"
    if len(self.contents) == 0:
      Trace.error('Empty deeper list')
      return
    items = []
    for item in self.contents:
      if isinstance(item, ListItem):
        self.settypeandsublist(item.type, True)
        items.append(item.contents[0])
      elif isinstance(item, DeeperList):
        items.append(item)
      else:
        self.settypeandsublist(None, False)
    if not self.sublist:
      # do not mangle contents
      return
    self.contents = items
    self.output.settag(ListItem.typetags[self.type], True)

  def settypeandsublist(self, type, sublist):
    "Set the new type and whether a sublist"
    if self.type and not sublist:
      Trace.error('Layouts in nested list not allowed')
    if self.sublist and self.type and self.type != type:
      Trace.error('Mixed items in nested list not allowed')
    self.type = type
    self.sublist = sublist

ContainerFactory.types += [QuoteContainer, LyxLine, EmphaticText, ShapedText,
    VersalitasText, ColorText, SizeText, BoldText, TextFamily, Hfill,
    FlexCode, ListItem, DeeperList, BarredText]

