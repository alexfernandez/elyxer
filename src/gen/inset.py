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
from parse.headerparse import *
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
    self.type = self.getparameter('type')
    self.contents = [Constant(self.getparameter('arg'))]

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
    self.filename = os.path.join(Options.directory, self.getparameter('filename'))
    Trace.debug('Child document: ' + self.filename)
    LstParser().parsecontainer(self)
    command = self.getparameter('LatexCommand')
    if command == 'verbatiminput':
      self.readverbatim()
      return
    elif command == 'lstinputlisting':
      self.readlisting()
      return
    self.processinclude()

  def processinclude(self):
    "Process a regular include: standard child document."
    self.contents = []
    olddir = Options.directory
    newdir = os.path.dirname(self.getparameter('filename'))
    if newdir != '':
      Trace.debug('Child dir: ' + newdir)
      Options.directory = os.path.join(Options.directory, newdir)
    try:
      self.convertinclude()
    finally:
      Options.directory = olddir

  def convertinclude(self):
    "Convert an included document."
    try:
      converter = IncludeInset.converterfactory.create(self)
    except:
      Trace.error('Could not read ' + self.filename + ', please check that the file exists and has read permissions.')
      return
    if self.hasemptyoutput():
      return
    converter.convert()
    self.contents = converter.getcontents()

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

