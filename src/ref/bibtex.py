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
from parse.position import *
from ref.link import *
from ref.biblio import *


class BibTeX(Container):
  "Show a BibTeX bibliography and all referenced entries"

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()
    self.entries = list()

  def process(self):
    "Read all bibtex files and process them"
    bibliography = TranslationConfig.constants['bibliography']
    tag = TaggedText().constant(bibliography, 'h1 class="biblio"')
    self.contents.append(tag)
    files = self.parser.parameters['bibfiles'].split(',')
    for file in files:
      bibfile = BibFile(file)
      self.entries += bibfile.entries

class BibFile(object):
  "A BibTeX file"

  def __init__(self, filename):
    "Create and parse the BibTeX file"
    self.entries = []
    bibpath = InputPath(filename + '.bib')
    bibfile = BulkFile(bibpath.path)
    parsed = list()
    for line in bibfile.readall():
      if not line.startswith('%') and not line.strip() == '':
        parsed.append(line)
    self.parseentries('\n'.join(parsed))

  def parseentries(self, text):
    "Extract all the entries in a piece of text"
    pos = Position(text)
    pos.skipspace()
    while not pos.finished():
      self.parseentry(pos)

  def parseentry(self, pos):
    "Parse a single entry"
    for entry in Entry.entries:
      if entry.detect(pos):
        newentry = entry.clone()
        newentry.parse(pos)
        self.entries.append(newentry)
        return
    self.lineerror(pos, 'Unidentified entry: ')

  def lineerror(self, pos, error):
    "Skip the whole line, and show it as an error"
    pos.checkskip('\n')
    toline = pos.glob(lambda current: current != '\n')
    Trace.error(error + toline)

class Entry(object):
  "An entry in a BibTeX file"

  entries = []
  structure = ['{', ',', '=', '"']
  quotes = ['{', '"', '#']

  def __init__(self):
    self.tags = dict()

  def parse(self, pos):
    "Parse the entry between {}"
    self.type = self.parsepiece(pos, Entry.structure)
    Trace.debug('Entry of type ' + self.type)
    pos.skipspace()
    if not pos.checkskip('{'):
      self.lineerror(pos, 'Entry should start with {: ')
      return
    pos.pushending('}')
    self.parsetags(pos)
    pos.popending('}')
    pos.skipspace()

  def parsetags(self, pos):
    "Parse all tags in the entry"
    pos.skipspace()
    while not pos.finished():
      self.parsetag(pos)
  
  def parsetag(self, pos):
    piece = self.parsepiece(pos, Entry.structure)
    if pos.checkskip(','):
      Trace.debug('Reference: ' + piece + '')
      self.ref = piece
      return
    if pos.checkskip('='):
      piece = piece.lower().strip()
      pos.skipspace()
      value = self.parsequoted(pos)
      Trace.debug('Tag: ' + piece + '->' + value)
      self.tags[piece] = value
      pos.checkskip(',')
      return
    Trace.debug('No more tags: ' + pos.current())

  def parsepiece(self, pos, undesired):
    "Parse a piece not structure"
    return pos.glob(lambda current: not current in undesired)

  def parsequoted(self, pos):
    "Parse a piece of quoted text"
    pos.skipspace()
    if pos.checkfor(','):
      Trace.error('Unexpected ,')
      return ''
    if pos.checkskip('{'):
      pos.pushending('}')
    elif pos.checkskip('"'):
      pos.pushending('"')
    else:
      return self.parsepiece(pos, Entry.quotes)
    quoted = self.parsequoted(pos)
    pos.popending()
    pos.skipspace()
    if pos.checkskip('#'):
      pos.skipspace()
      quoted += self.parsequoted(pos)
    return quoted

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

class SpecialEntry(Entry):
  "A special entry"

  types = ['@STRING', '@PREAMBLE', '@COMMENT']

  def detect(self, pos):
    "Detect the special entry"
    for type in SpecialEntry.types:
      if pos.checkfor(type):
        return True
    return False

class PubEntry(Entry):
  "A publication entry"

  def detect(self, pos):
    "Detect a publication entry"
    return pos.checkfor('@')

Entry.entries += [SpecialEntry(), PubEntry()]

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

