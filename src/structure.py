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
# Alex 20090312
# LyX structure in containers

from trace import Trace
from parse import *
from output import *
from container import *


class LyxHeader(Container):
  "Reads the header, outputs the HTML header"

  start = '\\begin_header'
  ending = '\\end_header'

  def __init__(self):
    self.parser = HeaderParser()
    self.output = HeaderOutput()

  def process(self):
    "Find pdf title"
    if '\\pdf_title' in self.parser.parameters:
      Options.title = self.parser.parameters['\\pdf_title']
      Trace.debug('PDF Title: ' + Options.title)

class LyxFooter(Container):
  "Reads the footer, outputs the HTML footer"

  start = '\\end_body'
  ending = '\\end_document'

  def __init__(self):
    self.parser = BoundedDummy()
    self.output = FooterOutput()

class Float(Container):
  "A floating inset"

  start = '\\begin_inset Float'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    self.tag = 'div class="' + self.type + '"'

class InsetText(Container):
  "An inset of text in a lyx file"

  start = '\\begin_inset Text'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

class Caption(Container):
  "A caption for a figure or a table"

  start = '\\begin_inset Caption'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.tag = 'div class="caption"'
    self.breaklines = True

class Align(Container):
  "Bit of aligned text"

  start = '\\align'
  ending = '\\end_layout'

  def __init__(self):
    self.parser = ExcludingParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.tag = 'div class="' + self.header[1] + '"'

class Layout(Container):
  "A layout (block of text) inside a lyx file"

  start = '\\begin_layout'
  ending = '\\end_layout'

  typetags = { 'Quote':'blockquote', 'Standard':'div',
        'Chapter':'h1', 'Section':'h2', 'Subsection':'h3', 'Subsubsection':'h4',
        'Quotation':'blockquote', 'Center':'div', 'Paragraph':'div',
        'Part':'h1'}

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.numbered = False

  def process(self):
    self.type = self.header[1]
    if False: #self.searchfor(Align):
      align = self.searchfor(Align)
      self.tag = 'div class="' + align.header[1] + '"'
    elif self.type in Layout.typetags:
      self.numbered = True
      self.tag = Layout.typetags[self.type] + ' class="' + self.type + '"'
    elif self.type.replace('*', '') in Layout.typetags:
      self.tag = Layout.typetags[self.type.replace('*', '')] + ' class="' +  self.type.replace('*', '-') + '"'
    else:
      self.tag = 'div class="' + self.type + '"'

  def __str__(self):
    return 'Layout of type ' + self.type

class Title(Layout):
  "The title of the whole document"

  start = '\\begin_layout Title'
  ending = '\\end_layout'

  def process(self):
    self.tag = 'h1 class="title"'
    string = self.searchfor(StringContainer)
    self.title = string.contents[0]
    Trace.message('Title: ' + self.title)

class Author(Layout):
  "The document author"

  start = '\\begin_layout Author'
  ending = '\\end_layout'

  def process(self):
    self.tag = 'h2 class="author"'
    string = self.searchfor(StringContainer)
    FooterOutput.author = string.contents[0]
    Trace.debug('Author: ' + FooterOutput.author)

class Description(Layout):
  "A description layout"

  start = '\\begin_layout Description'
  ending = '\\end_layout'

  def process(self):
    "Set the first word to bold"
    self.tag = 'div class="Description"'
    firstword, found = self.extractfirst(self.contents)
    if not firstword:
      return
    firstword.append(Constant(u' '))
    tag = 'span class="Description-entry"'
    self.contents.insert(0, TaggedText().complete(firstword, tag))

  def extractfirst(self, contents):
    "Extract the first word as a list"
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
    first, found = self.extractfirst(container.contents)
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

class Space(Container):
  "A space of several types"

  start = '\\begin_inset space'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()

  def process(self):
    self.type = self.header[2]
    if self.type not in SpaceConfig.spaces:
      Trace.error('Unknown space type ' + self.type)
      self.html = [' ']
      return
    self.html = [SpaceConfig.spaces[self.type]]

class Inset(Container):
  "A generic inset in a LyX document"

  start = '\\begin_inset'
  ending = '\\end_inset'

  def __init__(self):
    self.contents = list()
    self.parser = InsetParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    self.type = self.header[1]
    self.tag = 'span class="' + self.type + '"'

  def __str__(self):
    return 'Inset of type ' + self.type

class Newline(Container):
  "A newline"

  start = '\\newline'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.html = '<br/>'

class NewlineInset(Newline):
  "A newline or line break in an inset"

  start = '\\begin_inset Newline'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()

class Branch(Container):
  "A branch within a LyX document"

  start = '\\begin_inset Branch'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TagOutput()
    self.breaklines = True

  def process(self):
    "Disable inactive branches"
    self.branch = self.header[2]
    self.tag = 'span class="branch"'
    if not self.isactive():
      self.output = EmptyOutput()

  def isactive(self):
    "Check if the branch is active"
    if not self.branch in Options.branches:
      Trace.error('Invalid branch ' + self.branch)
      return True
    branch = Options.branches[self.branch]
    return branch.selected == 1

class ShortTitle(Container):
  "A short title to display (always hidden)"

  start = '\\begin_inset OptArg'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

class Footnote(Container):
  "A footnote to the main text"

  starts = ['\\begin_inset Foot', '\\begin_inset Marginal']
  ending = '\\end_inset'

  order = 0
  list = 'ABCDEFGHIJKLMNOPQRSTUVW'

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Add a letter for the order, rotating"
    letter = Footnote.list[Footnote.order % len(Footnote.list)]
    span = 'span class="FootMarker"'
    fromfoot = TaggedText().constant(u'[→' + letter + u'] ', span)
    self.contents.insert(0, fromfoot)
    tag = TaggedText().complete(self.contents, 'span class="Foot"', True)
    tofoot = TaggedText().constant(' [' + letter + u'→] ', span)
    self.contents = [tofoot, tag]
    Footnote.order += 1

ContainerFactory.types += [
    LyxHeader, LyxFooter, InsetText, Caption, Inset,
    Align, Layout, Float, Title, Author, Description, Newline, Space,
    NewlineInset, Branch, ShortTitle, Footnote
    ]

