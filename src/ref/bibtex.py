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
      type = entry.type.lower()
      if type in style:
        entry.template = style[type]
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

  def __init__(self):
    self.key = None
    self.tags = dict()
    self.output = TaggedOutput().settag('p class="biblio"', True)

  def parse(self, pos):
    "Parse the entry between {}"
    self.type = self.parseexcluding(pos, self.nameseparators)
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
      if pos.checkfor('{'):
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

  escaped = BibTeXConfig.escaped

  def detect(self, pos):
    "Detect a publication entry"
    return pos.checkfor('@')

  def isreferenced(self):
    "Check if the entry is referenced"
    if not self.key:
      return False
    return self.key in BiblioReference.references

  def process(self):
    "Process the entry"
    self.index = NumberGenerator.instance.generateunique('pubentry')
    biblio = BiblioEntry()
    biblio.processcites(self.key)
    self.contents = [biblio, Constant(' ')]
    self.contents.append(self.getcontents())

  def getcontents(self):
    "Get the contents as a constant"
    pos = TextPosition(self.template)
    result = self.parsepart(pos)
    return Constant(self.escapeentry(result))

  def parsepart(self, pos):
    "Parse a part of a template, return a tuple consisting of:"
    "The resulting string, and if it contained non-empty variables."
    result = ''
    globalempty = True
    while not pos.finished():
      piece, empty = self.parsepiece(pos)
      if piece:
        result += piece
      if not empty:
        globalempty = False
    return result, globalempty

  def parsepiece(self, pos):
    "Get the next piece of the template, return if it was empty."
    if pos.checkfor('{'):
      return self.parsebraces(pos)
    elif pos.checkfor('$'):
      return self.parsevariable(pos)
    else:
      return self.parseexcluding(pos, ['{', '$']), True

  def parsebraces(self, pos):
    "Parse a pair of curly braces {}."
    if not pos.checkskip('{'):
      Trace.error('Missing { in braces.')
      return None, True
    pos.pushending('}')
    return self.parsepart(pos)

  def parsevariable(self, pos):
    "Parse a variable $name."
    if not pos.checkskip('$'):
      Trace.error('Missing $ in variable name.')
      return None, True
    variable = pos.globalpha()
    value = self.gettag(variable)
    if not value:
      return None, True
    return value, False

  def replacevariable(self, string):
    "Replace a variable with its value."
    tag = self.extracttag(string)
    value = self.gettag(tag)
    dollar = string.find('$' + tag)
    begin = string.rfind('{', 0, dollar)
    end = string.find('}', dollar)
    if begin != -1 and end != -1 and begin < end:
      bracket = string[begin + 1:end]
      if not value:
        result = ''
      else:
        result = bracket.replace('$' + tag, value)
      return string[0:begin] + result + string[end + 1:]
    if not value:
      value = ''
    return string.replace('$' + tag, value)

  def extracttag(self, string):
    "Extract the first tag in the form $tag"
    result = ''
    index = string.index('$') + 1
    while string[index].isalpha():
      result += string[index]
      index += 1
    return result

  def gettag(self, key):
    "Get a tag with the given key"
    if not key in self.tags:
      return None
    return self.tags[key]

  def escapeentry(self, string):
    "Escape a string."
    for escape in self.escaped:
      if escape in string:
        string = string.replace(escape, self.escaped[escape])
    return string

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

Entry.entries += [CommentEntry(), SpecialEntry(), PubEntry()]

