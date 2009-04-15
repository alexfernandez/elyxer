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
# Alex 20090411
# LyX layout and derived classes

from util.trace import Trace
from io.parse import *
from io.output import *
from structure import *
from gen.container import *


class Layout(Container):
  "A layout (block of text) inside a lyx file"

  start = '\\begin_layout'
  ending = '\\end_layout'

  typetags = {
      'Quote':'blockquote', 'Standard':'div', 'Part':'h1',
      'Chapter':'h1', 'Section':'h2', 'Subsection':'h3', 'Subsubsection':'h4',
      'Quotation':'blockquote', 'Center':'div', 'Paragraph':'div',
      'LyX-Code':'pre'
      }

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    if self.type in Layout.typetags:
      self.output.tag = Layout.typetags[self.type] + ' class="' + self.type + '"'
    elif self.type.replace('*', '') in Layout.typetags:
      self.output.tag = Layout.typetags[self.type.replace('*', '')] + ' class="' +  self.type.replace('*', '-') + '"'
    else:
      self.output.tag = 'div class="' + self.type + '"'

  def __str__(self):
    return 'Layout of type ' + self.type

class Title(Layout):
  "The title of the whole document"

  start = '\\begin_layout Title'
  ending = '\\end_layout'

  def process(self):
    self.type = 'title'
    self.output.tag = 'h1 class="title"'
    string = self.searchfor(StringContainer)
    self.title = string.contents[0]
    Trace.message('Title: ' + self.title)

class Author(Layout):
  "The document author"

  start = '\\begin_layout Author'
  ending = '\\end_layout'

  def process(self):
    self.type = 'author'
    self.output.tag = 'h2 class="author"'
    string = self.searchfor(StringContainer)
    FooterOutput.author = string.contents[0]
    Trace.debug('Author: ' + FooterOutput.author)

class FirstWorder(Layout):
  "A layout where the first word is extracted"

  def extractfirstword(self, contents):
    "Extract the first word as a list"
    first, found = self.extractfirsttuple(contents)
    return first

  def extractfirsttuple(self, contents):
    "Extract the first word as a tuple"
    firstcontents = []
    index = 0
    while index < len(contents):
      first, found = self.extractfirstcontainer(contents[index])
      if first:
        firstcontents += first
      if found:
        return firstcontents, True
      else:
        del contents[index]
    return firstcontents, False

  def extractfirstcontainer(self, container):
    "Extract the first word from a string container"
    if len(container.contents) == 0:
      # empty container
      return [container], False
    if isinstance(container, StringContainer):
      return self.extractfirststring(container)
    elif isinstance(container, ERT):
      return [container], False
    if len(container.contents) == 0:
      # empty container
      return None, False
    first, found = self.extractfirsttuple(container.contents)
    if isinstance(container, TaggedText) and hasattr(container, 'tag'):
      newtag = TaggedText().complete(first, container.tag)
      return [newtag], found
    return first, found

  def extractfirststring(self, container):
    "Extract the first word from a string container"
    string = container.contents[0]
    if not ' ' in string:
      return [container], False
    split = string.split(' ', 1)
    container.contents[0] = split[1]
    return [Constant(split[0])], True

class Description(FirstWorder):
  "A description layout"

  start = '\\begin_layout Description'
  ending = '\\end_layout'

  def process(self):
    "Set the first word to bold"
    self.type = 'Description'
    self.output.tag = 'div class="Description"'
    firstword = self.extractfirstword(self.contents)
    if not firstword:
      return
    firstword.append(Constant(u' '))
    tag = 'span class="Description-entry"'
    self.contents.insert(0, TaggedText().complete(firstword, tag))

class List(FirstWorder):
  "A list layout"

  start = '\\begin_layout List'
  ending = '\\end_layout'

  def process(self):
    "Set the first word to bold"
    self.type = 'List'
    self.output.tag = 'div class="List"'
    firstword = self.extractfirstword(self.contents)
    if not firstword:
      return
    tag = 'span class="List-entry"'
    self.contents.insert(0, TaggedText().complete(firstword, tag))

ContainerFactory.types += [
    Layout, Title, Author, Description, List
    ]

