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
# eLyXer links

from util.trace import Trace
from parse.parser import *
from io.output import *
from gen.container import *
from gen.styles import *
from util.numbering import *


class Link(Container):
  "A link to another part of the document"

  def __init__(self):
    self.contents = list()
    self.output = LinkOutput()

  def complete(self, text, anchor = None, url = None, type = None):
    self.contents = [Constant(text)]
    if anchor:
      self.anchor = anchor
    if url:
      self.url = url
    if type:
      self.type = type
    return self

class ListOf(Container):
  "A list of entities (figures, tables, algorithms)"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('div class="list"', True)

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    self.contents = [Constant(TranslationConfig.lists[self.type])]

class TableOfContents(Container):
  "Table of contents"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('div class="toc"', True)

  def process(self):
    "Parse the header and get the type"
    self.contents = [Constant(TranslationConfig.constants['toc'])]

class IndexEntry(Link):
  "An entry in the alphabetical index"

  entries = dict()

  namescapes = {'!':'', '|':', ', '  ':' '}
  keyescapes = {' ':'-', '--':'-', ',':''}

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Put entry in index"
    if 'name' in self.parameters:
      name = self.parameters['name'].strip()
    else:
      name = self.extracttext()
    self.name = self.escape(name, IndexEntry.namescapes)
    self.key = self.escape(self.name, IndexEntry.keyescapes)
    if not self.key in IndexEntry.entries:
      # no entry; create
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)
    self.anchor = 'entry-' + self.key + '-' + unicode(self.index)
    self.url = '#index-' + self.key
    self.contents = [Constant(u'↓')]

class PrintIndex(Container):
  "Command to print an index"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

  def process(self):
    "Create the alphabetic index"
    index = TranslationConfig.constants['index']
    self.contents = [TaggedText().constant(index, 'h1 class="index"'),
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
          '#entry-' + entry.key + '-' + unicode(entry.index))
      arrows += [link, Constant(u', \n')]
    return arrows[:-1]

class NomenclatureEntry(Link):
  "An entry of LyX nomenclature"

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

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    self.keys = self.sortentries()
    nomenclature = TranslationConfig.constants['nomenclature']
    self.contents = [TaggedText().constant(nomenclature, 'h1 class="nomenclature"')]
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

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Read URL from parameters"
    name = self.escape(self.parser.parameters['target'])
    if 'type' in self.parser.parameters:
      self.url = self.escape(self.parser.parameters['type']) + name
    else:
      self.url = name
    if 'name' in self.parser.parameters:
      name = self.parser.parameters['name']
    self.contents = [Constant(name)]

class FlexURL(URL):
  "A flexible URL"

  def process(self):
    "Read URL from contents"
    self.url = self.extracttext()

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

