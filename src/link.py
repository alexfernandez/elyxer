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
# Alex 20090218
# eLyXer links and nodes

from trace import Trace
from parse import *
from output import *
from container import *
from styles import *


class Link(Container):
  "A link to another part of the document"

  def __init__(self):
    self.contents = list()
    self.output = LinkOutput()

  def complete(self, text, anchor, url, type = None):
    self.contents = [Constant(text)]
    if anchor:
      self.anchor = anchor
    if url:
      self.url = url
    if type:
      self.type = type
    return self

class Label(Container):
  "A label to be referenced"

  starts = ['\\begin_inset LatexCommand label', '\\begin_inset CommandInset label']
  ending = '\\end_inset'

  labels = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    self.anchor = self.parser.parameters['name']
    Label.labels[self.anchor] = self
    self.contents = [Constant(' ')]

class Reference(Link):
  "A reference to a label"

  starts = ['\\begin_inset LatexCommand ref', '\\begin_inset CommandInset ref']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()
    self.direction = u'↓'

  def process(self):
    key = self.parser.parameters['reference']
    self.url = '#' + key
    if key in Label.labels:
      # already seen
      self.direction = u'↑'
    self.contents = [Constant(self.direction)]

class BiblioCite(Container):
  "Cite of a bibliography entry"

  starts = ['\\begin_inset LatexCommand cite', '\\begin_inset CommandInset citation']
  ending = '\\end_inset'

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.tag = 'sup'
    self.breaklines = False

  def process(self):
    "Add a cite to every entry"
    self.contents = list()
    keys = self.parser.parameters['key'].split(',')
    for key in keys:
      BiblioCite.index += 1
      number = str(BiblioCite.index)
      link = Link().complete(number, 'cite-' + number, '#' + number)
      self.contents.append(link)
      self.contents.append(Constant(','))
      if not key in BiblioCite.entries:
        BiblioCite.entries[key] = []
      BiblioCite.entries[key].append(number)
    if len(keys) > 0:
      # remove trailing ,
      self.contents.pop()

class Bibliography(Container):
  "A bibliography layout containing an entry"

  start = '\\begin_layout Bibliography'
  ending = '\\end_layout'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'p class="biblio"'

class BiblioEntry(Container):
  "A bibliography entry"

  starts = ['\\begin_inset LatexCommand bibitem', '\\begin_inset CommandInset bibitem']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.tag = 'span class="entry"'
    self.breaklines = False

  def process(self):
    "Get all the cites of the entry"
    cites = list()
    key = self.parser.parameters['key']
    if key in BiblioCite.entries:
      cites = BiblioCite.entries[key]
    self.contents = [Constant('[')]
    for cite in cites:
      link = Link().complete(cite, cite, '#cite-' + cite)
      self.contents.append(link)
      self.contents.append(Constant(','))
    if len(cites) > 0:
      self.contents.pop(-1)
    self.contents.append(Constant('] '))

class ListOf(Container):
  "A list of entities (figures, tables, algorithms)"

  start = '\\begin_inset FloatList'
  ending = '\\end_inset'

  names = {'figure':'figures', 'table':'tables', 'algorithm':'listings'}

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    self.tag = 'div class="list"'
    self.contents = [Constant(u'List of ' + ListOf.names[self.type])]

class TableOfContents(Container):
  "Table of contents"

  starts = ['\\begin_inset LatexCommand tableofcontents',
      '\\begin_inset CommandInset toc']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Parse the header and get the type"
    self.tag = 'div class="toc"'
    self.contents = [Constant(u'Table of Contents')]

class IndexEntry(Link):
  "An entry in the alphabetical index"

  start = '\\begin_inset LatexCommand index'
  ending = '\\end_inset'

  entries = dict()

  namescapes = {'!':'', '|':', ', '  ':' '}
  keyescapes = {' ':'-', '--':'-', ',':''}

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()
    self.breaklines = False

  def process(self):
    "Put entry in index"
    name = self.parser.parameters['name'].strip()
    self.name = self.escape(name, IndexEntry.namescapes)
    self.key = self.escape(self.name, IndexEntry.keyescapes)
    if not self.key in IndexEntry.entries:
      # no entry; create
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)
    self.anchor = 'entry-' + self.key + '-' + str(self.index)
    self.url = '#index-' + self.key
    self.contents = [Constant(u'↓')]

