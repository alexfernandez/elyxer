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


class PendingList(object):
  "A pending list"

  def __init__(self):
    self.contents = []
    self.type = None

  def additem(self, item):
    "Add a list item"
    self.contents += item.contents
    self.type = item.type

  def adddeeper(self, deeper):
    "Add a deeper list item"
    if self.empty():
      self.insertfake()
    item = self.contents[-1]
    self.contents[-1].contents.append(deeper)

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

class PostDeeperList(object):
  "Postprocess a deeper list"

  processedclass = DeeperList

  def postprocess(self, deeper, last):
    "Return the list in the postprocessor"
    if not hasattr(self.stages, 'list'):
      self.stages.list = PendingList()
    self.stages.list.adddeeper(deeper)
    Trace.debug('New deeper list: ' + unicode(deeper.postprocessor.stages.list))
    return deeper

class PostListItem(object):
  "Postprocess a list item"

  processedclass = ListItem

  def postprocess(self, item, last):
    "Add the item to pending and return an empty item"
    if not hasattr(self.stages, 'list'):
      self.stages.list = Pending()
    self.stages.list.additem(item)
    Trace.debug('New list item' + unicode(item))
    return BlackBox()

class PostListPending(object):
  "Check if there is a pending list"

  def postprocess(self, element, last):
    "If a list element do not return anything;"
    "otherwise return the whole pending list"
    list = None
    if not self.generatepending(element):
      return element
    Trace.debug('Generate pending')
    list = self.stages.list.generatelist()
    self.stages.list = PendingList()
    Trace.debug('Returning list')
    return Group().contents([list, element])

  def generatepending(self, element):
    "Decide whether to generate the pending list"
    if not hasattr(self.stages, 'list') or self.stages.list.empty():
      return False
    if isinstance(element, ListItem):
      if not self.stages.list.type:
        return False
      if self.stages.list.type != element.type:
        return True
      return False
    if isinstance(element, DeeperList):
      return False
    return True

Postprocessor.stages += [PostDeeperList]
Postprocessor.unconditional += [PostListPending]

