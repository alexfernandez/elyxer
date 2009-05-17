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
from io.output import *
from gen.container import *
from gen.structure import *
from gen.layout import *


class Float(Container):
  "A floating inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="float"', True)

  def process(self):
    "Get the float type"
    self.debug()
    self.type = self.header[2]
    tagged = TaggedText().complete(self.contents, 'div class="' + self.type + '"')
    self.contents = [tagged]
    caption = self.searchshallow(Caption)
    if caption:
      number = NumberGenerator.instance.generatechaptered(self.type)
      prefix = TranslationConfig.floats[self.type]
      layout = caption.contents[0]
      layout.contents.insert(0, Constant(prefix + number + u' '))

class Wrap(Float):
  "A wrapped (floating) float"

  def process(self):
    "Get the wrap type"
    Float.process(self)
    placement = self.parameters['placement']
    self.output.tag = 'div class="wrap-' + placement + '"'

class InsetText(Container):
  "An inset of text in a lyx file"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

class Caption(Container):
  "A caption for a figure or a table"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="caption"', True)

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

class Branch(Container):
  "A branch within a LyX document"

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

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

class Footnote(Container):
  "A footnote to the main text"

  order = 0
  list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Add a letter for the order, rotating"
    letter = Footnote.list[Footnote.order % len(Footnote.list)]
    span = 'span class="FootMarker"'
    pre = FootnoteConfig.constants['prefrom']
    post = FootnoteConfig.constants['postfrom']
    fromfoot = TaggedText().constant(pre + letter + post, span)
    self.contents.insert(0, fromfoot)
    tag = TaggedText().complete(self.contents, 'span class="Foot"', True)
    pre = FootnoteConfig.constants['preto']
    post = FootnoteConfig.constants['postto']
    tofoot = TaggedText().constant(pre + letter + post, span)
    self.contents = [tofoot, tag]
    Footnote.order += 1

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

class FlexCode(Container):
  "A bit of inset code"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="code"', True)

class InfoInset(Container):
  "A LyX Info inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="Info"', False)

  def process(self):
    "Set the shortcut as text"
    self.type = self.parser.parameters['type']
    if self.type not in ContainerConfig.infoinsets:
      Trace.error('Unknown Info type ' + self.type)
    self.contents = [Constant(self.parser.parameters['arg'])]

class Listing(Container):
  "A code listing"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('code class="listing"', True)
    self.numbered = None
    self.counter = 0

  def process(self):
    "Remove all layouts"
    self.processparams()
    newcontents = []
    for container in self.contents:
      newcontents += self.extract(container)
    self.contents = newcontents

  def processparams(self):
    "Process listing parameteres"
    paramlist = self.parameters['lstparams'].split(',')
    for param in paramlist:
      if not '=' in param:
        Trace.error('Invalid listing parameter ' + param)
      else:
        key, value = param.split('=', 1)
        self.parameters[key] = value
        if key == 'numbers':
          self.numbered = value

  def extract(self, container):
    "Extract the container's contents and return them"
    if isinstance(container, StringContainer):
      return [container]
    if isinstance(container, Layout):
      return self.modifylayout(container.contents)
    Trace.error('Unexpected container ' + container.__class__.__name__ +
        ' in listing')
    return []

  def modifylayout(self, contents):
    "Modify a listing layout contents"
    if len(contents) == 0:
      contents = [Constant(u'​')]
    contents.append(Constant('\n'))
    if self.numbered:
      self.counter += 1
      tag = 'span class="number-' + self.numbered + '"'
      contents.insert(0, TaggedText().constant(unicode(self.counter), tag))
    return contents

class BoxInset(Container):
  "A box inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div', True)

  def process(self):
    "Set the correct tag"
    self.type = self.header[2]
    if not self.type in TagConfig.boxes:
      Trace.error('Uknown box type ' + self.type)
      return
    self.output.settag(TagConfig.boxes[self.type], True)


