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
from gen.float import *
from ref.label import *


class NewfangledChunk(Layout):
  "A chunk of literate programming."

  names = dict()
  firsttime = True

  def process(self):
    "Process the literate chunk."
    self.output.tag = 'div class="chunk"'
    self.type = 'chunk'
    text = self.extracttext()
    parts = text.split(',')
    if len(parts) < 1:
      Trace.error('Not enough parameters in ' + text)
      return
    self.name = parts[0]
    self.number = self.order()
    self.createlinks()
    self.contents = [self.left, self.declaration(), self.right]
    ChunkProcessor.lastchunk = self

  def order(self):
    "Create the order number for the chunk."
    return NumberGenerator.instance.generateunique('chunk')

  def createlinks(self):
    "Create back and forward links."
    self.leftlink = Link().complete(self.number, 'chunk:' + self.number, type='chunk')
    self.left = TaggedText().complete([self.leftlink], 'span class="chunkleft"', False)
    self.right = TaggedText().constant('', 'span class="chunkright"', False)
    if not self.name in NewfangledChunk.names:
      NewfangledChunk.names[self.name] = []
    else:
      last = NewfangledChunk.names[self.name][-1]
      forwardlink = Link().complete(self.number + u'→', 'chunkback:' + last.number, type='chunk')
      backlink = Link().complete(u'←' + last.number + u' ', 'chunkforward:' + self.number, type='chunk')
      forwardlink.setmutualdestination(backlink)
      last.right.contents.append(forwardlink)
      self.right.contents.append(backlink)
    NewfangledChunk.names[self.name].append(self)
    self.origin = self.createorigin()
    if self.name in NewfangledChunkRef.references:
      for ref in NewfangledChunkRef.references[self.name]:
        Trace.debug('Dangling reference: ' + unicode(ref))
        self.linkorigin(ref.origin)

  def createorigin(self):
    "Create a link that points to the chunks' origin."
    link = Link()
    self.linkorigin(link)
    return link

  def linkorigin(self, link):
    "Create a link to the origin."
    start = NewfangledChunk.names[self.name][0]
    link.complete(start.number, type='chunk')
    link.destination = start.leftlink
    link.computedestination()

  def declaration(self):
    "Get the chunk declaration."
    contents = []
    text = u'⟨' + self.name + '[' + unicode(len(NewfangledChunk.names[self.name])) + '] '
    contents.append(Constant(text))
    contents.append(self.origin)
    text = ''
    if NewfangledChunk.firsttime:
      Listing.processor = ChunkProcessor()
      NewfangledChunk.firsttime = False
    text += u'⟩'
    if len(NewfangledChunk.names[self.name]) > 1:
      text += '+'
    text += u'≡'
    contents.append(Constant(text))
    return TaggedText().complete(contents, 'span class="chunkdecl"', True)

class ChunkProcessor(object):
  "A processor for listings that belong to chunks."

  lastchunk = None
  counters = dict()

  def preprocess(self, listing):
    "Preprocess a listing: set the starting counter."
    if not ChunkProcessor.lastchunk:
      return
    name = ChunkProcessor.lastchunk.name
    if not name in ChunkProcessor.counters:
      ChunkProcessor.counters[name] = 0
    listing.counter = ChunkProcessor.counters[name]
    for container in listing.searchall(StringContainer):
      if '<=\\' in container.string:
        start = container.string.index('<=\\') + len('<=\\')
        if '>' in container.string[start:]:
          end = container.string.index('>', start)
          Trace.debug('Piece: ' + container.string[start, end])

  def postprocess(self, listing):
    "Postprocess a listing: store the ending counter for next chunk."
    if not ChunkProcessor.lastchunk:
      return
    ChunkProcessor.counters[ChunkProcessor.lastchunk.name] = listing.counter

class NewfangledChunkRef(Inset):
  "A reference to a chunk."

  references = dict()

  def process(self):
    "Show the reference."
    self.output.tag = 'span class="chunkref"'
    self.ref  = self.extracttext()
    if not self.ref in NewfangledChunkRef.references:
      NewfangledChunkRef.references[self.ref] = []
    NewfangledChunkRef.references[self.ref].append(self)
    if self.ref in NewfangledChunk.names:
      start = NewfangledChunk.names[self.ref][0]
      self.origin = start.createorigin()
    else:
      self.origin = Link()
    self.contents.insert(0, Constant(u'⟨'))
    self.contents.append(Constant(' '))
    self.contents.append(self.origin)
    self.contents.append(Constant(u'⟩'))

  def __unicode__(self):
    "Return a printable representation."
    return 'Reference to chunk ' + self.ref

