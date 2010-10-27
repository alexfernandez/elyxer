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
from bib.biblio import *


class BibTeX(Container):
  "Show a BibTeX bibliography and all referenced entries"

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Read all bibtex files and process them."
    self.entries = []
    self.contents = [self.createheader()]
    bibliography = Translator.translate('bibliography')
    files = self.getparameterlist('bibfiles')
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

  def createheader(self):
    "Create the header for the bibliography."
    header = BiblioHeader()
    if 'bibtotoc' in self.getparameterlist('options'):
      header.addtotoc(self)
    return header

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
    for option in self.getparameterlist('options'):
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
    for entry in BibEntry.instances:
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

class BibEntry(Container):
  "An entry in a BibTeX file"

  instances = []

  def detect(self, pos):
    "Throw an error."
    Trace.error('Tried to detect() in ' + unicode(self))

  def parse(self, pos):
    "Throw an error."
    Trace.error('Tried to parse() in ' + unicode(self))

  def isreferenced(self):
    "Throw an error."
    Trace.error('Function isreferenced() not implemented for ' + unicode(self))

  def __unicode__(self):
    "Return a string representation"
    return 'BibTeX entry ' + self.__class__.__name__

class CommentEntry(BibEntry):
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

class SpecialEntry(BibEntry):
  "A special entry"

  types = ['@string', '@preamble', '@comment']

  def __init__(self):
    self.contents = []
    self.output = EmptyOutput()

  def detect(self, pos):
    "Detect the special entry"
    for type in SpecialEntry.types:
      if pos.checkforlower(type):
        return True
    return False

  def parse(self, pos):
    "Parse and ignore."
    self.type = 'special'
    while not pos.checkskip('{'):
      pos.skipcurrent()
    pos.pushending('}')
    while not pos.finished():
      if pos.checkfor('{'):
        self.parse(pos)
      else:
        pos.skipcurrent()
    pos.popending()

  def isreferenced(self):
    "A special entry is never referenced"
    return False

  def __unicode__(self):
    "Return a string representation"
    return self.type

# More instances will be added later
BibEntry.instances += [CommentEntry(), SpecialEntry()]

