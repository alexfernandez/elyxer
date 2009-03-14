#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

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
  outputs = { 'eld':u'“', 'erd':u'”' }

  def __init__(self):
    self.parser = BoundedParser()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.type = self.header[2]
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
    self.tag = 'i'

class SlantedText(TaggedText):
  "Text slanted (not italic)"

  start = '\\shape slanted'

  def process(self):
    self.tag = 'i'

class VersalitasText(TaggedText):
  "Text in versalitas"

  start = '\\noun on'

  def process(self):
    self.tag = 'span class="versalitas"'

class ColorText(TaggedText):
  "Colored text"

  start = '\\color'

  def process(self):
    self.color = self.header[1]
    self.tag = 'span class="' + self.color + '"'

class SizeText(TaggedText):
  "Sized text"

  start = '\\size'

  def process(self):
    self.size = self.header[1]
    self.tag = 'span class="' + self.size + '"'

class BoldText(TaggedText):
  "Bold text"

  start = '\\series bold'

  def process(self):
    self.tag = 'b'

class TextFamily(TaggedText):
  "A bit of text from a different family"

  start = '\\family'
  typetags = { 'typewriter':'tt', 'sans':'span class="sans"' }

  def process(self):
    "Parse the type of family"
    self.type = self.header[1]
    self.tag = TextFamily.typetags[self.type]

class Hfill(TaggedText):
  "Horizontall fill"

  start = '\\hfill'

  def process(self):
    self.tag = 'span class="right"'

class Align(Container):
  "Bit of aligned text"

  start = '\\align center'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class ListItem(Container):
  "An element in a list"

  starts = ['\\begin_layout Enumerate', '\\begin_layout Itemize']
  ending = '\\end_layout'

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  tags = {'Enumerate':'ol', 'Itemize':'ul'}

  def process(self):
    self.tag = ListItem.tags[self.header[1]]
    tag = TaggedText().complete(self.contents, 'li', True)
    self.contents = [tag]

class DeeperList(Container):
  "A nested list"

  start = '\\begin_deeper'
  ending = '\\end_deeper'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'ul'

ContainerFactory.types += [QuoteContainer, LyxLine, EmphaticText, SlantedText,
    VersalitasText, ColorText, SizeText, BoldText, TextFamily, Hfill, Align,
    ListItem, DeeperList]

