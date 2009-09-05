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
# Alex 20090905
# eLyXer BibTeX processing

from util.trace import Trace
from io.output import *
from io.path import *
from io.bulk import *
from ref.link import *
from ref.biblio import *


class BibTeX(Container):
  "Show a BibTeX bibliography and all referenced entries"

  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()
    self.refs = list()

  def process(self):
    "Read all bibtex files and process them"
    bibliography = TranslationConfig.constants['bibliography']
    tag = TaggedText().constant(bibliography, 'h1 class="biblio"')
    self.contents.append(tag)
    files = self.parser.parameters['bibfiles'].split(',')
    for file in files:
      self.refs += self.readbib(file + ".bib")

  def readbib(self, filename):
    "Read a bibtex file"
    bibpath = InputPath(filename)
    bibfile = BulkFile(bibpath.path)
    parsed = list()
    for line in bibfile.readall():
      if not line.startswith('%') and not line.strip() == '':
        parsed.append(line)
    return self.getrefs('\n'.join(parsed))

  def getrefs(self, text):
    "Extract all the references in a piece of text"
    refs = list()
    pos = Position(text)
    whitespace = pos.glob(lambda current: current.isspace())
    return refs

class Fake(Container):
  "A leftover to copy content from"

  def process(self):
    self.contents = list()
    keys = self.parser.parameters['key'].split(',')
    for key in keys:
      BiblioCite.index += 1
      number = unicode(BiblioCite.index)
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

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('p class="biblio"', True)

class BiblioEntry(Container):
  "A bibliography entry"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="entry"')

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

