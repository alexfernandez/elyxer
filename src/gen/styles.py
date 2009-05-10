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

from util.trace import Trace
from parse.parser import *
from io.output import *
from gen.container import *


class QuoteContainer(Container):
  "A container for a pretty quote"

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

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<hr class="line" />']

class EmphaticText(TaggedText):
  "Text with emphatic mode"

  def process(self):
    self.output.tag = 'i'

class ShapedText(TaggedText):
  "Text shaped (italic, slanted)"

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

  def process(self):
    self.output.tag = 'span class="versalitas"'

class ColorText(TaggedText):
  "Colored text"

  def process(self):
    self.color = self.header[1]
    self.output.tag = 'span class="' + self.color + '"'

class SizeText(TaggedText):
  "Sized text"

  def process(self):
    self.size = self.header[1]
    self.output.tag = 'span class="' + self.size + '"'

class BoldText(TaggedText):
  "Bold text"

  def process(self):
    self.output.tag = 'b'

class TextFamily(TaggedText):
  "A bit of text from a different family"

  typetags = { 'typewriter':'tt', 'sans':'span class="sans"' }

  def process(self):
    "Parse the type of family"
    self.type = self.header[1]
    self.output.tag = TextFamily.typetags[self.type]
    Trace.debug('Family ' + self.type + ', text: ' + str(self.contents))

class Hfill(TaggedText):
  "Horizontall fill"

  def process(self):
    self.output.tag = 'span class="right"'

class BarredText(TaggedText):
  "Text with a bar somewhere"

  typetags = { 'under':'u' }

  def process(self):
    "Parse the type of bar"
    self.type = self.header[1]
    if not self.type in BarredText.typetags:
      Trace.error('Unknown bar type ' + self.type)
      self.output.tag = 'span'
      return
    self.output.tag = BarredText.typetags[self.type]

class LangLine(Container):
  "A line with language information"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

  def process(self):
    self.lang = self.header[1]

