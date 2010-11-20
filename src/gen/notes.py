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
# Alex 20101119
# LyX notes: notes, footnotes and margin notes.

from util.trace import Trace
from util.numbering import *
from parse.parser import *
from out.output import *
from gen.container import *
from ref.link import *


class SideNote(Container):
  "A side note that appears at the right."

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput()

  def process(self):
    "Enclose everything in a marginal span."
    self.output.settag('span class="Marginal"', True)

class Footnote(Container):
  "A footnote to the main text."

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="FootOuter"', False)
    if not Options.numberfoot:
      NumberGenerator.generator.getcounter('Footnote').setmode('A')

  def process(self):
    "Add a counter for the footnote."
    "Can be numeric or a letter depending on runtime options."
    marker = self.createmarker()
    anchor = self.createanchor(marker)
    notecontents = [anchor] + list(self.contents)
    self.contents = [marker]
    if Options.hoverfoot:
      self.contents.append(self.createnote(notecontents, 'span class="HoverFoot"'))
    if Options.marginfoot:
      self.contents.append(self.createnote(notecontents, 'span class="MarginFoot"'))
    if Options.endfoot:
      EndFootnotes.footnotes.append(self.createnote(notecontents, 'div class="EndFoot"'))

  def createnote(self, contents, tag):
    "Create a note with the given contents and HTML tag."
    return TaggedText().complete(contents, tag, True)

  def createmarker(self):
    "Create the marker for a footnote."
    order = NumberGenerator.generator.generate('Footnote')
    text = '[' + order + ']'
    if Options.endfoot:
      contents = [Link().complete(text, 'footmarker-' + order)]
    else:
      contents = [Constant(text)]
    return self.tagmarker(contents, order)

  def createanchor(self, marker):
    "Create the anchor for a footnote marker. Adds a link for end footnotes."
    if not Options.endfoot:
      return marker
    original = marker.contents[0]
    link = Link().complete('[' + marker.order + ']', 'footnote-' + marker.order)
    link.setmutualdestination(original)
    return self.tagmarker([link])

  def tagmarker(self, contents, order=None):
    "Create a footnote marker based on its contents."
    span = 'span class="SupFootMarker"'
    if Options.inlinefoot:
      span = 'span class="InlineFootMarker"'
    tagged = TaggedText().complete(contents, span)
    if order:
      tagged.order = order
    return tagged

class EndFootnotes(Container):
  "The collection of footnotes at the document end."

  footnotes = []

  def __init__(self):
    "Generate all footnotes and a proper header for them all."
    self.output = ContentsOutput()
    header = TaggedText().constant(Translator.translate('footnotes'), 'h1 class="index"')
    self.contents = [header] + self.footnotes

class Note(Container):
  "A LyX note of several types"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

  def process(self):
    "Hide note and comment, dim greyed out"
    self.type = self.header[2]
    if TagConfig.notes[self.type] == '':
      return
    self.output = TaggedOutput().settag(TagConfig.notes[self.type], True)

