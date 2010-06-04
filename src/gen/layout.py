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
from parse.parser import *
from io.output import *
from gen.structure import *
from gen.container import *
from post.postprocess import *
from ref.label import *
from util.numbering import *
from ref.link import *


class Layout(Container):
  "A layout (block of text) inside a lyx file"

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    if self.type in TagConfig.layouts:
      self.output.tag = TagConfig.layouts[self.type] + ' class="' + self.type + '"'
    elif self.type.replace('*', '') in TagConfig.layouts:
      self.output.tag = TagConfig.layouts[self.type.replace('*', '')] + ' class="' +  self.type.replace('*', '-') + '"'
    else:
      self.output.tag = 'div class="' + self.type + '"'
    self.numerate()

  def numerate(self):
    "Numerate if necessary."
    if not LayoutNumberer.instance.isnumbered(self):
      return
    if self.containsappendix():
      self.activateappendix()
    LayoutNumberer.instance.numberlayout(self)

  def containsappendix(self):
    "Find out if there is an appendix somewhere in the layout"
    for element in self.contents:
      if isinstance(element, Appendix):
        return True
    return False
    
  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    NumberGenerator.instance.number = ['-']

  def __unicode__(self):
    return 'Layout of type ' + self.type

class StandardLayout(Layout):
  "A standard layout -- can be a true div or nothing at all"

  indentation = False

  def process(self):
    self.type = 'standard'
    self.output = ContentsOutput()

  def complete(self, contents):
    "Set the contents and return it."
    self.process()
    self.contents = contents
    return self

class Title(Layout):
  "The title of the whole document"

  def process(self):
    self.type = 'title'
    self.output.tag = 'h1 class="title"'
    title = self.extracttext()
    TitleOutput.title = title
    Trace.message('Title: ' + title)

class Author(Layout):
  "The document author"

  def process(self):
    self.type = 'author'
    self.output.tag = 'h2 class="author"'
    author = self.extracttext()
    Trace.debug('Author: ' + author)
    FooterOutput.appendauthor(author)

class Abstract(Layout):
  "A paper abstract"

  def process(self):
    self.type = 'abstract'
    self.output.tag = 'div class="abstract"'
    message = Translator.translate('abstract')
    tagged = TaggedText().constant(message, 'p class="abstract-message"', True)
    self.contents.insert(0, tagged)

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
    if isinstance(container, StringContainer):
      return self.extractfirststring(container)
    if isinstance(container, ERT):
      return [container], False
    if len(container.contents) == 0:
      # empty container
      return [container], False
    first, found = self.extractfirsttuple(container.contents)
    if isinstance(container, TaggedText) and hasattr(container, 'tag'):
      newtag = TaggedText().complete(first, container.tag)
      return [newtag], found
    return first, found

  def extractfirststring(self, container):
    "Extract the first word from a string container"
    string = container.string
    if not ' ' in string:
      return [container], False
    split = string.split(' ', 1)
    container.string = split[1]
    return [Constant(split[0])], True

class Description(FirstWorder):
  "A description layout"

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

  def process(self):
    "Set the first word to bold"
    self.type = 'List'
    self.output.tag = 'div class="List"'
    firstword = self.extractfirstword(self.contents)
    if not firstword:
      return
    first = TaggedText().complete(firstword, 'span class="List-entry"')
    second = TaggedText().complete(self.contents, 'span class="List-contents"')
    self.contents = [first, second]

class PlainLayout(Layout):
  "A plain layout"

  def process(self):
    "Output just as contents."
    self.output = ContentsOutput()
    self.type = 'Plain'

  def makevisible(self):
    "Make the layout visible, output as tagged text."
    self.output = TaggedOutput().settag('div class="PlainVisible"', True)

class LyXCode(Layout):
  "A bit of LyX-Code."

  def process(self):
    "Output as pre."
    self.output.tag = 'pre class="LyX-Code"'
    for newline in self.searchall(Newline):
      index = newline.parent.contents.index(newline)
      newline.parent.contents[index] = Constant('\n')

class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout

  def postprocess(self, last, layout, next):
    "Generate a number and place it before the text"
    if not hasattr(layout, 'number'):
      return layout
    label = Label().create(layout.anchortext, layout.partkey, type='toc')
    layout.contents.insert(0, label)
    if layout.anchortext != '':
      layout.contents.insert(1, Constant(u' '))
    return layout

  def modifylayout(self, layout, type):
    "Modify a layout according to the given type."
    layout.level = NumberGenerator.instance.getlevel(type)
    layout.output.tag = layout.output.tag.replace('?', unicode(layout.level))

  def containsappendix(self, layout):
    "Find out if there is an appendix somewhere in the layout"
    for element in layout.contents:
      if isinstance(element, Appendix):
        return True
    return False

  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    NumberGenerator.instance.number = ['-']

class PostStandard(object):
  "Convert any standard spans in root to divs"

  processedclass = StandardLayout

  def postprocess(self, last, standard, next):
    "Switch to div"
    type = 'Standard'
    if LyXHeader.indentstandard:
      if isinstance(last, StandardLayout):
        type = 'Indented'
      else:
        type = 'Unindented'
    standard.output = TaggedOutput().settag('div class="' + type + '"', True)
    return standard

class PostLyXCode(object):
  "Coalesce contiguous LyX-Code layouts."

  processedclass = LyXCode

  def postprocess(self, last, lyxcode, next):
    "Coalesce if last was also LyXCode"
    if not isinstance(last, LyXCode):
      return lyxcode
    if hasattr(last, 'first'):
      lyxcode.first = last.first
    else:
      lyxcode.first = last
    toappend = lyxcode.first.contents
    toappend.append(Constant('\n'))
    toappend += lyxcode.contents
    lyxcode.output = EmptyOutput()
    return lyxcode

Postprocessor.stages += [PostLayout, PostStandard, PostLyXCode]

