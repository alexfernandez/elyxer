#!/usr/bin/python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090131
# eLyXer containers for Lyx data that output HTML

from trace import Trace
from parse import *
from output import *


class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  @classmethod
  def comesnext(cls, reader):
    "Return if the current line matches"
    line = reader.currentline()
    if hasattr(cls, 'start'):
      return line.startswith(cls.start)
    if hasattr(cls, 'starts'):
      for start in cls.starts:
        if line.startswith(start):
          return True
    return False

  def parse(self, reader):
    "Parse a line reader"
    if hasattr(self, 'ending'):
      self.parser.ending = self.ending
    self.parser.factory = self.factory
    self.header = self.parser.parseheader(reader)
    self.begin = self.parser.begin
    self.contents = self.parser.parse(reader)
    self.process()
    self.parser = []

  def process(self):
    "Process contents"
    pass

  def finished(self, reader):
    "Find out if we are at the end"
    return reader.currentline().startswith(self.ending)

  def gethtml(self):
    "Get the resulting HTML"
    return self.output.gethtml(self)

  def __str__(self):
    "Get a description"
    return self.__class__.__name__ + '@' + str(self.begin)

  escapes = {'&':'&amp;', '<':'&lt;', '>':'&gt;'}

  def escape(self, line):
    "Escape a line to appear in HTML"
    pieces = Container.escapes.keys()
    # do the '&' first
    pieces.sort()
    for piece in pieces:
      if piece in line:
        line = line.replace(piece, Container.escapes[piece])
    return line

  def searchfor(self, check):
    "Search for an embedded element recursively"
    return self.searchinside(self.contents, check)

  def searchinside(self, contents, check):
    "Search for an embedded element in a list"
    for element in contents:
      if isinstance(element, Container):
        if check(element):
          return element
        result = self.searchinside(element.contents, check)
        if result:
          return result
    return None

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

class BlackBox(Container):
  "A container that does not output anything"

  starts = ['\\lyxformat', '\\begin_document', '\\begin_body',
      '\\end_body', '\\end_document', '\\family default', '\\color inherit',
      '\\shape default', '\\series default', '\\emph off',
      '\\bar no', '\\noun off', '\\emph default', '\\bar default',
      '\\noun default', '\\family roman', '\\series medium',
      '\\shape up', '\\size normal', '\\color none', '#LyX']

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

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

class StringContainer(Container):
  "A container for a single string"

  start = ''

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()
    
  replaces = { '`':u'‘', '\'':u'’', '\n':'', '--':u'—' }
  commands = { '\\SpecialChar \\ldots{}':u'…', '\\InsetSpace ~':'&nbsp;', '\\backslash':'\\' }

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.escape(line)
    replaced = self.changeline(replaced)
    self.contents = [replaced]
    if '\\' in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Error at ' + str(self.parser.begin) + ': ' + replaced.strip())

  def changeline(self, line):
    line = self.replacemap(line, StringContainer.replaces)
    if not '\\' in line:
      return line
    line = self.replacemap(line, StringContainer.commands)
    return line

  def replacemap(self, line, map):
    for piece in map:
      if piece in line:
        line = line.replace(piece, map[piece])
    return line
  
  def __str__(self):
    length = ''
    descr = ''
    if len(self.contents) > 0:
      length = str(len(self.contents[0]))
      descr = self.contents[0].strip()
    return 'StringContainer@' + str(self.begin) + '(' + str(length) + ')'

class Constant(StringContainer):
  "A constant string"

  def __init__(self, text):
    self.contents = [text]
    self.output = MirrorOutput()

  def __str__(self):
    return 'Constant'

class LangLine(Container):
  "A line with language information"

  start = '\\lang'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

  def process(self):
    self.lang = self.header[1]

class LyxLine(Container):
  "A Lyx line"

  start = '\\lyxline'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<hr class="line" />']

class TaggedText(Container):
  "Text inside a tag"

  def __init__(self):
    self.parser = TextParser()
    self.output = TagOutput()
    self.breaklines = False

  def complete(self, contents, tag, breaklines=False):
    "Complete the tagged text and return it"
    self.contents = contents
    self.tag = tag
    self.breaklines = breaklines
    return self

  def constant(self, text, tag):
    "Complete the tagged text with a constant"
    constant = Constant(text)
    return self.complete([constant], tag)

  def __str__(self):
    return 'Tagged <' + self.tag + '>'

class EmphaticText(TaggedText):
  "Text with emphatic mode"

  start = '\\emph on'

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

class Float(Container):
  "A floating inset"

  start = '\\begin_inset Float'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    self.tag = 'div class="' + self.type + '"'
    self.breaklines = True
    # skip over four float parameters
    del self.contents[0:3]

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
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.tag = 'div class="caption"'
    self.breaklines = True

class Align(Container):
  "Bit of aligned text"

  start = '\\align center'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class Title(Container):
  "The title of the whole document"

  start = '\\begin_layout Title'
  ending = '\\end_layout'

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TitleOutput()

  def process(self):
    self.title = self.contents[0].contents[0].strip()
    Trace.debug('Title: ' + self.title)

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

class Author(Layout):
  "The document author"

  start = '\\begin_layout Author'
  ending = '\\end_layout'

  def process(self):
    self.tag = 'h2'
    FooterOutput.author = self.contents[0].contents[0].strip()
    Trace.debug('Author: ' + FooterOutput.author)

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


