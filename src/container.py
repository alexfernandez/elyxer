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

class BlackBox(Container):
  "A container that does not output anything"

  starts = ['\\lyxformat', '\\begin_document', '\\begin_body',
      '\\end_body', '\\end_document', '\\family default', '\\color inherit',
      '\\shape default', '\\series default', '\\emph off',
      '\\bar no', '\\noun off', '\\emph default', '\\bar default',
      '\\noun default', '\\family roman', '\\series medium',
      '\\shape up', '\\size normal', '\\color none', '#LyX', '\\noindent']

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
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    self.tag = 'span class="' + self.type + '"'
    # remove status open/collapsed
    if len(self.contents) > 0 and isinstance(self.contents[0], StringContainer):
      if self.contents[0].contents[0].startswith('status'):
        del(self.contents[0])

  def __str__(self):
    return 'Inset of type ' + self.type

class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox, Title, Author, LangLine, LyxHeader, LyxFooter, InsetText,
      Caption, Inset, Layout, Float, StringContainer]

  def __init__(self):
    self.tree = ParseTree(ContainerFactory.types)

  def create(self, reader):
    "Get the container and parse it"
    # Trace.debug('processing ' + reader.currentline().strip())
    type = self.tree.find(reader)
    container = type.__new__(type)
    container.__init__()
    container.factory = self
    container.parse(reader)
    return container

