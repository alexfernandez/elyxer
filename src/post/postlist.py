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
    if not self.type:
      self.type = item.type

  def adddeeper(self, deeper):
    "Add a deeper list item"
    if self.empty():
      self.insertfake()
    item = self.contents[-1]
    self.contents[-1].contents += deeper.contents

  def generatelist(self):
    "Get the resulting list"
    if not self.type:
      return Group().contents(self.contents)
    tag = TagConfig.listitems[self.type]
    text = TaggedText().complete(self.contents, tag, True)
    self.__init__()
    return text

  def isduewithitem(self, item):
    "Decide whether the pending list must be generated before the given item"
    if not self.type:
      return False
    Trace.debug('List type: ' + self.type + ', item type: ' + item.type)
    if self.type != item.type:
      return True
    return False

  def isdue(self, element):
    "Decide whether the pending list has to be generated with the given item"
    Trace.debug('Deciding to generate pending for ' + unicode(element))
    if isinstance(element, ListItem):
      Trace.debug('List type: ' + self.type + ', element type: ' + element.type)
      if not self.type:
        return False
      if self.type != element.type:
        return True
      return False
    if isinstance(element, DeeperList):
      return False
    return True

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

class PostListItem(object):
  "Postprocess a list item"

  processedclass = ListItem

  def postprocess(self, item, last):
    "Add the item to pending and return an empty item"
    result = BlackBox()
    if not hasattr(self.postprocessor, 'list'):
      self.postprocessor.list = PendingList()
    if self.postprocessor.list.isduewithitem(item):
      Trace.debug('Generating list before ' + unicode(item))
      result = Group().contents([item, self.postprocessor.list.generatelist()])
    Trace.debug('New item ' + unicode(item))
    self.postprocessor.list.additem(item)
    return result

  def generatepending(self, element):
    "Return a pending list"
    Trace.debug('Generate pending')
    list = self.postprocessor.list.generatelist()
    Trace.debug('Returning list ' + unicode(list))
    if not element:
      return list
    return Group().contents([list, element])

class PostDeeperList(object):
  "Postprocess a deeper list"

  processedclass = DeeperList

  def postprocess(self, deeper, last):
    "Return the list in the postprocessor"
    if not hasattr(self.postprocessor, 'list'):
      self.postprocessor.list = PendingList()
    self.postprocessor.list.adddeeper(deeper)
    return deeper

class PostLastItem(PostListItem):
  "Last element was a list item"

  processedclass = ListItem

  def postprocess(self, element, last):
    "If a pending list is due return it"
    if not self.mustgeneratepending(element):
      Trace.debug('Do not generate pending yet')
      return element
    return self.generatepending(element)

class PostLastDeeper(PostLastItem):
  "Last element was a deeper list"

  processedclass = DeeperList

Postprocessor.stages += [PostListItem, PostDeeperList]
Postprocessor.laststages += [PostLastItem] #, PostLastDeeper]

