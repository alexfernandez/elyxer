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
# Alex 20090524
# eLyXer list postprocessing

from gen.container import *
from util.trace import Trace
from gen.structure import *
from gen.layout import *
from gen.inset import *
from ref.link import *
from post.postprocess import *


class PostNestedList(object):
  "Postprocess a nested list"

  processedclass = DeeperList

  def postprocess(self, deeper, last):
    "Run the postprocessor on the nested list"
    postproc = Postprocessor()
    for index, part in enumerate(deeper.contents):
      result = postproc.postprocessroot(part)
      deeper.contents[index] = result
    # one additional item to flush the list
    deeper.contents.append(postproc.postprocessroot(BlackBox()))
    return deeper

class PendingList(object):
  "A pending list"

  def __init__(self):
    self.contents = []
    self.type = None

  def additem(self, item):
    "Add a list item"
    self.contents += item.contents
    self.type = item.type

  def addnested(self, nested):
    "Add a nested list item"
    if self.empty():
      self.insertfake()
    item = self.contents[-1]
    self.contents[-1].contents.append(nested)

  def generatelist(self):
    "Get the resulting list"
    if not self.type:
      return Group().contents(self.contents)
    tag = TagConfig.listitems[self.type]
    return TaggedText().complete(self.contents, tag, True)

  def empty(self):
    return len(self.contents) == 0

  def insertfake(self):
    "Insert a fake item"
    item = TaggedText().constant('', 'li class="nested"', True)
    self.contents = [item]
    self.type = 'Itemize'

  def __unicode__(self):
    result = 'pending ' + unicode(self.type) + ': ['
    for element in self.contents:
      result += unicode(element) + ', '
    if len(self.contents) > 0:
      result = result[:-2]
    return result + ']'

class PostListPending(object):
  "Check if there is a pending list"

  def __init__(self):
    self.pending = PendingList()

  def postprocess(self, element, last):
    "If a list element do not return anything;"
    "otherwise return the whole pending list"
    list = None
    Trace.debug('Element ' + unicode(element) + ' after ' + unicode(last))
    if self.generatepending(element):
      Trace.debug('Generate pending')
      list = self.pending.generatelist()
      self.pending.__init__()
    if isinstance(element, ListItem):
      element = self.processitem(element)
      Trace.debug('New list item')
    elif isinstance(element, DeeperList):
      element = self.processnested(element)
      Trace.debug('New deeper list')
    if not list:
      Trace.debug('No list to return')
      return element
    Trace.debug('Returning list')
    return Group().contents([list, element])

  def processitem(self, item):
    "Process a list item"
    self.pending.additem(item)
    return BlackBox()

  def processnested(self, nested):
    "Process a nested list"
    self.pending.addnested(nested)
    return BlackBox()

  def generatepending(self, element):
    "Decide whether to generate the pending list"
    if self.pending.empty():
      return False
    if isinstance(element, ListItem):
      if not self.pending.type:
        return False
      if self.pending.type != element.type:
        return True
      return False
    if isinstance(element, DeeperList):
      return False
    return True

#Postprocessor.stages += [PostNestedList]
Postprocessor.unconditional += [PostListPending]

