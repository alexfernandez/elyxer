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
# Alex 20090415
# eLyXer bibliography

from util.trace import Trace
from parse.parser import *
from io.output import *
from ref.link import *
from post.postprocess import *


class BiblioCite(Container):
  "Cite of a bibliography entry"

  cites = dict()
  generator = NumberGenerator()

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('sup')
    self.contents = []
    self.entries = []

  def process(self):
    "Add a cite to every entry"
    keys = self.parameters['key'].split(',')
    for key in keys:
      number = NumberGenerator.instance.generateunique('bibliocite')
      entry = self.createentry(key, number)
      cite = Link().complete(number, 'cite-' + number, type='bibliocite')
      cite.setmutualdestination(entry)
      self.contents += [cite, Constant(',')]
      if not key in BiblioCite.cites:
        BiblioCite.cites[key] = []
      BiblioCite.cites[key].append(cite)
    if len(keys) > 0:
      # remove trailing ,
      self.contents.pop()

  def createentry(self, key, number):
    "Create the entry with the given key and number."
    entry = Link().complete(number, 'biblio-' + number, type='biblioentry')
    if not key in BiblioEntry.entries:
      BiblioEntry.entries[key] = []
    BiblioEntry.entries[key].append(entry)
    return entry

class Bibliography(Container):
  "A bibliography layout containing an entry"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('p class="biblio"', True)

class BiblioEntry(Container):
  "A bibliography entry"

  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="entry"')

  def process(self):
    "Process the cites for the entry's key"
    self.processcites(self.parameters['key'])

  def processcites(self, key):
    "Get all the cites of the entry"
    self.key = key
    if not key in BiblioEntry.entries:
      self.contents.append(Constant('[-] '))
      return
    entries = BiblioEntry.entries[key]
    self.contents = [Constant('[')]
    for entry in entries:
      self.contents.append(entry)
      self.contents.append(Constant(','))
    self.contents.pop(-1)
    self.contents.append(Constant('] '))

class PostBiblio(object):
  "Insert a Bibliography legend before the first item"

  processedclass = Bibliography

  def postprocess(self, last, element, next):
    "If we have the first bibliography insert a tag"
    if isinstance(last, Bibliography):
      return element
    bibliography = Translator.translate('bibliography')
    header = TaggedText().constant(bibliography, 'h1 class="biblio"')
    layout = StandardLayout().complete([header, element])
    return layout

Postprocessor.stages.append(PostBiblio)

