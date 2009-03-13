#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090312
# LyX structure in containers

from trace import Trace
from parse import *
from output import *
from container import *


class LyxHeader(Container):
  "Reads the header, outputs the HTML header"

  start = '\\begin_header'
  ending = '\\end_header'

  def __init__(self):
    self.parser = BoundedDummy()
    self.output = HeaderOutput()

class LyxFooter(Container):
  "Reads the footer, outputs the HTML footer"

  start = '\\end_body'
  ending = '\\end_document'

  def __init__(self):
    self.parser = BoundedDummy()
    self.output = FooterOutput()

class Float(Container):
  "A floating inset"

  start = '\\begin_inset Float'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    self.tag = 'div class="' + self.type + '"'

class InsetText(Container):
  "An inset of text in a lyx file"

  start = '\\begin_inset Text'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

class Caption(Container):
  "A caption for a figure or a table"

  start = '\\begin_inset Caption'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.tag = 'div class="caption"'
    self.breaklines = True

class Layout(Container):
  "A layout (block of text) inside a lyx file"

  start = '\\begin_layout '
  ending = '\\end_layout'

  typetags = { 'Quote':'blockquote', 'Standard':'div class="text"',
        'Subsubsection*':'h4', 'Chapter':'h1', 'Section':'h2',
        'Subsection': 'h3', 'Description':'div class="desc"',
        'Quotation':'blockquote', 'Center':'div class="center"',
        'Paragraph*':'div class="paragraph"', 'Part':'h1 class="part"',
        'Subsection*': 'h3'}

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    self.tag = 'div class="' + self.type + '"'
    if self.type in Layout.typetags:
      self.tag = Layout.typetags[self.type]

  def __str__(self):
    return 'Layout of type ' + self.type

class Title(Layout):
  "The title of the whole document"

  start = '\\begin_layout Title'
  ending = '\\end_layout'

  def process(self):
    self.tag = 'h1 class="title"'
    string = self.searchfor(lambda x: isinstance(x, StringContainer))
    self.title = string.contents[0]
    Trace.debug('Title: ' + self.title)

class Author(Layout):
  "The document author"

  start = '\\begin_layout Author'
  ending = '\\end_layout'

  def process(self):
    self.tag = 'h2 class="author"'
    string = self.searchfor(lambda x: isinstance(x, StringContainer))
    FooterOutput.author = string.contents[0]
    Trace.debug('Author: ' + FooterOutput.author)

class Inset(Container):
  "A generic inset in a LyX document"

  start = '\\begin_inset'
  ending = '\\end_inset'

  def __init__(self):
    self.contents = list()
    self.parser = InsetParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    self.tag = 'span class="' + self.type + '"'

  def __str__(self):
    return 'Inset of type ' + self.type

class Newline(Container):
  "A newline or line break"

  start = '\\begin_inset Newline'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.type = self.header[2]
    self.html = '<br/>'

ContainerFactory.types += [LyxHeader, LyxFooter, InsetText, Caption, Inset,
    Layout, Float, Title, Author, Newline]

