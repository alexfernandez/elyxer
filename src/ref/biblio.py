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
# eLyXer bibliography

from util.trace import Trace
from io.parse import *
from io.output import *
from ref.link import *


class BiblioCite(Container):
  "Cite of a bibliography entry"

  starts = ['\\begin_inset LatexCommand cite', '\\begin_inset CommandInset citation']
  ending = '\\end_inset'

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('sup')

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
    self.output = TaggedOutput().settag('p class="biblio"', True)

class BiblioEntry(Container):
  "A bibliography entry"

  starts = ['\\begin_inset LatexCommand bibitem', '\\begin_inset CommandInset bibitem']
  ending = '\\end_inset'

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

ContainerFactory.types += [
    BiblioCite, Bibliography, BiblioEntry
    ]

