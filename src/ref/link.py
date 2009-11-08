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
    Container.__init__(self)
    self.parser = InsetParser()
    self.output = LinkOutput()
    self.anchor = None
    self.url = None
    self.type = None
    self.page = None
    self.target = None
    if Options.target:
      self.target = Options.target

  def complete(self, text, anchor = None, url = None, type = None):
    "Complete the link."
    self.contents = [Constant(text)]
    if anchor:
      self.anchor = anchor
    if url:
      self.url = url
    if type:
      self.type = type
    return self

  def setdestination(self, destination):
    "Set another link as the destination of this one."
    if not destination.anchor:
      Trace.error('Missing anchor in link destination ' + unicode(destination))
      return
    self.url = '#' + destination.anchor
    if destination.page:
      self.url = destination.page + self.url

  def setmutualdestination(self, destination):
    "Set another link as destination, and set its destination to this one."
    self.setdestination(destination)
    destination.setdestination(self)

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
    text = TranslationConfig.lists[self.type]
    self.contents = [TaggedText.constant(text, 'div class="list"', True)]

class TableOfContents(ListInset):
  "Table of contents"

  def process(self):
    "Parse the header and get the type"
    text = TranslationConfig.constants['toc']
    self.contents = [TaggedText().constant(text, 'div class="toc"', True)]

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
    self.setdestination(IndexEntry.entries[key])
    arrow = Link().complete(u'↑', 'index-' + key)
    arrow.setdestination(self)
    IndexEntry.arrows[key].append(arrow)

class PrintIndex(ListInset):
  "Command to print an index"

  def process(self):
    "Create the alphabetic index"
    index = TranslationConfig.constants['index']
    self.contents = [TaggedText().constant(index, 'h1 class="index"'),
        Constant('\n')]
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
    nomenclature = TranslationConfig.constants['nomenclature']
    self.contents = [TaggedText().constant(nomenclature,
      'h1 class="nomenclature"')]
    for key in self.sortdictionary(NomenclatureEntry.entries):
      entry = NomenclatureEntry.entries[key]
      contents = [entry, Constant(entry.symbol + u' ' + entry.description)]
      text = TaggedText().complete(contents, 'div class="Nomenclated"', True)
      self.contents.append(text)

class URL(Link):
  "A clickable URL"

  def process(self):
    "Read URL from parameters"
    name = self.escape(self.parameters['target'])
    if 'type' in self.parameters:
      self.url = self.escape(self.parameters['type']) + name
    else:
      self.url = name
    if 'name' in self.parameters:
      name = self.parameters['name']
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
    if container.type:
      type = container.type
    tag = 'a class="' + type + '"'
    if container.anchor:
      tag += ' name="' + container.anchor + '"'
    if container.url:
      tag += ' href="' + container.url + '"'
    if container.target:
      tag += ' target="' + container.target + '"'
    text = TaggedText().complete(container.contents, tag)
    return text.gethtml()

