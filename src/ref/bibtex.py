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
from util.clone import *
from io.output import *
from io.path import *
from io.bulk import *
from conf.config import *
from parse.position import *
from ref.link import *
from ref.biblio import *


class BibTeX(Container):
  "Show a BibTeX bibliography and all referenced entries"

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Read all bibtex files and process them"
    self.entries = []
    bibliography = Translator.translate('bibliography')
    tag = TaggedText().constant(bibliography, 'h1 class="biblio"', True)
    self.contents.append(tag)
    files = self.parameters['bibfiles'].split(',')
    for file in files:
      bibfile = BibFile(file)
      bibfile.parse()
      self.entries += bibfile.entries
      Trace.message('Parsed ' + unicode(bibfile))
    self.entries.sort(key = unicode)
    self.applystyle()

  def applystyle(self):
    "Read the style and apply it to all entries"
    style = self.readstyle()
    for entry in self.entries:
      entry.template = style['default']
      if entry.type in style:
        entry.template = style[entry.type]
      entry.process()
      self.contents.append(entry)

  def readstyle(self):
    "Read the style from the bibliography options"
    options = self.parameters['options'].split(',')
    for option in options:
      if hasattr(BibStylesConfig, option):
        return getattr(BibStylesConfig, option)
    return BibStylesConfig.default

class BibFile(object):
  "A BibTeX file"

  def __init__(self, filename):
    "Create the BibTeX file"
    self.filename = filename + '.bib'
    self.added = 0
    self.ignored = 0
    self.entries = []

  def parse(self):
    "Parse the BibTeX file and extract all entries."
    bibpath = InputPath(self.filename)
    if Options.lowmem:
      pos = FilePosition(bibpath.path)
    else:
      bulkfile = BulkFile(bibpath.path)
      text = ''.join(bulkfile.readall())
      pos = TextPosition(text)
    while not pos.finished():
      pos.skipspace()
      self.parseentry(pos)

  def parseentry(self, pos):
    "Parse a single entry"
    for entry in Entry.entries:
      if entry.detect(pos):
        newentry = Cloner.clone(entry)
        newentry.parse(pos)
        if newentry.isreferenced():
          self.entries.append(newentry)
          self.added += 1
        else:
          self.ignored += 1
        return
    # Skip the whole line, and show it as an error
    pos.checkskip('\n')
    Entry.entries[0].lineerror('Unidentified entry', pos)

  def __unicode__(self):
    "String representation"
    string = self.filename + ': ' + unicode(self.added) + ' entries added, '
    string += unicode(self.ignored) + ' entries ignored'
    return string

class Entry(Container):
  "An entry in a BibTeX file"

  entries = []

  def lineerror(self, message, pos):
    "Show an error message for a line."
    Trace.error(message + ': ' + pos.identifier())
    pos.globincluding('\n')

class CommentEntry(Entry):
  "A simple comment."

  def detect(self, pos):
    "Detect the special entry"
    return pos.checkfor('%')

  def parse(self, pos):
    "Parse all consecutive comment lines."
    while pos.checkfor('%'):
      pos.globincluding('\n')

  def isreferenced(self):
    "A comment entry is never referenced"
    return False

  def __unicode__(self):
    "Return a string representation"
    return 'Comment'

