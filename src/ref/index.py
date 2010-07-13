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
# Alex 20100713
# eLyXer: indexing entries

from util.trace import Trace
from util.translate import *
from parse.parser import *
from out.output import *
from gen.container import *
from gen.styles import *
from ref.link import *
from ref.partkey import *


class ListInset(Container):
  "An inset with a list, normally made of links."

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def sortdictionary(self, dictionary):
    "Sort all entries in the dictionary"
    keys = dictionary.keys()
    # sort by name
    keys.sort()
    return keys

class ListOf(ListInset):
  "A list of entities (figures, tables, algorithms)"

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    text = Translator.translate('list-' + self.type)
    self.contents = [TaggedText().constant(text, 'div class="tocheader"', True)]

class TableOfContents(ListInset):
  "Table of contents"

  def process(self):
    "Parse the header and get the type"
    self.create(Translator.translate('toc'))

  def create(self, heading):
    "Create a table of contents with the given heading text."
    self.output = TaggedOutput().settag('div class="fulltoc"', True)
    self.contents = [TaggedText().constant(heading, 'div class="tocheader"', True)]
    return self

  def add(self, entry):
    "Add a new entry to the TOC."
    self.contents.append(entry)

class IndexEntry(Link):
  "An entry in the alphabetical index"

  entries = dict()
  arrows = dict()

  namescapes = {'!':'', '|':', ', '  ':' '}
  keyescapes = {' ':'-', '--':'-', ',':''}

  def process(self):
    "Put entry in index"
    if 'name' in self.parameters:
      name = self.parameters['name'].strip()
    else:
      name = self.extracttext()
    self.name = self.escape(name, IndexEntry.namescapes)
    key = self.escape(self.name, IndexEntry.keyescapes)
    if not key in IndexEntry.entries:
      # no entry yet; create
      entry = Link().complete(name, 'index-' + key, None, 'printindex')
      entry.name = name
      IndexEntry.entries[key] = entry
    if not key in IndexEntry.arrows:
      # no arrows yet; create list
      IndexEntry.arrows[key] = []
    self.index = len(IndexEntry.arrows[key])
    self.complete(u'↓', 'entry-' + key + '-' + unicode(self.index))
    self.destination = IndexEntry.entries[key]
    arrow = Link().complete(u'↑', 'index-' + key)
    arrow.destination = self
    IndexEntry.arrows[key].append(arrow)

  def __unicode__(self):
    "Return a printable representation."
    return 'Index entry for ' + self.name

class PrintIndex(ListInset):
  "Command to print an index"

  def process(self):
    "Create the alphabetic index"
    name = Translator.translate('index')
    self.partkey = PartKey().createindex(name)
    self.contents = [self.partkey.toclabel(),
        TaggedText().constant(name, 'h1 class="index"')]
    for key in self.sortdictionary(IndexEntry.entries):
      entry = IndexEntry.entries[key]
      entrytext = [IndexEntry.entries[key], Constant(': ')]
      contents = [TaggedText().complete(entrytext, 'i')]
      contents += self.extractarrows(key)
      self.contents.append(TaggedText().complete(contents, 'p class="printindex"',
          True))

  def extractarrows(self, key):
    "Extract all arrows (links to the original reference) for a key."
    arrows = []
    for arrow in IndexEntry.arrows[key]:
      arrows += [arrow, Constant(u', \n')]
    return arrows[:-1]

class NomenclatureEntry(Link):
  "An entry of LyX nomenclature"

  entries = dict()

  def process(self):
    "Put entry in index"
    symbol = self.parameters['symbol']
    description = self.parameters['description']
    key = symbol.replace(' ', '-').lower()
    if key in NomenclatureEntry.entries:
      Trace.error('Duplicated nomenclature entry ' + key)
    self.complete(u'↓', 'noment-' + key)
    entry = Link().complete(u'↑', 'nom-' + key)
    entry.symbol = symbol
    entry.description = description
    self.setmutualdestination(entry)
    NomenclatureEntry.entries[key] = entry

class PrintNomenclature(ListInset):
  "Print all nomenclature entries"

  def process(self):
    "Create the nomenclature."
    name = Translator.translate('nomenclature')
    self.partkey = PartKey().createindex(name)
    self.contents = [self.partkey.toclabel(),
        TaggedText().constant(name, 'h1 class="nomenclature"')]
    for key in self.sortdictionary(NomenclatureEntry.entries):
      entry = NomenclatureEntry.entries[key]
      contents = [entry, Constant(entry.symbol + u' ' + entry.description)]
      text = TaggedText().complete(contents, 'div class="Nomenclated"', True)
      self.contents.append(text)

class PostListInset(object):
  "Postprocess any container that contains a list inset."

  def postprocess(self, container):
    "Postprocess a container, extract any list inset and return it."
    return container

Postprocessor.rootstages += [PostListInset()]

