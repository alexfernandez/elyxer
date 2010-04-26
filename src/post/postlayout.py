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
# Alex 20100411
# eLyXer postprocessing layouts.

from gen.container import *
from util.trace import Trace
from gen.structure import *
from ref.label import *
from gen.layout import *
from util.numbering import *
from ref.link import *
from post.postprocess import *


class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout

  def postprocess(self, last, layout, next):
    "Generate a number and place it before the text"
    if not hasattr(layout, 'number'):
      return layout
    label = Label().create(layout.anchortext, layout.partkey, type='toc')
    layout.contents.insert(0, label)
    if layout.anchortext != '':
      layout.contents.insert(1, Constant(u' '))
    return layout
    if not LayoutNumberer.instance.isnumbered(layout):
      return layout
    if self.containsappendix(layout):
      self.activateappendix()
    LayoutNumberer.instance.numberlayout(layout)
    label = Label().create(layout.anchortext, layout.partkey, type='toc')
    layout.contents.insert(0, label)
    if layout.anchortext != '':
      layout.contents.insert(1, Constant(u' '))
    return layout

  def modifylayout(self, layout, type):
    "Modify a layout according to the given type."
    layout.level = NumberGenerator.instance.getlevel(type)
    layout.output.tag = layout.output.tag.replace('?', unicode(layout.level))

  def containsappendix(self, layout):
    "Find out if there is an appendix somewhere in the layout"
    for element in layout.contents:
      if isinstance(element, Appendix):
        return True
    return False

  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    NumberGenerator.instance.number = ['-']

class PostStandard(object):
  "Convert any standard spans in root to divs"

  processedclass = StandardLayout

  def postprocess(self, last, standard, next):
    "Switch to div"
    type = 'Standard'
    if LyXHeader.indentstandard:
      if isinstance(last, StandardLayout):
        type = 'Indented'
      else:
        type = 'Unindented'
    standard.output = TaggedOutput().settag('div class="' + type + '"', True)
    return standard

class PostLyXCode(object):
  "Coalesce contiguous LyX-Code layouts."

  processedclass = LyXCode

  def postprocess(self, last, lyxcode, next):
    "Coalesce if last was also LyXCode"
    if not isinstance(last, LyXCode):
      return lyxcode
    if hasattr(last, 'first'):
      lyxcode.first = last.first
    else:
      lyxcode.first = last
    toappend = lyxcode.first.contents
    toappend.append(Constant('\n'))
    toappend += lyxcode.contents
    lyxcode.output = EmptyOutput()
    return lyxcode

Postprocessor.stages += [PostLayout, PostStandard, PostLyXCode]

