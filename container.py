#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 2009-01-31
# Generate custom HTML version from Lyx document
# Containers for Lyx data that output HTML

from trace import Trace
from parse import *


class ContainerFactory(object):
  "Creates containers depending on the first line"

  @classmethod
  def create(cls, reader):
    "Get the container corresponding to the reader contents"
    # Trace.debug('processing ' + reader.currentline().strip())
    containerlist = [BlackBox,
        # do not add above this line
        Layout, EmphaticText, VersalitasText, Image, QuoteContainer,
        IndexEntry, BiblioEntry, BiblioCite, LangLine, Reference, Label,
        TextFamily, Formula, PrintIndex, LyxHeader, URL, ListOf,
        TableOfContents, Hfill, ColorText, SizeText, BoldText, LyxLine,
        Align,
        # do not add below this line
        Float, Inset, StringContainer]
    for type in containerlist:
      if type.comesnext(reader):
        container = type.__new__(type)
        container.__init__()
        if hasattr(container, 'ending'):
          container.parser.ending = container.ending
        container.parser.factory = ContainerFactory
        container.header = container.parser.parseheader(reader)
        container.contents = container.parser.parse(reader)
        container.process()
        return container
    Trace.error('Error creating container at ' + str(reader.index) + ': ' + reader.currentline())

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

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    reader.nextline()

  def parse(self, reader):
    "Parse the contents of the container"
    while not self.finished(reader):
      container = ContainerFactory.create(reader)
      self.contents.append(container)
    # skip last line
    reader.nextline()

  def process(self):
    "Process contents"
    pass

  def finished(self, reader):
    "Find out if we are at the end"
    return reader.currentline().startswith(self.ending)
 
  def gethtml(self):
    "Get the HTML output"
    return self.output.gethtml(self)

  def __str__(self):
    "Get a description"
    return 'Container ' + self.__class__.__name__

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
      '\\noun default']

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class LyxHeader(Container):
  "Reads the header, does nothing with it"

  start = '\\begin_header'
  ending = '\\end_header'

  def __init__(self):
    self.parser = BoundedDummy()
    self.output = EmptyOutput()

class StringContainer(Container):
  "A container for a single string"

  @classmethod
  def comesnext(cls, reader):
    "Return if the next line is a string, always true"
    return True

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()
    
  replaces = { '`':u'‘', '\'':u'’', '\n':'', '--':u'—' }
  commands = { '\\SpecialChar \\ldots{}':u'…', '\\InsetSpace ~':'&nbsp;' }

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.changeline(line)
    self.contents = [replaced]
    if '\\' in replaced:
      # unprocessed commands
      Trace.error('Error in ' + str(line) + ': ' + replaced.strip())

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

class Image(Container):
  "An embedded image"

  start = '\\begin_inset Graphics'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = ImageCommand()
    self.output = ImageOutput()
    self.figure = False

  def process(self):
    self.url = self.header[1]

class PrintIndex(Container):
  "Command to print an index"

  start = '\\begin_inset LatexCommand printindex'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = IndexOutput()

  def process(self):
    self.keys = self.sortentries()
    self.entries = IndexEntry.entries

  def sortentries(self):
    "Sort all entries in the index"
    keys = IndexEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

class IndexEntry(Container):
  "An entry in the alphabetical index"

  start = '\\begin_inset LatexCommand index'
  ending = '\\end_inset'

  entries = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = IndexEntryOutput()

  def process(self):
    "Put entry in index"
    self.key = self.parser.key
    self.name = self.parser.name
    if not self.key in IndexEntry.entries:
      # no entry; create
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)

class BiblioEntry(Container):
  "A bibliography entry"

  start = '\\begin_inset LatexCommand bibitem'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = BiblioEntryOutput()

  def process(self):
    self.key = self.parser.key
    self.cites = BiblioCite.entries[self.key]

class BiblioCite(Container):
  "Cite of a bibliography entry"

  start = '\\begin_inset LatexCommand cite'
  ending = '\\end_inset'

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = BiblioCiteOutput()

  def process(self):
    self.key = self.parser.key
    BiblioCite.index += 1
    if not self.key in BiblioCite.entries:
      BiblioCite.entries[self.key] = []
    BiblioCite.entries[self.key].append(BiblioCite.index)
    self.cite = str(BiblioCite.index)

