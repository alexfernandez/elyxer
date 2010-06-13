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
# Alex 20100606
# eLyXer BibTeX publication entries.

from util.trace import Trace
from io.output import *
from conf.config import *
from parse.position import *
from ref.link import *
from ref.bibtex import *


class PubEntry(ContentEntry):
  "A publication entry"

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
    self.tags['index'] = self.index
    biblio = BiblioEntry()
    biblio.citeref = self.createref()
    biblio.processcites(self.key)
    self.contents = [biblio, Constant(' ')]
    self.contents += self.entrycontents()

  def entrycontents(self):
    "Get the contents of the entry."
    return self.translatetemplate(self.template)

  def createref(self):
    "Create the reference to cite."
    return self.translatetemplate(self.citetemplate)

  def translatetemplate(self, template):
    "Translate a complete template into a list of contents."
    pos = TextPosition(template)
    part = self.parsepart(pos)
    for variable in part.searchall(BibVariable):
      if variable.empty():
        Trace.error('Error parsing BibTeX template for ' + unicode(self) + ': '
            + unicode(variable) + ' is empty')
    return [part]

  def parsepart(self, pos):
    "Parse a part of a template, return a list of contents."
    part = BibPart()
    while not pos.finished():
      part.add(self.parsepiece(pos))
    return part

  def parsepiece(self, pos):
    "Get the next piece of the template, return if it was empty."
    if pos.checkfor('{'):
      return self.parsebraces(pos)
    elif pos.checkfor('$'):
      return self.parsevariable(pos)
    else:
      return Constant(self.parseexcluding(pos, ['{', '$']))

  def parsebraces(self, pos):
    "Parse a pair of curly braces {}."
    if not pos.checkskip('{'):
      Trace.error('Missing { in braces.')
      return None
    pos.pushending('}')
    part = self.parsepart(pos)
    pos.popending('}')
    empty = self.emptyvariables(part)
    if empty:
      return None
    return part

  def parsevariable(self, pos):
    "Parse a variable $name."
    variable = BibVariable().parse(pos)
    variable.processtags(self.tags)
    return variable

  def emptyvariables(self, part):
    "Find out if there are only empty variables in the part."
    for variable in part.searchall(BibVariable):
      if not variable.empty():
        return False
    return True

  def __unicode__(self):
    "Return a string representation"
    string = ''
    if 'author' in self.tags:
      string += self.tags['author'] + ': '
    if 'title' in self.tags:
      string += '"' + self.tags['title'] + '"'
    return string

class BibPart(Container):
  "A part of a BibTeX template."

  def __init__(self):
    self.output = ContentsOutput()
    self.contents = []

  def add(self, piece):
    "Add a new piece to the current part."
    if not piece:
      return
    if self.redundantdot(piece):
      # remove extra dot
      piece.string = piece.string[1:]
    self.contents.append(piece)
    piece.parent = self

  def redundantdot(self, piece):
    "Find out if there is a redundant dot in the next piece."
    if not isinstance(piece, Constant):
      return False
    if not piece.string.startswith('.'):
      return False
    if len(self.contents) == 0:
      return False
    if not isinstance(self.contents[-1], BibVariable):
      return False
    if not self.contents[-1].extracttext().endswith('.'):
      return False
    return True

class BibVariable(Container):
  "A variable in a BibTeX template."

  escaped = BibTeXConfig.escaped
  
  def __init__(self):
    self.output = TaggedOutput()
    self.contents = []

  def parse(self, pos):
    "Parse the variable name."
    if not pos.checkskip('$'):
      Trace.error('Missing $ in variable name.')
      return self
    self.key = pos.globalpha()
    self.output.tag = 'bib-' + self.key
    return self

  def processtags(self, tags):
    "Find the tag with the appropriate key in the list of tags."
    if not self.key in tags:
      return
    result = self.escapestring(tags[self.key])
    self.contents = [Constant(result)]

  def empty(self):
    "Find out if the variable is empty."
    if not self.contents:
      return True
    if self.extracttext() == '':
      return True
    return False

  def escapestring(self, string):
    "Escape a string."
    for escape in self.escaped:
      if escape in string:
        string = string.replace(escape, self.escaped[escape])
    return string.strip()

  def __unicode__(self):
    "Return a printable representation."
    result = 'variable ' + self.key
    if not self.empty():
      result += ':' + self.gettext()
    return result

Entry.entries += [PubEntry()]

