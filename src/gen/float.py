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
# Alex 20090518
# LyX floats

from util.trace import Trace
from util.numbering import *
from parse.parser import *
from io.output import *
from gen.container import *
from gen.structure import *
from gen.layout import *
from ref.label import *


class Float(Container):
  "A floating inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="float"', True)

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    caption = self.searchshallow(Caption)
    if not caption:
      return
    number = NumberGenerator.instance.generatechaptered(self.type)
    prefix = TranslationConfig.floats[self.type]
    caption.contents.insert(0, Constant(prefix + number + u' '))
    label = caption.searchshallow(Label)
    if not label:
      return
    caption.contents.remove(label)
    self.contents.insert(0, label)

class Wrap(Float):
  "A wrapped (floating) float"

  def process(self):
    "Get the wrap type"
    Float.process(self)
    placement = self.parameters['placement']
    self.output.tag = 'div class="wrap-' + placement + '"'

class Caption(Container):
  "A caption for a figure or a table"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="caption"', True)

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
    if not 'lstparams' in self.parameters:
      return
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

