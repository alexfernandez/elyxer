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

from gen.container import *
from util.trace import Trace
from gen.structure import *
from ref.label import *
from gen.layout import *
from gen.inset import *
from util.numbering import *
from ref.link import *


class Group(Container):
  "A silly group of containers"

  def __init__(self):
    self.output = ContentsOutput()

  def contents(self, contents):
    self.contents = contents
    return self

  def __str__(self):
    return 'Group: ' + str(self.contents)

class PostNestedList(object):
  "Postprocess a nested list"

  processedclass = DeeperList

  def postprocess(self, deeper, last):
    "Run the postprocessor on the nested list"
    postproc = Postprocessor()
    for index, part in enumerate(deeper.contents):
      result = postproc.postprocess(part)
      deeper.contents[index] = result
    # one additional item to flush the list
    deeper.contents.append(postproc.postprocess(BlackBox()))
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
    tag = ListItem.typetags[self.type]
    return TaggedText().complete(self.contents, tag, True)

  def empty(self):
    return len(self.contents) == 0

  def insertfake(self):
    "Insert a fake item"
    item = TaggedText().constant('', 'li class="nested"', True)
    self.contents = [item]
    self.type = 'Itemize'

  def __str__(self):
    result = 'pending ' + str(self.type) + ': ['
    for element in self.contents:
      result += str(element) + ', '
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
    if self.generatepending(element):
      list = self.pending.generatelist()
      self.pending.__init__()
    if isinstance(element, ListItem):
      element = self.processitem(element)
    elif isinstance(element, DeeperList):
      element = self.processnested(element)
    if not list:
      return element
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

class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout

  ordered = ['Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph']
  unique = ['Part', 'Book']

  def __init__(self):
    self.generator = NumberGenerator.instance

  def postprocess(self, layout, last):
    "Generate a number and place it before the text"
    if self.containsappendix(layout):
      self.activateappendix()
    if layout.type in PostLayout.unique:
      number = self.generator.generateunique(layout.type)
    elif layout.type in PostLayout.ordered:
      level = PostLayout.ordered.index(layout.type)
      number = self.generator.generate(level)
    elif layout.type == 'Standard':
      return self.checkforfloat(layout)
    else:
      return layout
    layout.contents.insert(0, Constant(number + u' '))
    return layout

  def containsappendix(self, layout):
    "Find out if there is an appendix somewhere in the layout"
    for element in layout.contents:
      if isinstance(element, Appendix):
        return True
    return False

  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    self.generator.number = ['-']

  def checkforfloat(self, standard):
    "Check a standard layout for a float inset"
    float = standard.searchfor(Float)
    if not float:
      return standard
    caption = float.searchfor(Caption)
    for layout in caption.contents:
      for element in layout.contents:
        self.movelabel(float, layout, element)
    return float

  def movelabel(self, float, layout, element):
    "Move any labels to the start of the float"
    if not isinstance(element, Label):
      return
    float.contents.insert(0, element)
    index = layout.contents.index(element)
    layout.contents[index] = BlackBox()

class PostStandard(object):
  "Convert any standard spans in root to divs"

  processedclass = StandardLayout

  def postprocess(self, standard, last):
    "Switch span to div"
    standard.output.tag = 'div class="Standard"'
    return standard

class Postprocessor(object):
  "Postprocess an element keeping some context"

  stages = [PostNestedList, PostLayout, PostStandard]
  unconditional = [PostListPending]

  def __init__(self):
    self.stages = self.instantiate(Postprocessor.stages)
    self.stagedict = dict([(x.processedclass, x) for x in self.stages])
    self.unconditional = self.instantiate(Postprocessor.unconditional)
    self.last = None

  def postprocess(self, original):
    "Postprocess an element taking into account the last one"
    element = original
    if element.__class__ in self.stagedict:
      stage = self.stagedict[element.__class__]
      element = stage.postprocess(element, self.last)
    for stage in self.unconditional:
      element = stage.postprocess(element, self.last)
    self.last = original
    return element

  def instantiate(self, classes):
    "Instantiate an element from each class"
    list = [x.__new__(x) for x in classes]
    for element in list:
      element.__init__()
    return list

