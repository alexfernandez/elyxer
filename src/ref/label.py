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
# Alex 20090218
# eLyXer labels

from util.trace import Trace
from io.parse import *
from io.output import *
from gen.container import *
from gen.styles import *
from util.numbering import *
from ref.link import *


class LabelName(object):
  "The name of a label"

  names = dict()

  def __init__(self, name):
    "Parse the label name"
    self.name = name
    self.type = self.name.split(':')[0]
    self.number = NumberGenerator.instance.generatechaptered(self.type)

  def create(cls, string):
    "Construct the numbering for a label name"
    if not string in LabelName.names:
      name = LabelName(string)
      LabelName.names[string] = name
    return LabelName.names[string]

  create = classmethod(create)

class Label(Container):
  "A label to be referenced"

  starts = ['\\begin_inset LatexCommand label', '\\begin_inset CommandInset label']
  ending = '\\end_inset'
  typelabels = {
      'fig':'Figure ', 'tab':'Table ', 'alg':'Listing '
      }

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    self.anchor = self.parser.parameters['name']
    self.name = LabelName.create(self.anchor)
    text = Label.typelabels[self.name.type] + self.name.number + u' '
    self.contents = [Constant(text)]

class Reference(Link):
  "A reference to a label"

  starts = ['\\begin_inset LatexCommand ref', '\\begin_inset CommandInset ref']
  ending = '\\end_inset'

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()
    self.direction = u'↓'

  def process(self):
    key = self.parser.parameters['reference']
    self.url = '#' + key
    if key in LabelName.names:
      # already seen
      self.direction = u'↑'
    self.contents = [Constant(self.direction)]

ContainerFactory.types += [
    Label, Reference
    ]

