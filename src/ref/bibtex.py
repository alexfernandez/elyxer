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
from out.output import *
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
    self.contents = [BiblioHeader()]
    bibliography = Translator.translate('bibliography')
    files = self.getparameter('bibfiles').split(',')
    showall = False
    if self.getparameter('btprint') == 'btPrintAll':
      showall = True
    for file in files:
      bibfile = BibFile(file, showall)
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
      entry.citetemplate = style['cite']
      type = entry.type.lower()
      if type in style:
        entry.template = style[type]
      entry.process()
      self.contents.append(entry)

  def readstyle(self):
    "Read the style from the bibliography options"
    options = self.getparameter('options').split(',')
    for option in options:
      if hasattr(BibStylesConfig, option):
        return getattr(BibStylesConfig, option)
    return BibStylesConfig.default

class BibFile(object):
  "A BibTeX file"

  def __init__(self, filename, showall):
    "Create the BibTeX file"
    self.filename = filename + '.bib'
    self.showall = showall
    self.added = 0
    self.ignored = 0
    self.entries = []

  def parse(self):
    "Parse the BibTeX file and extract all entries."
    try:
      self.parsefile()
    except IOError:
      Trace.error('Error reading ' + self.filename + '; make sure the file exists and can be read.')

  def parsefile(self):
    "Parse the whole file."
    bibpath = InputPath(self.filename)
    if Options.lowmem:
      pos = FilePosition(bibpath.path)
    else:
      bulkfile = BulkFile(bibpath.path)
      text = ''.join(bulkfile.readall())
      pos = TextPosition(text)
    while not pos.finished():
      pos.skipspace()
      if pos.checkskip(','):
        pos.skipspace()
      self.parseentry(pos)

  def parseentry(self, pos):
    "Parse a single entry"
    for entry in Entry.entries:
      if entry.detect(pos):
        newentry = Cloner.clone(entry)
        newentry.parse(pos)
        if self.showall or newentry.isreferenced():
          self.entries.append(newentry)
          self.added += 1
        else:
          self.ignored += 1
        return
    # Skip a single character and show it as an error
    skipped = pos.globincluding('\n').strip()
    Trace.error('Unidentified BibTeX entry, skipped "' + skipped + '"')

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
  replaced = BibTeXConfig.replaced
  replacedinitials = [x[0] for x in BibTeXConfig.replaced]

  def __init__(self):
    self.key = None
    self.tags = dict(BibStylesConfig.defaulttags)
    self.output = TaggedOutput().settag('p class="biblio"', True)

  def parse(self, pos):
    "Parse the entry between {}"
    self.type = self.parseexcluding(pos, self.nameseparators).strip()
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
    "Parse a single tag."
    pos.skipspace()
    piece = self.parseexcluding(pos, self.nameseparators)
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
    if hasattr(self, 'dissect' + name):
      dissector = getattr(self, 'dissect' + name)
      dissector(value)
    if not pos.finished():
      remainder = pos.globexcluding(',')
      self.lineerror('Ignored ' + remainder + ' before comma', pos)

  def parsevalue(self, pos):
    "Parse the value for a tag"
    pos.skipspace()
    if pos.checkfor(','):
      self.lineerror('Unexpected ,', pos)
      return ''
    return self.parserecursive(pos, True)

  def parserecursive(self, pos, initial=False):
    "Parse brackets or quotes recursively."
    contents = ''
    while not pos.finished():
      contents += self.parseexcluding(pos, self.valueseparators)
      if pos.finished():
        return contents
      elif pos.checkfor('{'):
        contents += self.parsebracket(pos)
      elif pos.checkfor('"'):
        contents += self.parsequoted(pos, initial)
      elif pos.checkfor('\\'):
        contents += self.parseescaped(pos)
      elif pos.checkfor('#'):
        contents += self.parsehash(pos, initial)
      else:
        self.lineerror('Unexpected character ' + pos.current(), pos)
        pos.currentskip()
    return contents

  def parseescaped(self, pos):
    "Parse an escaped string \\*."
    if not pos.checkskip('\\'):
      self.lineerror('Not an escaped character', pos)
      return ''
    escaped = '\\'
    if pos.checkskip('{'):
      escaped += pos.currentskip()
      if not pos.checkskip('}'):
        self.lineerror('Weird escaped but unclosed brackets \\{*', pos)
      if not escaped in ContentEntry.escaped:
        self.lineerror('Unknown escaped character ' + escaped, pos)
        return escaped[1:]
      return ContentEntry.escaped[escaped]
    for key in ContentEntry.escaped:
      if pos.checkskip(key[1:]):
        return ContentEntry.escaped[key]
    if pos.current().isalpha():
      alpha = '\\' + pos.globalpha()
      if alpha in FormulaConfig.commands:
        return FormulaConfig.commands[alpha]
      self.lineerror('Unknown escaped command \\' + alpha, pos)
      return ''
    self.lineerror('Unknown escaped string \\' + pos.current(), pos)
    return pos.currentskip()

  def parsebracket(self, pos):
    "Parse a {} bracket"
    if not pos.checkskip('{'):
      self.lineerror('Missing opening { in bracket', pos)
      return ''
    pos.pushending('}')
    bracket = self.parserecursive(pos)
    pos.popending('}')
    return bracket

  def parsequoted(self, pos, initial):
    "Parse a piece of quoted text"
    if not pos.checkskip('"'):
      self.lineerror('Missing opening " in quote', pos)
      return ''
    if not initial:
      return '"'
    pos.pushending('"', True)
    quoted = self.parserecursive(pos)
    pos.popending('"')
    pos.skipspace()
    return quoted

  def parsehash(self, pos, initial):
    "Parse a hash mark #."
    if not pos.checkskip('#'):
      self.lineerror('Missing # in hash', pos)
      return ''
    if not initial:
      return '#'
    pos.skipspace()
    return ''

  def parseexcluding(self, pos, undesired):
    "Parse a piece not structure (including spaces)."
    result = ''
    while not pos.finished():
      if pos.current() in undesired:
        return result
      if pos.current().isspace():
        result += ' '
        pos.skipspace()
      else:
        replaced = self.parsereplaced(pos)
        if replaced:
          result += replaced
        else:
          result += pos.currentskip()
    return result

  def parsereplaced(self, pos):
    "Check for one of the replaced strings."
    if not pos.current() in ContentEntry.replacedinitials:
      return None
    for key in ContentEntry.replaced:
      if pos.checkskip(key):
        return ContentEntry.replaced[key]
    return None

  def dissectauthor(self, authortag):
    "Dissect the author tag into pieces."
    authorsplit = authortag.split(' and ')
    if len(authorsplit) == 0:
      return
    authorlist = []
    for authorname in authorsplit:
      author = BibAuthor().parse(authorname)
      authorlist.append(author)
    initials = ''
    authors = ''
    if len(authorlist) == 1:
      initials = authorlist[0].surname[0:3]
      authors = unicode(authorlist[0])
    else:
      for author in authorlist:
        initials += author.surname[0:1]
        authors += unicode(author) + ', '
      authors = authors[:-2]
    self.tags['surname'] = authorlist[0].surname
    self.tags['Sur'] = initials
    self.tags['authors'] = authors

  def dissectyear(self, yeartag):
    "Dissect the year tag into pieces, looking for 4 digits in a row."
    pos = TextPosition(yeartag)
    while not pos.finished():
      if pos.current().isdigit():
        number = pos.globnumber()
        if len(number) == 4:
          self.tags['YY'] = number[2:]
          return
      else:
        pos.currentskip()

  def dissectfile(self, filetag):
    "Extract the filename from the file tag as ':filename:FORMAT'."
    if not filetag.startswith(':'):
      return
    bits = filetag.split(':')
    if len(bits) != 3:
      return
    self.tags['filename'] = bits[1]
    self.tags['format'] = bits[2]

