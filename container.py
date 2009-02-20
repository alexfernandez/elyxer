#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 31-01-2009
# Generate custom HTML version from Lyx document
# Containers for Lyx data that output HTML

import sys
import re
import codecs
import os.path
import subprocess
from trace import Trace


class LineReader(object):
  "Reads a file line by line"

  def __init__(self, arg):
    self.contents = list()
    self.index = 0
    self.readfile(arg)

  def readfile(self, filename):
    file = codecs.open(filename, 'r', "utf-8")
    try:
      self.contents = file.readlines()
    finally:
      file.close()

  def currentline(self):
    return self.contents[self.index]

  def nextline(self):
    "Go to next line"
    self.index += 1

  def finished(self):
    return self.index >= len(self.contents)

  def skipblanks(self):
    "Skip blank lines: spaces, tabs"
    while len(self.currentline().strip()) == 0:
      self.nextline()

class ContainerFactory(object):
  "Creates containers depending on the first line"

  @classmethod
  def createcontainer(cls, reader):
    "Get the container corresponding to the reader contents"
    containerlist = [Layout, StyledText, Image, QuoteContainer, BlackBox,
        IndexEntry, BiblioEntry, BiblioCite, LangLine, Reference, Label,
        TextFamily, Formula, PrintIndex, LyxHeader, URL, ListOf,
        TableOfContents, Hfill, ColorText,
        # do not add to this line
        Float, Inset, StringContainer]
    for type in containerlist:
      if type.comesnext(reader):
        container = type.__new__(type)
        container.__init__()
        container.parseheader(reader)
        container.parse(reader)
        return container
    Trace.error('Error in line ' + reader.currentline())

class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  @classmethod
  def comesnext(cls, reader):
    "Return if the next line matches"
    return reader.currentline().startswith(cls.start)

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    reader.nextline()

  def parse(self, reader):
    "Parse the contents of the container"
    while not self.finished(reader):
      container = ContainerFactory.createcontainer(reader)
      self.contents.append(container)
    # skip last line
    reader.nextline()

  def finished(self, reader):
    "Find out if we are at the end"
    return reader.currentline().startswith(self.ending)

  def gethtml(self):
    "Get HTML code, invalid in Container"
    Trace.error('Error getting HTML from empty container')

class QuoteContainer(Container):
  "A container for a pretty quote"

  start = '\\begin_inset Quotes'

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    self.type = reader.currentline().split()[2]
    reader.nextline()

  def parse(self, reader):
    "Skip a couple of lines"
    reader.nextline()
    reader.nextline()

  def gethtml(self):
    "Get the HTML for a quote"
    if self.type == 'eld':
      return u'“'
    elif self.type == 'erd':
      return u'”'
    else:
      Trace.error('Error in quote ' + self.type)

class BlackBox(Container):
  "A container that does not output anything"

  @classmethod
  def comesnext(cls, reader):
    "Return if the next line matches"
    if not reader.currentline().startswith('\\'):
      return False
    lines = ['\\lyxformat', '\\begin_document', '\\begin_body',
        '\\end_body', '\\end_document', '\\family default']
    for line in lines:
      if reader.currentline().startswith(line):
        return True
    return False

  def parse(self, reader):
    "Do nothing"
    pass

  def gethtml(self):
    "Get nothing out"
    return []

class LyxHeader(Container):
  "Reads the header, does nothing with it"

  start = '\\begin_header'
  ending = '\\end_header'

  def parse(self, reader):
    "Skip over every line"
    while not self.finished(reader):
      reader.nextline()
    # skip last line
    reader.nextline()

  def gethtml(self):
    "Get nothing out"
    return []

class StringContainer(Container):
  "A container for a single string"

  @classmethod
  def comesnext(cls, reader):
    "Return if the next line is a string, always true"
    return True

  def parseheader(self, reader):
    "Parse the header of the container: pass"
    pass

  def parse(self, reader):
    "Read the single line, replacing problematic characters"
    line = reader.currentline()
    replacemap = { '`':u'‘', '\'':u'’', '\n':'', '\\SpecialChar \\ldots{}':u'…',
        '\\InsetSpace ~':'&nbsp;' }
    for piece in replacemap:
      line = line.replace(piece, replacemap[piece])
    if line.startswith('\\'):
      Trace.error('Error in line ' + line.strip())
    if len(line) > 0:
      self.contents.append(line)
    reader.nextline()

  def gethtml(self):
    "Get the HTML output of the converter as a list"
    return self.contents

class Image(Container):
  "An embedded image"

  start = '\\begin_inset Graphics'
  ending = '\\end_inset'

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    reader.nextline()
    self.url = reader.currentline().split()[1]
    reader.nextline()

  def gethtml(self):
    "Get the HTML output of the image as a list"
    cssclass = 'embedded'
    if hasattr(self, 'figure') and self.figure:
      cssclass = 'figure'
    return ['<img class="' + cssclass + '" src="' + self.destination +
        '" alt="' + os.path.basename(self.destination) + '" width="' + 
        str(self.width) + '" height="' + str(self.height) + '"/>\n']

