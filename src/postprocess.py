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
# Alex 20090324
# eLyXer postprocessor code

from container import *
from link import *
from trace import Trace
from structure import *


class Group(Container):
  "A silly group of containers"

  def __init__(self):
    self.output = ContentsOutput()

  def contents(self, contents):
    self.contents = contents
    return self

  def __str__(self):
    return 'Group: ' + str(self.contents)

class PostBiblio(object):
  "Insert a Bibliography legend before the first item"

  processedclass = Bibliography

  def postprocess(self, element, last):
    "If we have the first bibliography insert a tag"
    if isinstance(last, Bibliography):
      return element
    tag = TaggedText().constant('Bibliography', 'h1 class="biblio"')
    return Group().contents([tag, element])

class PostListItem(object):
  "Output a unified list element"

  processedclass = ListItem

  pending = []

  def lastprocess(self, element, last):
    "Add the last list item"
    PostListItem.pending += last.contents
    return self.decidelist(element, last)

  def decidelist(self, element, last):
    "After the last list element return it all"
    if isinstance(element, ListItem) and element.type == last.type:
      Trace.debug('Another ' + last.type + ' pending')
      return element
    elif isinstance(element, DeeperList):
      Trace.debug('Another deeper ' + element.type + ' pending')
      element.output = EmptyOutput()
      return element
    tag = ListItem.typetags[last.type]
    list = TaggedText().complete(PostListItem.pending, tag)
    Trace.debug('Output list with ' + str(len(list.contents)) + ' items')
    PostListItem.pending = []
    return Group().contents([list, element])

  def generate(self):
    "Generate the list"

class PostDeeperList(PostListItem):
  "Add nested lists as list items"

  processedclass = DeeperList

  def lastprocess(self, element, last):
    "Add the last nested list"
    tag = ListItem.typetags[last.type]
    last.output = TaggedOutput().settag(tag, True)
    PostListItem.pending.append(last)
    return self.decidelist(element, last)

class Postprocessor(object):
  "Postprocess an element keeping some context"

  stages = [PostBiblio()]
  laststages = [PostListItem(), PostDeeperList()]

  stagedict = dict([(x.processedclass, x) for x in stages])
  laststagedict = dict([(x.processedclass, x) for x in laststages])

  def __init__(self):
    self.last = None

  def postprocess(self, original):
    "Postprocess an element taking into account the last one"
    element = original
    if element.__class__ in Postprocessor.stagedict:
      stage = Postprocessor.stagedict[element.__class__]
      element = stage.postprocess(element, self.last)
    if self.last and self.last.__class__ in Postprocessor.laststagedict:
      stage = Postprocessor.laststagedict[self.last.__class__]
      element = stage.lastprocess(element, self.last)
    self.last = original
    return element

