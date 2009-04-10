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

class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout

  ordered = ['Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph']
  unique = ['Part', 'Book']

  def __init__(self):
    self.startinglevel = 0
    self.number = []
    self.uniques = dict()

  def postprocess(self, element, last):
    "Generate a number and place it before the text"
    if element.type in PostLayout.unique:
      level = PostLayout.unique.index(element.type)
      number = self.generateunique(element.type)
    elif element.type in PostLayout.ordered:
      level = PostLayout.ordered.index(element.type)
      number = self.generate(level)
    else:
      return element
    element.contents.insert(0, Constant(number + u' '))
    return element

  def generateunique(self, type):
    "Generate a number to place in the title but not to append to others"
    if not type in PostLayout.unique:
      self.uniques[type] = 0
    self.uniques[type] += 1
    return type + ' ' + self.uniques[type] + '.'

  def generate(self, level):
    "Generate a number in the given level"
    if self.number == [] and level == 1:
      # starting at level 1
      self.startinglevel = 1
    level -= self.startinglevel
    if len(self.number) > level:
      self.number = self.number[:level + 1]
    else:
      while len(self.number) <= level:
        self.number.append(0)
    self.number[level] += 1
    return self.dotseparated()

  def dotseparated(self):
    "Get the number separated by dots: 1.1.3"
    dotsep = ''
    if len(self.number) == 0:
      Trace.error('Empty number')
      return '.'
    for number in self.number:
      dotsep += '.' + str(number)
    return dotsep[1:]

class PendingList(object):
  "A pending list"

  def __init__(self):
    self.contents = []
    self.type = None

  def additem(self, item):
    "Add a list item"
    self.contents += item.contents
    self.type = item.type

  def getlist(self):
    "Get the resulting list"
    tag = ListItem.typetags[self.type]
    return TaggedText().complete(self.contents, tag)

class PostListItem(object):
  "Output a unified list element"

  processedclass = ListItem

  def __init__(self, pending):
    self.pending = pending

  def lastprocess(self, element, last):
    "Add the last list item"
    self.pending.additem(last)
    return self.decidelist(element, last)

  def decidelist(self, element, last):
    "After the last list element return it all"
    if isinstance(element, ListItem) and element.type == last.type:
      return element
    elif isinstance(element, DeeperList):
      element.output = EmptyOutput()
      return element
    list = self.pending.getlist()
    self.pending.__init__()
    return Group().contents([list, element])

class PostDeeperList(PostListItem):
  "Add nested lists as list items"

  processedclass = DeeperList

  def __init__(self, pending):
    self.pending = pending

  def lastprocess(self, element, last):
    "Add the last nested list"
    if last.sublist:
      tag = ListItem.typetags[last.type]
      last.output = TaggedOutput().settag(tag, True)
      self.pending.contents.append(last)
    else:
      if len(self.pending.contents) == 0:
        Trace.error('No items in list for nested element')
      else:
        Trace.debug('Adding ' + str(last) + ' to pending ' + str(self.pending))
        self.pending.contents[-1].contents.append(last)
    return self.decidelist(element, last)

class Postprocessor(object):
  "Postprocess an element keeping some context"

  def __init__(self):
    self.stages = [PostBiblio(), PostLayout()]
    pending = PendingList()
    self.laststages = [PostListItem(pending), PostDeeperList(pending)]
    self.stagedict = dict([(x.processedclass, x) for x in self.stages])
    self.laststagedict = dict([(x.processedclass, x) for x in self.laststages])
    self.last = None

  def postprocess(self, original):
    "Postprocess an element taking into account the last one"
    element = original
    if element.__class__ in self.stagedict:
      stage = self.stagedict[element.__class__]
      element = stage.postprocess(element, self.last)
    if self.last and self.last.__class__ in self.laststagedict:
      stage = self.laststagedict[self.last.__class__]
      element = stage.lastprocess(element, self.last)
    self.last = original
    return element

