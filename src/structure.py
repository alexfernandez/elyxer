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
    self.output = TaggedOutput().settag('div class="float"', True)

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    tag = TaggedText().complete(self.contents, 'div class="' + self.type + '"')
    self.contents = [tag]

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
    self.output = TaggedOutput().settag('div class="caption"', True)

class Align(Container):
  "Bit of aligned text"

  start = '\\align'
  ending = '\\end_layout'

  def __init__(self):
    self.parser = ExcludingParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.output.tag = 'div class="' + self.header[1] + '"'

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
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    self.output.tag = 'span class="' + self.type + '"'

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
    self.output = TaggedOutput().settag('span class="branch"', True)

  def process(self):
    "Disable inactive branches"
    self.branch = self.header[2]
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

class Note(Container):
  "A LyX note of several types"

  start = '\\begin_inset Note'
  ending = '\\end_inset'

  typetags = {'Note':'', 'Comment':'', 'Greyedout':'span class="greyedout"'}

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

  def process(self):
    "Hide note and comment, dim greyed out"
    self.type = self.header[2]
    if Note.typetags[self.type] == '':
      return
    self.output = TaggedOutput().settag(Note.typetags[self.type], True)

class Appendix(Container):
  "An appendix to the main document"

  start = '\\start_of_appendix'

  def __init__(self):
    self.parser = LoneCommand()
    self.output = TaggedOutput().settag('span class="appendix"', True)

class ListItem(Container):
  "An element in a list"

  starts = ['\\begin_layout Enumerate', '\\begin_layout Itemize']
  ending = '\\end_layout'

  def __init__(self):
    "Output should be empty until the postprocessor can group items"
    self.contents = list()
    self.parser = BoundedParser()
    self.output = EmptyOutput()

  typetags = {'Enumerate':'ol', 'Itemize':'ul'}

  def process(self):
    "Set the correct type and contents."
    self.type = self.header[1]
    tag = TaggedText().complete(self.contents, 'li', True)
    self.contents = [tag]

  def __str__(self):
    return self.type + ' item @ ' + str(self.begin)

class DeeperList(Container):
  "A nested list"

  start = '\\begin_deeper'
  ending = '\\end_deeper'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput()

  def process(self):
    "Create the deeper list"
    if len(self.contents) == 0:
      Trace.error('Empty deeper list')
      return

  def __str__(self):
    result = 'deeper list @ ' + str(self.begin) + ': ['
    for element in self.contents:
      result += str(element) + ', '
    return result[:-2] + ']'

ContainerFactory.types += [
    LyxHeader, LyxFooter, InsetText, Caption, Inset, Align, Float, Newline,
    Space, NewlineInset, Branch, ShortTitle, Footnote, Appendix, Note,
    ListItem, DeeperList
    ]

