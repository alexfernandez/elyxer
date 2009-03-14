#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

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

  def complete(self, text, anchor, url):
    self.contents = [Constant(text)]
    self.anchor = anchor
    self.url = url
    return self

class Label(Container):
  "A label to be referenced"

  start = '\\begin_inset LatexCommand label'
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

  start = '\\begin_inset LatexCommand ref'
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

  names = {'figure':'figuras', 'table':'tablas', 'algorithm':'listados',
      'tableofcontents':'contenidos'}

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    self.tag = 'div class="list"'
    self.contents = [Constant(u'Índice de ' + ListOf.names[self.type])]

class TableOfContents(ListOf):
  "Table of contents"

  start = '\\begin_inset LatexCommand tableofcontents'

class IndexEntry(Link):
  "An entry in the alphabetical index"

  start = '\\begin_inset LatexCommand index'
  ending = '\\end_inset'

  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = IndexEntryOutput()

  def process(self):
    "Put entry in index"
    self.name = self.parser.parameters['name']
    self.key = self.name.replace(' ', '-')
    if not self.key in IndexEntry.entries:
      # no entry; create
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)

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

class URL(Link):
  "A clickable URL"

  start = '\\begin_inset LatexCommand url'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Read URL from parameters"
    self.url = self.escape(self.parser.parameters['target'])
    self.contents = [Constant(self.url)]

class FlexURL(URL):
  "A flexible URL"

  start = '\\begin_inset Flex URL'
  ending = '\\end_inset'

  def process(self):
    "Read URL from contents"
    text = self.searchfor(StringContainer).contents[0]
    self.url = self.escape(text)
    Trace.debug('Flex URL: ' + self.url)
    self.contents = [Constant(self.url)]

class IndexOutput(object):
  "Returns an index as output"

  def gethtml(self, container):
    "Get the HTML code for the index"
    html = [u'<h1>Índice Alfabético</h1>\n']
    for key in container.keys:
      entries = container.entries[key]
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

class IndexEntryOutput(object):
  "An entry in an index"

  def gethtml(self, container):
    "Get the HTML code for the entry"
    return ['<a class="index" name="' + container.key + '-' + str(container.index) +
        '" href="#' + container.key + u'">↓</a>']

class BiblioEntryOutput(object):
  "An entry in the bibliography"

class BiblioCiteOutput(object):
  "A bibliographical entry cited"

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
    FlexURL]

