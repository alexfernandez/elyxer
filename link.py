#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090218
# Generate custom HTML version from Lyx document
# Links and nodes

from trace import Trace
from parse import *
from output import *
from container import *


class Link(Container):
  "A link to another part of the document"

  def __init__(self):
    self.contents = list()
    self.destination = None
  
  def complete(self, url, contents):
    self.url = url
    self.output = LinkOutput()
    self.contents = contents

  def geturl(self):
    "Get the URL of the link"
    return self.url

class NodeLink(Link):
  "A link based on a node"

  def complete(self, node):
    self.node = node

  def geturl(self):
    return node.filename + '#' + node.getkey()

  def getcontents(self):
    return node.dashnumber()

class Destination(Container):
  "The destination of a link"

  def __init__(self):
    self.contents = list()
    self.node = None

class Label(Destination):
  "A label to be referenced"

  start = '\\begin_inset LatexCommand label'
  ending = '\\end_inset'

  labels = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = EmptyOutput()

  def process(self):
    self.key = self.parser.key
    Label.labels[self.key] = self
    if self.key in Reference.refs:
      ref = Reference.refs[self.key]
      ref.label = self
      ref.arrow = u'↓'

class Reference(Link):
  "A reference to a label"

  start = '\\begin_inset LatexCommand ref'
  ending = '\\end_inset'

  refs = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = ReferenceOutput()
    self.arrow = '?'

  def process(self):
    self.key = self.parser.key
    if self.key in Label.labels:
      self.label = Label.labels[self.key]
      self.arrow = u'↑'
    Reference.refs[self.key] = self

class BiblioCite(Link):
  "Cite of a bibliography entry"

  start = '\\begin_inset LatexCommand cite'
  ending = '\\end_inset'

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = NamedCommand()
    self.output = BiblioCiteOutput()

  def process(self):
    keys = self.parser.key.split(',')
    self.cites = []
    for key in keys:
      BiblioCite.index += 1
      if not key in BiblioCite.entries:
        BiblioCite.entries[key] = []
      BiblioCite.entries[key].append(BiblioCite.index)
      self.cites.append(str(BiblioCite.index))

class Bibliography(Container):
  "A bibliography layout containing an entry"

  start = '\\begin_layout Bibliography'
  ending = '\\end_layout'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'p class="biblio"'

class BiblioEntry(Destination):
  "A bibliography entry"

  start = '\\begin_inset LatexCommand bibitem'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = NamedCommand()
    self.output = BiblioEntryOutput()

  def process(self):
    "Get all the cites of the entry"
    self.key = self.parser.key
    cites = []
    if self.key in BiblioCite.entries:
      cites = BiblioCite.entries[self.key]
    self.contents = ['[',']']
    for cite in cites:
      link = Link().link(cite.node, Constant(cite.number))
      self.contents.insert(-1, link)
      self.contents.insert(-1, Constant('-1'))
    if len(cites) > 0:
      self.contents.pop(-2)

    html = ['[']
    for cite in container.cites:
      c = str(cite)
      html.append('<a class="biblio" name="' + c + '" href="#back-' + c + '">' + c + '</a>')
      html.append(',')
    if len(html) > 1:
      html.pop()
    html.append('] ')

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

class PrintIndex(object):
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

  def gethtml(self, container):
    "Get the HTML code for the entry"
    html = ['[']
    for cite in container.cites:
      c = str(cite)
      html.append('<a class="biblio" name="' + c + '" href="#back-' + c + '">' + c + '</a>')
      html.append(',')
    if len(html) > 1:
      html.pop()
    html.append('] ')
    return html

class BiblioCiteOutput(object):
  "A bibliographical entry cited"

  def gethtml(self, container):
    "Get the HTML code for the cite"
    html = []
    for cite in container.cites:
      html.append('<a class="cite" name="back-' + cite + '" href="#' +
          cite + '"><sup>[' + cite + ']</sup></a>')
    return html

class ReferenceOutput(object):
  "A reference to a labeled node"

  def gethtml(self, container):
    "Get the HTML code for the reference"
    html = ['<a class="ref" href="']
    link, name = self.getdestination(container)
    html.append(link + '">')
    html.append(name)
    html.append('</a>')
    return html

  def getdestination(self, container):
    "Find the destination for a container"
    link = 'not-found.html'
    name = '?'
    if not hasattr(container, 'node'):
      Trace.error('No node in ' + str(container))
      return link, name
    if not hasattr(container, 'label'):
      #Trace.error('No label in ' + str(container))
      return link, name
    if not hasattr(container.label, 'node'):
      Trace.error('No node in label for ' + str(container))
      return link, name
    origin = container.node
    destination = container.label.node
    Trace.debug('From ' + str(origin) + ' to ' + str(destination))
    link = '#' + container.label.node.getkey()
    name = container.label.node.getnumber()
    if origin.filename == destination.filename:
      return link, self.addarrow(container, name)
    link = destination.filename + link
    return link, self.switcharrow(container, name)

  def addarrow(self, container, name):
    "Name for same destination"
    return name + container.arrow

  def switcharrow(self, container, name):
    "Name with a switched arrow"
    "The arrows switch from ↑ to ← and ↓ to →"
    if container.arrow == u'↑':
      return u'←' + name
    elif container.arrow == u'↓':
      return name + u'→'
    Trace.debug('Error in arrow for ' + str(container))
    return name

class LinkOutput(object):
  "A link pointing to some destination"
  "Or the destination itself"

  def gethtml(self, container):
    "Get the HTML code for the link"
    tag = TagOutput()
    container.tag = 'a class="' + container.__class__.__name__ + '"'
    if hasattr(container, 'anchor'):
      container.tag += ' name="' + container.anchor + '"'
    if hasattr(container, 'url'):
      container.tag += ' href="' + container.url + '"'
    container.breaklines = False
    return tag.gethtml(container)


