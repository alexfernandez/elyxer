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


class SideNote(Container):
  "A side note that appears at the right."

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput()

  def process(self):
    "Enclose everything in a marginal span."
    self.output.settag('span class="Marginal"', True)

class Footnote(Container):
  "A footnote to the main text"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="FootOuter"', False)
    if not Options.numberfoot:
      NumberGenerator.generator.getcounter('Footnote').setmode('A')

  def process(self):
    "Add a counter for the footnote."
    "Can be numeric or a letter depending on runtime options."
    order = NumberGenerator.generator.generate('Footnote')
    span = 'span class="FootMarker"'
    marker = TaggedText().constant('[' + order + ']', span)
    tag = TaggedText().complete([marker] + self.contents, 'span class="Foot"', True)
    self.contents = [marker, tag]

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

