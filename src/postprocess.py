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
      return
    tag = TaggedText().constant('Bibliography', 'h1 class="biblio"')
    return Group().contents([tag, element])

class Postprocessor(object):
  "Postprocess an element keeping some context"

  stages = [PostBiblio()]

  stagedict = dict([(x.processedclass, x) for x in stages])

  def __init__(self):
    self.last = None

  def postprocess(self, element):
    "Postprocess an element taking into account the last one"
    if not self.last:
      self.last = element
      return element
    if not isinstance(element, Container):
      return element
    if not element.__class__ in Postprocessor.stagedict:
      return element
    stage = Postprocessor.stagedict[element.__class__]
    result = stage.postprocess(element, self.last)
    self.last = element
    if not result:
      return element
    return result

