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
# Alex 20100201
# LyX literate programming with the newfangle module.

from util.trace import Trace
from util.numbering import *
from gen.container import *
from gen.layout import *
from ref.label import *


class NewfangledChunk(Layout):
  "A chunk of literate programming."

  names = dict()
  firsttime = True

  def process(self):
    "Process the literate chunk."
    self.output.tag = 'div class="chunk"'
    text = self.extracttext()
    parts = text.split(',')
    if len(parts) < 1:
      Trace.error('Not enough parameters in ' + text)
      return
    name = parts[0]
    self.number = self.order()
    self.createlinks(name)
    self.contents = [self.left, self.declaration(name), self.right]

  def order(self):
    "Create the order number for the chunk."
    return NumberGenerator.instance.generateunique('chunk')

  def createlinks(self, name):
    "Create back and forward links."
    self.leftlink = Link().complete(self.number, 'chunk:' + self.number, type='chunk')
    self.left = TaggedText().complete([self.leftlink], 'span class="chunkleft"', False)
    self.right = TaggedText().constant('', 'span class="chunkright"', False)
    if not name in NewfangledChunk.names:
      NewfangledChunk.names[name] = []
      start = self
    else:
      forwardlink = Link().complete(self.number + u'→', 'chunkforward:' + self.number, type='chunk')
      backlink = Link().complete(u'←' + self.number + u' ', 'chunkback:' + self.number, type='chunk')
      forwardlink.setmutualdestination(backlink)
      last = NewfangledChunk.names[name][-1]
      last.right.contents.append(forwardlink)
      self.right.contents.append(backlink)
      start = NewfangledChunk.names[name][0]
    self.origin = Link().complete(start.number, type='chunk')
    self.origin.destination = start.leftlink
    self.origin.computedestination()
    NewfangledChunk.names[name].append(self)

  def declaration(self, name):
    "Get the chunk declaration."
    contents = []
    text = u'⟨' + name + '[' + unicode(len(NewfangledChunk.names[name])) + '] '
    contents.append(Constant(text))
    contents.append(self.origin)
    text = ''
    if NewfangledChunk.firsttime:
      NewfangledChunk.firsttime = False
    else:
      text += ', add to '
    text += u'⟩'
    if len(NewfangledChunk.names[name]) > 1:
      text += '+'
    text += u'≡'
    contents.append(Constant(text))
    return TaggedText().complete(contents, 'span class="chunkdecl"', True)

