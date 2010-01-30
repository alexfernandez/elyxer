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

  def create(self, text, key, type = 'Label'):
    "Create the label for a given key."
    self.key = key
    self.complete(text, anchor = key, type = type)
    Label.names[key] = self
    if key in Reference.references:
      for reference in Reference.references[key]:
        reference.destination = self
    return self

  def labelnumber(self):
    "Get the number for the latest numbered container seen."
    numbered = self.numbered(self)
    if numbered and numbered.number:
      return numbered.number
    return ''

  def numbered(self, container):
    "Get the numbered container for the label."
    if hasattr(container, 'number'):
      return container
    if not hasattr(container, 'parent'):
      if hasattr(self, 'lastnumbered'):
        return self.lastnumbered
      return None
    return self.numbered(container.parent)

  def __unicode__(self):
    "Return a printable representation."
    if not hasattr(self, 'key'):
      return 'Unnamed label'
    return 'Label ' + self.key

class Reference(Link):
  "A reference to a label."

  references = dict()
  formats = {
      'ref':u'@↕', 'eqref':u'(@↕)', 'pageref':u'#↕',
      'vref':u'@on-page↕'
      }

  def process(self):
    "Read the reference and set the arrow."
    self.key = self.parameters['reference']
    if self.key in Label.names:
      self.direction = u'↑'
      label = Label.names[self.key]
    else:
      self.direction = u'↓'
      label = Label().complete(' ', self.key, 'preref')
    self.destination = label
    self.format()
    if not self.key in Reference.references:
      Reference.references[self.key] = []
    Reference.references[self.key].append(self)

  def format(self):
    "Format the reference contents."
    formatkey = self.parameters['LatexCommand']
    if not formatkey in self.formats:
      Trace.error('Unknown reference format ' + formatkey)
      formatstring = u'↕'
    else:
      formatstring = self.formats[formatkey]
    formatstring = formatstring.replace(u'↕', self.direction)
    formatstring = formatstring.replace('@', self.destination.labelnumber())
    formatstring = formatstring.replace('#', '1')
    formatstring = formatstring.replace('on-page', Translator.translate('on-page'))
    self.contents = [Constant(formatstring)]

  def __unicode__(self):
    "Return a printable representation."
    return 'Reference ' + self.key

