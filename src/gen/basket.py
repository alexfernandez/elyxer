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
# Alex 20091101
# eLyXer output baskets
# http://www.nongnu.org/elyxer/


import os.path
from util.options import *
from util.clone import *
from gen.toc import *


class Basket(object):
  "A basket to place a set of containers. Can write them, store them..."

  def setwriter(self, writer):
    self.writer = writer
    return self

class WriterBasket(Basket):
  "A writer of containers. Just writes them out to a writer."

  def write(self, container):
    "Write a container to the line writer."
    self.writer.write(container.gethtml())

  def finish(self):
    "Mark as finished."
    self.writer.close()

class KeeperBasket(Basket):
  "Keeps all containers stored."

  def __init__(self):
    self.contents = []

  def write(self, container):
    "Keep the container."
    self.contents.append(container)

  def finish(self):
    "Finish the basket by flushing to disk."
    self.flush()

  def flush(self):
    "Flush the contents to the writer."
    for container in self.contents:
      self.writer.write(container.gethtml())

class TOCBasket(Basket):
  "A basket to place the TOC of a document."

  def __init__(self):
    self.indenter = Indenter()
    self.maketree = False
    self.tree = []
    self.leaves = dict()

  def setwriter(self, writer):
    Basket.setwriter(self, writer)
    Options.nocopy = True
    self.indenter.setwriter(writer)
    self.writer.write(LyXHeader().gethtml())
    return self

  def write(self, container):
    "Write the table of contents for a container."
    entries = self.translate(container)
    for entry in entries:
      self.writer.write(entry.gethtml())

  def translate(self, container):
    "Return one or more containers for the TOC."
    entry = self.convert(container)
    if not entry:
      return []
    if self.maketree:
      self.placeintree(entry)
    indent = self.indenter.getindent(entry.depth)
    return [indent, entry]

  def convert(self, container):
    "Convert a container to a TOC container."
    if container.__class__ in [LyXHeader, LyXFooter]:
      return TOCEntry().header(container)
    if not hasattr(container, 'entry'):
      return None
    if container.level > LyXHeader.tocdepth:
      return None
    return TOCEntry().create(container)

  def placeintree(self, entry):
    "Place the entry in a tree of entries."
    while len(self.tree) < entry.depth:
      self.tree.append(None)
    if len(self.tree) > entry.depth:
      self.tree = self.tree[:entry.depth - 1]
    stem = self.findstem()
    self.tree.append(entry)
    self.leaves[entry.key] = entry
    if stem:
      stem.child = entry

  def findstem(self):
    "Find the stem where our next element will be inserted."
    for element in self.tree.reverse():
      if element:
        return element
    return None

  def finish(self):
    "Mark as finished."
    self.writer.write(LyXFooter().gethtml())