class LangLine(Container):
  "A line with language information"

  start = '\\lang '
  ending = '\\lang '

  def parseheader(self, reader):
    "Parse the language"
    self.lang = reader.currentline().split()[1]

  def gethtml(self):
    "Lang is not relevant for HTML"
    return []

class LatexCommand(Container):
  "A generic Latex command"

  @classmethod
  def comesnext(cls, reader):
    "Return if the current line has an index"
    return reader.currentline().startswith('\\begin_inset LatexCommand ' + cls.command)

  ending = '\\end_inset'

class PrintIndex(LatexCommand):
  "Command to print an index"

  command = 'printindex'

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    reader.nextline()

  def gethtml(self):
    "Get the HTML code for the index"
    html = [u'<h1>Índice Alfabético</h1>\n']
    for key in self.sortentries():
      entries = IndexEntry.entries[key]
      for entry in entries:
        if entries.index(entry) == 0:
          html.append(u'<p class="printindex">\n<i><a class="printindex" name="' +
              key + '">' + entries[0].name + '</a></i>: ')
        else:
          html.append(u', \n')
        html.append('<a href="#' + entry.key +
            '-' + str(entry.index) + u'">↑</a>')
      html.append('</p>\n')
    return html

  def sortentries(self):
    "Sort all entries in the index"
    keys = IndexEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

class NamedCommand(LatexCommand):
  "A Latex command with a name or key on the next line"

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    reader.nextline()
    self.name = reader.currentline().split('"')[1]
    self.key = self.name.replace(' ', '-')
    reader.nextline()

class IndexEntry(NamedCommand):
  "An entry in the alphabetical index"

  command = 'index'

  entries = dict()

  def parse(self, reader):
    "Order the result of the parse"
    NamedCommand.parse(self, reader)
    if not self.key in IndexEntry.entries:
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)

  def gethtml(self):
    "Get the HTML code for the entry"
    return ['<a class="index" name="' + self.key + '-' + str(self.index) +
        '" href="#' + self.key + u'">↓</a>']

class BiblioEntry(NamedCommand):
  "A bibliography entry"

  command = 'bibitem'

  def gethtml(self):
    "Get the HTML code for the entry"
    html = ['[']
    for cite in BiblioCite.entries[self.key]:
      c = str(cite)
      html.append('<a class="biblio" name="' + c + '" href="#back-' + c + '">' + c + '</a>')
      html.append(',')
    if len(html) > 1:
      html.pop()
    html.append('] ')
    return html

class BiblioCite(NamedCommand):
  "Cite of a bibliography entry"

  index = 0
  entries = dict()
  command = 'cite'

  def gethtml(self):
    "Get the HTML code for the entry"
    BiblioCite.index += 1
    if not self.key in BiblioCite.entries:
      BiblioCite.entries[self.key] = []
    BiblioCite.entries[self.key].append(BiblioCite.index)
    cite = str(BiblioCite.index)
    return ['<a class="cite" name="back-' + cite + '" href="#' + cite + '"><sup>[' + cite + ']</sup></a>']

class Reference(NamedCommand):
  "A reference to a label"

  command = 'ref'

  def gethtml(self):
    "Get the HTML code for the entry"
    return ['<a class="ref" href="#' + self.key + '">' + self.name + '</a>']

class Label(NamedCommand):
  "A label to be referenced"

  command = 'label'

  def gethtml(self):
    "Get the HTML code for the entry"
    return ['<a class="label" name="' + self.key + '"> </a>']

class URL(NamedCommand):
  "A clickable URL"

  command = 'url'

  def gethtml(self):
    "Get the HTML code for the entry"
    return ['<a class="url" href="' + self.name + '">' + self.name + '</a>']

class HtmlTag(Container):
  "Outputs an HTML tag surrounding the contents"

  def gethtml(self):
    "return the HTML code for the tag"
    if len(self.contents) == 1 and isinstance(self.contents[0], StringContainer):
      # with one line do not break lines
      self.breaklines = False
    if not hasattr(self, 'tag'):
      # choose tag from type
      self.tag = self.__class__.typetags[self.type]
    html = [self.getopen()]
    for container in self.contents:
      html += container.gethtml()
    html.append(self.getclose())
    return html

  def getopen(self):
    "Get opening line"
    if not hasattr(self, 'breaklines'):
      self.breaklines = False
    if not hasattr(self, 'extratag'):
      self.extratag = ''
    open = '<' + self.tag + self.extratag + '>'
    if self.breaklines:
      return '\n' + open + '\n'
    return open

  def getclose(self):
    "Get closing line"
    close = '</' + self.tag.split()[0] + '>'
    if self.breaklines:
      return '\n' + close + '\n'
    return close