class ContentEntry(Entry):
  "An entry holding some content."

  nameseparators = ['{', '=', '"', '#']
  valueseparators = ['{', '"', '#', '\\', '}']
  escaped = BibTeXConfig.escaped

  def __init__(self):
    self.key = None
    self.tags = dict()
    self.output = TaggedOutput().settag('p class="biblio"', True)

  def parse(self, pos):
    "Parse the entry between {}"
    self.type = self.parsepiece(pos, self.nameseparators)
    pos.skipspace()
    if not pos.checkskip('{'):
      self.lineerror('Entry should start with {', pos)
      return
    pos.pushending('}')
    self.parsetags(pos)
    pos.popending('}')
    pos.skipspace()

  def parsetags(self, pos):
    "Parse all tags in the entry"
    pos.skipspace()
    while not pos.finished():
      if pos.checkskip('{'):
        self.lineerror('Unmatched {', pos)
        return
      pos.pushending(',', True)
      self.parsetag(pos)
      if pos.checkfor(','):
        pos.popending(',')
  
  def parsetag(self, pos):
    piece = self.parsepiece(pos, self.nameseparators)
    if pos.finished():
      self.key = piece
      return
    if not pos.checkskip('='):
      self.lineerror('Undesired character in tag name ' + piece, pos)
      return
    name = piece.lower().strip()
    pos.skipspace()
    value = self.parsevalue(pos)
    self.tags[name] = value
    if not pos.finished():
      remainder = pos.globexcluding(',')
      self.lineerror('Ignored ' + remainder + ' before comma', pos)

  def parsevalue(self, pos):
    "Parse the value for a tag"
    pos.skipspace()
    if pos.checkfor(','):
      self.lineerror('Unexpected ,', pos)
      return ''
    value = self.parserecursive(pos)
    if not '\\' in value:
      return value
    for escape in self.escaped:
      if escape in value:
        value = value.replace(escape, self.escaped[escape])
    return value

  def parserecursive(self, pos):
    "Parse brackets or quotes recursively."
    contents = ''
    while not pos.finished():
      contents += self.parsepiece(pos, self.valueseparators)
      if pos.finished():
        return contents
      if pos.checkfor('{'):
        contents += self.parsebracket(pos)
      elif pos.checkfor('"'):
        contents += self.parsequoted(pos)
      elif pos.checkfor('\\'):
        contents += self.parseescaped(pos)
      elif pos.checkskip('#'):
        pos.skipspace()
      else:
        self.lineerror('Unexpected character ' + pos.current(), pos)
        pos.currentskip()
    return contents

  def parseescaped(self, pos):
    "Parse an escaped character \\*."
    if not pos.checkskip('\\'):
      self.lineerror('Not an escaped character', pos)
      return ''
    if not pos.checkskip('{'):
      return '\\' + pos.currentskip()
    current = pos.currentskip()
    if not pos.checkskip('}'):
      self.lineerror('Weird escaped but unclosed brackets \\{*', pos)
    return '\\' + current

  def parsebracket(self, pos):
    "Parse a {} bracket"
    if not pos.checkskip('{'):
      self.lineerror('Missing opening { in bracket', pos)
      return ''
    pos.pushending('}')
    bracket = self.parserecursive(pos)
    pos.popending('}')
    return bracket

  def parsequoted(self, pos):
    "Parse a piece of quoted text"
    if not pos.checkskip('"'):
      self.lineerror('Missing opening " in quote', pos)
      return ''
    pos.pushending('"', True)
    quoted = self.parserecursive(pos)
    pos.popending('"')
    pos.skipspace()
    return quoted

  def parsepiece(self, pos, undesired):
    "Parse a piece not structure."
    return pos.glob(lambda current: not current in undesired)

class SpecialEntry(ContentEntry):
  "A special entry"

  types = ['@STRING', '@PREAMBLE', '@COMMENT']

  def detect(self, pos):
    "Detect the special entry"
    for type in SpecialEntry.types:
      if pos.checkfor(type):
        return True
    return False

  def isreferenced(self):
    "A special entry is never referenced"
    return False

  def __unicode__(self):
    "Return a string representation"
    return self.type

class PubEntry(ContentEntry):
  "A publication entry"

  def detect(self, pos):
    "Detect a publication entry"
    return pos.checkfor('@')

  def isreferenced(self):
    "Check if the entry is referenced"
    if not self.key:
      return False
    return self.key in BiblioEntry.entries

  def process(self):
    "Process the entry"
    biblio = BiblioEntry()
    biblio.processcites(self.key)
    self.contents = [biblio, Constant(' ')]
    self.contents.append(self.getcontents())

  def getcontents(self):
    "Get the contents as a constant"
    contents = self.template
    while contents.find('$') >= 0:
      tag = self.extracttag(contents)
      value = self.gettag(tag)
      contents = contents.replace('$' + tag, value)
    return Constant(contents)

  def extracttag(self, string):
    "Extract the first tag in the form $tag"
    pos = TextPosition(string)
    pos.globexcluding('$')
    pos.skip('$')
    return pos.globalpha()

  def __unicode__(self):
    "Return a string representation"
    string = ''
    author = self.gettag('author')
    if author:
      string += author + ': '
    title = self.gettag('title')
    if title:
      string += '"' + title + '"'
    return string

  def gettag(self, key):
    "Get a tag with the given key"
    if not key in self.tags:
      return ''
    return self.tags[key]

Entry.entries += [CommentEntry(), SpecialEntry(), PubEntry()]