class LayoutIndexEntry(IndexEntry):
  "An entry with the name in a layout"

  start = '\\begin_inset Index'
  ending = '\\end_inset'

  def process(self):
    "Read entry from layout and put in index"
    name = ''
    layout = self.contents[0]
    for element in layout.contents:
      if isinstance(element, StringContainer):
        name += element.contents[0]
      else:
        name += ' '
    self.parser.parameters['name'] = name
    IndexEntry.process(self)

class PrintIndex(Container):
  "Command to print an index"

  starts = ['\\begin_inset LatexCommand printindex',
      '\\begin_inset CommandInset index_print']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

  def process(self):
    "Create the alphabetic index"
    self.contents = [TaggedText().constant('Index', 'h1 class="index"'),
        Constant('\n')]
    for key in self.sortentries():
      name = IndexEntry.entries[key][0].name
      entry = [Link().complete(name, 'index-' + key, None, 'printindex'),
          Constant(': ')]
      contents = [TaggedText().complete(entry, 'i')]
      contents += self.createarrows(key, IndexEntry.entries[key])
      self.contents.append(TaggedText().complete(contents, 'p class="printindex"',
          True))

  def sortentries(self):
    "Sort all entries in the index"
    keys = IndexEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

  def createarrows(self, key, entries):
    "Create an entry in the index"
    arrows = []
    for entry in entries:
      link = Link().complete(u'↑', 'index-' + entry.key,
          '#entry-' + entry.key + '-' + str(entry.index))
      arrows += [link, Constant(u', \n')]
    return arrows[:-1]

class NomenclatureEntry(Link):
  "An entry of LyX nomenclature"

  start = '\\begin_inset CommandInset nomenclature'
  ending = '\\end_inset'

  entries = {}

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Put entry in index"
    self.symbol = self.parser.parameters['symbol']
    self.description = self.parser.parameters['description']
    self.key = self.symbol.replace(' ', '-').lower()
    NomenclatureEntry.entries[self.key] = self
    self.anchor = 'noment-' + self.key
    self.url = '#nom-' + self.key
    self.contents = [Constant(u'↓')]

class NomenclaturePrint(Container):
  "Print all nomenclature entries"

  start = '\\begin_inset CommandInset nomencl_print'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    self.keys = self.sortentries()
    self.contents = [TaggedText().constant('Nomenclature', 'h1 class="nomenclature"')]
    for key in self.keys:
      entry = NomenclatureEntry.entries[key]
      contents = [Link().complete(u'↑', 'nom-' + key, '#noment-' + key)]
      contents.append(Constant(entry.symbol + u' '))
      contents.append(Constant(entry.description))
      text = TaggedText().complete(contents, 'div class="Nomenclated"', True)
      self.contents.append(text)

  def sortentries(self):
    "Sort all entries in the index"
    keys = NomenclatureEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

class URL(Link):
  "A clickable URL"

  starts = ['\\begin_inset LatexCommand url',
      '\\begin_inset LatexCommand htmlurl', '\\begin_inset CommandInset href']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Read URL from parameters"
    self.url = self.escape(self.parser.parameters['target'])
    if 'type' in self.parser.parameters:
      self.url = self.escape(self.parser.parameters['type']) + self.url
    name = self.url
    if 'name' in self.parser.parameters:
      name = self.parser.parameters['name']
    self.contents = [Constant(name)]

class FlexURL(URL):
  "A flexible URL"

  start = '\\begin_inset Flex URL'
  ending = '\\end_inset'

  def process(self):
    "Read URL from contents"
    text = self.searchfor(StringContainer).contents[0]
    self.url = self.escape(text)
    self.contents = [Constant(self.url)]

class LinkOutput(object):
  "A link pointing to some destination"
  "Or an anchor (destination)"

  def gethtml(self, container):
    "Get the HTML code for the link"
    type = container.__class__.__name__
    if hasattr(container, 'type'):
      type = container.type
    tag = 'a class="' + type + '"'
    if hasattr(container, 'anchor'):
      tag += ' name="' + container.anchor + '"'
    if hasattr(container, 'url'):
      tag += ' href="' + container.url + '"'
    text = TaggedText().complete(container.contents, tag)
    return text.gethtml()

ContainerFactory.types += [Label, Reference, BiblioCite, Bibliography,
    BiblioEntry, ListOf, TableOfContents, IndexEntry, PrintIndex, URL,
    FlexURL, NomenclatureEntry, NomenclaturePrint, LayoutIndexEntry]

