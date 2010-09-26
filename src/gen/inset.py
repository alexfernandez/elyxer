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
# Alex 20090506
# LyX insets

from util.trace import Trace
from util.numbering import *
from parse.parser import *
from out.output import *
from io.bulk import *
from gen.container import *
from gen.styles import *
from gen.layout import *
from gen.float import *


class InsetText(Container):
  "An inset of text in a lyx file"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

class Inset(Container):
  "A generic inset in a LyX document"

  def __init__(self):
    self.contents = list()
    self.parser = InsetParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    self.output.tag = 'span class="' + self.type + '"'

  def __unicode__(self):
    return 'Inset of type ' + self.type

class NewlineInset(Newline):
  "A newline or line break in an inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()

class NewPageInset(NewPage):
  "A new page command."

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()

class Branch(Container):
  "A branch within a LyX document"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="branch"', True)

  def process(self):
    "Disable inactive branches"
    self.branch = self.header[2]
    if not self.isactive():
      Trace.debug('Branch ' + self.branch + ' not active')
      self.output = EmptyOutput()

  def isactive(self):
    "Check if the branch is active"
    if not self.branch in Options.branches:
      Trace.error('Invalid branch ' + self.branch)
      return True
    branch = Options.branches[self.branch]
    return branch.isselected()

class ShortTitle(Container):
  "A short title to display (always hidden)"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

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

  order = '-'

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="FootOuter"', False)

  def process(self):
    "Add a letter for the order, rotating"
    if Options.numberfoot:
      letter = NumberGenerator.instance.generateunique('Footnote')
    else:
      Footnote.order = NumberGenerator.instance.increase(Footnote.order)
      letter = Footnote.order
    span = 'span class="FootMarker"'
    marker = TaggedText().constant('[' + letter + ']', span)
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

class FlexInset(Container):
  "A flexible inset, generic version."

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span', False)

  def process(self):
    "Set the correct flex tag."
    self.type = self.header[2]
    if not self.type in TagConfig.flex:
      Trace.error('Unknown Flex inset ' + self.type)
      return
    self.output.settag(TagConfig.flex[self.type], False)

class InfoInset(Container):
  "A LyX Info inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="Info"', False)

  def process(self):
    "Set the shortcut as text"
    self.type = self.parameters['type']
    self.contents = [Constant(self.parameters['arg'])]

class BoxInset(Container):
  "A box inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div', True)

  def process(self):
    "Set the correct tag"
    self.type = self.header[2]
    self.output.settag('div class="' + self.type + '"', True)
    ContainerSize().readparameters(self).addstyle(self)

class IncludeInset(Container):
  "A child document included within another."

  # the converter factory will be set in converter.py
  converterfactory = None
  filename = None

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Include the provided child document"
    self.filename = os.path.join(Options.directory, self.parameters['filename'])
    Trace.debug('Child document: ' + self.filename)
    LstParser().parsecontainer(self)
    if 'LatexCommand' in self.parameters:
      if self.parameters['LatexCommand'] == 'verbatiminput':
        self.readverbatim()
        return
      if self.parameters['LatexCommand'] == 'lstinputlisting':
        self.readlisting()
        return
    olddir = Options.directory
    newdir = os.path.dirname(self.parameters['filename'])
    if newdir != '':
      Trace.debug('Child dir: ' + newdir)
      Options.directory = os.path.join(Options.directory, newdir)
    try:
      try:
        converter = IncludeInset.converterfactory.create(self)
      except:
        Trace.error('Could not read ' + self.filename + ', please check that the file exists and has read permissions.')
        self.contents = []
        return
      converter.convert()
      self.contents = converter.getcontents()
    finally:
      Options.directory = olddir

  def readverbatim(self):
    "Read a verbatim document."
    self.contents = [TaggedText().complete(self.readcontents(), 'pre', True)]

  def readlisting(self):
    "Read a document as a listing."
    listing = Listing()
    listing.contents = self.readcontents()
    listing.parameters = self.parameters
    listing.process()
    self.contents = [listing]

  def readcontents(self):
    "Read the contents of a complete file."
    contents = list()
    lines = BulkFile(self.filename).readall()
    for line in lines:
      contents.append(Constant(line))
    return contents

  def __unicode__(self):
    "Return a printable description."
    if not self.filename:
      return 'Included unnamed file'
    return 'Included "' + self.filename + '"'

