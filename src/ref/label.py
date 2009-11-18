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
from parse.parser import *
from io.output import *
from gen.container import *
from gen.styles import *
from util.numbering import *
from ref.link import *


class Label(Link):
  "A label to be referenced"

  names = dict()

  def process(self):
    "Process a label container."
    key = self.parameters['name']
    self.create(' ', key)

  def create(self, text, key, type = 'label'):
    "Create the label for a given key."
    self.key = key
    self.complete(text, anchor = key, type = type)
    Label.names[key] = self
    if key in Reference.references:
      for reference in Reference.references[key]:
        reference.setdestination(self)
    return self

  def __unicode__(self):
    "Return a printable representation."
    return 'Label ' + self.key

class Reference(Link):
  "A reference to a label"

  references = dict()

  def process(self):
    "Read the reference and set the arrow."
    key = self.parameters['reference']
    if key in Label.names:
      direction = u'↑'
      label = Label.names[key]
    else:
      direction = u'↓'
      label = Label().complete(' ', key, 'preref')
    self.setdestination(label)
    self.contents = [Constant(direction)]
    if not key in Reference.references:
      Reference.references[key] = []
    Reference.references[key].append(self)

