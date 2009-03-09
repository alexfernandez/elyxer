#!/usr/bin/python
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


class Link(Container):
  "A link to another part of the document"

  def __init__(self):
    self.contents = list()
    self.output = LinkOutput()

  def complete(self, anchor, url):
    self.anchor = anchor
    self.url = url
    return self

class Label(Link):
  "A label to be referenced"

  start = '\\begin_inset LatexCommand label'
  ending = '\\end_inset'

  labels = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = LinkOutput()
    self.contents = [Constant(' ')]

  def process(self):
    self.key = self.parser.key
    Label.labels[self.key] = self
    if self.key in Reference.refs:
      ref = Reference.refs[self.key]
      ref.label = self
      ref.direction = 'down'

class Reference(Link):
  "A reference to a label"

  start = '\\begin_inset LatexCommand ref'
  ending = '\\end_inset'

  refs = dict()

  arrows = {'up':u'↑', 'down':u'↓'}

  def __init__(self):
    self.parser = NamedCommand()
    self.output = LinkOutput()
    self.direction = None

  def process(self):
    self.key = self.parser.key
    if self.key in Label.labels:
      self.label = Label.labels[self.key]
      self.direction = 'up'
    Reference.refs[self.key] = self

  def gethtml(self):
    "Get the HTML code for the reference"
    if not hasattr(self, 'label'):
      #Trace.error('No label in ' + str(self))
      return ['?']
    self.destination = self.label.key
    self.contents = [Constant(self.gettext())]
    return self.output.gethtml(self)

  def gettext(self):
    "Get the inside text with the arrow"
    text = self.destination
    if not self.direction in Reference.arrows:
      Trace.error('Unknown direction ' + self.direction)
      return text + '?'
    return text + Reference.arrows[self.direction]

  def samepage(self):
    "Find out if destination is in our page"
    return (self.origin.filename == self.destination.filename)

class BiblioCite(Container):
  "Cite of a bibliography entry"

  start = '\\begin_inset LatexCommand cite'
  ending = '\\end_inset'

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = TagOutput()
    self.tag = 'sup'
    self.breaklines = False
    self.contents = list()

  def process(self):
    "Add a cite to every entry"
    keys = self.parser.key.split(',')
    for key in keys:
      BiblioCite.index += 1
      if not key in BiblioCite.entries:
        BiblioCite.entries[key] = []
      link = Link()
      link.index = BiblioCite.index
      link.contents = [Constant(str(link.index))]
      self.contents.append(link)
      BiblioCite.entries[key].append(link)

class Bibliography(Container):
  "A bibliography layout containing an entry"

  start = '\\begin_layout Bibliography'
  ending = '\\end_layout'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'p class="biblio"'

class BiblioEntry(Link):
  "A bibliography entry"

  start = '\\begin_inset LatexCommand bibitem'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = TagOutput()
    self.tag = 'span class="entry"'
    self.breaklines = False
    self.cites = list()

  def process(self):
    "Get all the cites of the entry"
    self.key = self.parser.key
    if self.key in BiblioCite.entries:
      self.cites = BiblioCite.entries[self.key]

  def gethtml(self):
    "Get the HTML code for the entry"
    self.contents = [Constant('[')]
    for cite in self.cites:
      link = Link().complete(str(cite.index), str(cite.index))
      self.contents.append(link)
      self.contents.append(Constant(','))
    if len(self.cites) > 0:
      self.contents.pop(-1)
    self.contents.append(Constant(']'))
    return self.output.gethtml(self)

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
    self.parser = NamedCommand()
    self.output = LinkOutput()

  def process(self):
    self.url = self.escape(self.parser.name)
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