class Reference(Container):
  "A reference to a label"

  start = '\\begin_inset LatexCommand ref'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = FixedOutput()

  def process(self):
    self.html =  ['<a class="ref" href="#' + self.parser.key +
        '">' + self.parser.name + '</a>']

class Label(Container):
  "A label to be referenced"

  start = '\\begin_inset LatexCommand label'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<a class="label" name="' + self.parser.key + '"> </a>']

class URL(Container):
  "A clickable URL"

  start = '\\begin_inset LatexCommand url'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<a class="url" href="' + self.parser.name +
        '">' + self.parser.name + '</a>']

class EmphaticText(Container):
  "Text with emphatic mode"

  start = '\\emph on'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.tag = 'i'
    self.breaklines = False

class VersalitasText(Container):
  "Text in versalitas"

  start = '\\noun on'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.tag = 'span class="versalitas"'
    self.breaklines = False

class ColorText(Container):
  "Colored text"

  start = '\\color'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.breaklines = False

  def process(self):
    self.color = self.header[1]
    self.tag = 'span class="' + self.color + '"'

class SizeText(Container):
  "Sized text"

  start = '\\size'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.breaklines = False

  def process(self):
    self.size = self.header[1]
    self.tag = 'span class="' + self.size + '"'

class BoldText(Container):
  "Bold text"

  start = '\\bold'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.breaklines = False

  def process(self):
    self.tag = 'b'

class TextFamily(Container):
  "A bit of text from a different family"

  start = '\\family'
  typetags = { 'typewriter':'tt', 'sans':'span class="sans"' }

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.breaklines = False

  def process(self):
    "Parse the type of family"
    self.type = self.header[1]
    self.tag = TextFamily.typetags[self.type]

class Formula(Container):
  "A Latex formula"

  start = '\\begin_inset Formula'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = FormulaParser()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<span class="formula">' + self.contents[0] + '</span>']

class ListOf(Container):
  "A list of entities (figures, tables, algorithms)"

  start = '\\begin_inset FloatList'
  ending = '\\end_inset'

  names = {'figure':'figuras', 'table':'tablas', 'algorithm':'listados',
      'tableofcontents':'contenidos'}

  def __init__(self):
    self.parser = BoundedParser()
    self.output = FixedOutput()

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    Trace.debug('List of: ' + self.type)
    self.html = [u'<div class="list">Índice de ' + ListOf.names[self.type] + '</div>']

class TableOfContents(ListOf):
  "Table of contents"

  start = '\\begin_inset LatexCommand tableofcontents'

class Hfill(Container):
  "Horizontall fill"

  start = '\\hfill'

  def __init__(self):
    self.parser = OneLiner()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.tag = 'p class="right"'

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
    # skip over three float parameters
    del self.contents[0:2]

class Inset(Container):
  "An inset (block of anything) inside a lyx file"

  start = '\\begin_inset '
  ending = '\\end_inset'

  typetags = {'Text':'div class="text"', 'Caption':'div class="caption"', 'Tabular':'table'}

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    if not self.type in Inset.typetags:
      Trace.error('Unrecognized inset: ' + self.type)
      return
    self.tag = Inset.typetags[self.type]

class Align(Container):
  "Bit of aligned text"

  start = '\\align center'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class Layout(Container):
  "A layout (block of text) inside a lyx file"

  start = '\\begin_layout '
  ending = '\\end_layout'

  typetags = {'Quote':'blockquote', 'Standard':'p', 'Title':'h1', 'Author':'h2',
        'Subsubsection*':'h4', 'Enumerate':'li', 'Chapter':'h1', 'Section':'h2', 'Subsection': 'h3',
        'Bibliography':'p class="biblio"', 'Ordered':'ol', 'Description':'p class="desc"',
        'Quotation':'blockquote', 'Itemize':'li', 'Unordered':'ul', 'Center':'p class="center"'}

  title = 'El libro gordo'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    self.tag = Layout.typetags[self.type]
    if self.type == 'Title':
      Layout.title = self.contents[0].contents[0].strip()
      Trace.debug('Title: ' + Layout.title)

  def __str__(self):
    return 'Layout of type ' + self.type