class StyledText(HtmlTag):
  "A bit of styled text"

  typetags = { 'emph':'i', 'noun':'span class="versalitas"' }

  @classmethod
  def comesnext(cls, reader):
    "Return if the next line is a style"
    line = reader.currentline()
    if not line.startswith('\\'):
      return False
    split = line.split()
    if len(split) < 2:
      return False
    return line.split()[1] == 'on'

  def parseheader(self, reader):
    "Parse the type of style"
    self.type = reader.currentline().split()[0].strip('\\')
    reader.nextline()

  def finished(self, reader):
    "Find out if we are at the end"
    return reader.currentline().startswith('\\' + self.type + ' default')

class ColorText(HtmlTag):
  "Colored text"

  start = '\\color '
  ending = '\\color inherit'
  typetags = { 'red':'span class="red"', 'green':'span class="green"' }

  def parseheader(self, reader):
    "Parse the color"
    self.type = reader.currentline().split()[1]
    reader.nextline()

class TextFamily(HtmlTag):
  "A bit of text from a different family"

  start = '\\family '
  typetags = { 'typewriter':'tt', 'sans':'span class="sans"' }

  def parseheader(self, reader):
    "Parse the type of family"
    self.type = reader.currentline().split()[1]
    reader.nextline()

  def parse(self, reader):
    "Parse the contents of the container"
    self.tag = 'tt'
    while not self.finished(reader):
      container = ContainerFactory.createcontainer(reader)
      self.contents.append(container)
    # do not skip last line

  def finished(self, reader):
    "Find out if we are at the end"
    if reader.currentline().startswith('\\family default'):
      return True
    return reader.currentline().startswith('\\end_layout')

class Formula(Container):
  "A Latex formula"

  start = '\\begin_inset Formula'
  ending = '\\end_inset'

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    if reader.currentline().find('$') > 0:
      self.formula = reader.currentline().split('$')[1]
    else:
      # formula of the form \[...\]
      reader.nextline()
      self.formula = reader.currentline().strip('\\[\n')
    reader.nextline()

  def gethtml(self):
    "return the HTML code for the formula"
    return ['<span class="formula">' + self.formula + '</span>']

class ListOf(Container):
  "A list of entities (figures, tables, algorithms)"

  start = '\\begin_inset FloatList '
  ending = '\\end_inset'

  def parseheader(self, reader):
    "Parse the header and get the type"
    self.type = reader.currentline().split()[2]
    Trace.debug('List of: ' + self.type)
    reader.nextline()

  def gethtml(self):
    "return the HTML code"
    names = {'figure':'figuras', 'table':'tablas', 'algorithm':'listados',
        'contents':'contenidos'}
    return [u'<div class="list">Índice de ' + names[self.type] + '</div>']

class TableOfContents(ListOf):
  "Table of contents"

  start = '\\begin_inset LatexCommand tableofcontents'

  def parseheader(self, reader):
    "Parse the header and get the type"
    self.type = 'contents'
    Trace.debug('List of: ' + self.type)
    reader.nextline()

class Hfill(HtmlTag):
  "Horizontall fill"

  start = '\\hfill'

  def parse(self, reader):
    "Parse just a line"
    string = StringContainer()
    string.parse(reader)
    self.contents.append(string)
    self.tag = 'p class="right"'

class Float(HtmlTag):
  "A floating inset"

  start = '\\begin_inset Float '
  ending = '\\end_inset'

  def parseheader(self, reader):
    "Parse the float type"
    self.type = reader.currentline().split()[2]
    self.tag = 'div class="' + self.type + '"'
    self.breaklines = True
    # skip over three float parameters
    for i in range(4):
      reader.nextline()

class Inset(HtmlTag):
  "An inset (block of anything) inside a lyx file"

  start = '\\begin_inset '
  ending = '\\end_inset'

  typetags = {'Text':'div class="text"', 'Caption':'div class="caption"', 'Tabular':'table'}

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    self.type = reader.currentline().strip()[len(Inset.start):]
    self.breaklines = True
    if not self.type in Inset.typetags:
      Trace.error('Unrecognized inset: ' + self.type)
    reader.nextline()

class Layout(HtmlTag):
  "A layout (block of text) inside a lyx file"

  start = '\\begin_layout '
  ending = '\\end_layout'

  typetags = {'Quote':'blockquote', 'Standard':'p', 'Title':'h1', 'Author':'h2',
        'Subsubsection*':'h4', 'Enumerate':'li', 'Chapter':'h1', 'Section':'h2', 'Subsection': 'h3',
        'Bibliography':'p class="biblio"', 'Ordered':'ol', 'Description':'p class="desc"',
        'Quotation':'blockquote', 'Itemize':'li', 'Unordered':'ul', 'Center':'p class="center"'}

  title = 'El libro gordo'

  def parseheader(self, reader):
    "Parse the header of the container: skip it"
    self.type = reader.currentline().split()[1]
    self.breaklines = True
    reader.nextline()
    if reader.currentline().startswith('\\align center'):
      self.type = 'Center'
      reader.nextline()

  def parse(self, reader):
    "Parse the title"
    Container.parse(self, reader)
    if self.type == 'Title':
      Layout.title = self.contents[0].contents[0]
      Trace.debug('Title: ' + Layout.title)

  def __str__(self):
    return 'Layout of type ' + self.type