class BibAuthor(object):
  "A BibTeX individual author."

  def __init__(self):
    self.surname = ''
    self.firstnames = []

  def parse(self, tag):
    "Parse an individual author tag."
    if ',' in tag:
      self.parsecomma(tag)
    else:
      self.parsewithoutcomma(tag)
    return self

  def parsecomma(self, tag):
    "Parse an author with a comma: Python, M."
    bits = tag.split(',')
    if len(bits) > 2:
      Trace.error('Too many commas in ' + tag)
    self.surname = bits[0].strip()
    self.parsefirstnames(bits[1].strip())

  def parsewithoutcomma(self, tag):
    "Parse an author without a comma: M. Python."
    bits = tag.rsplit(None, 1)
    self.surname = bits[-1].strip()
    if len(bits) == 1:
      return
    self.parsefirstnames(bits[0].strip())

  def parsefirstnames(self, firstnames):
    "Parse the first name."
    for firstname in firstnames.split():
      self.firstnames.append(firstname)

  def getinitial(self):
    "Get the main initial for the author."
    if len(self.surname) == 0:
      return ''
    return self.surname[0].toupper()

  def __unicode__(self):
    "Return a printable representation."
    result = ''
    for firstname in self.firstnames:
      result += firstname + ' '
    return result + self.surname

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

Entry.entries += [CommentEntry(), SpecialEntry()]

