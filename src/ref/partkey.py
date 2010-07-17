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
# Alex 20100705
# eLyXer: key that identifies a given document part (chapter, section...).

from util.trace import Trace
from util.options import *
from util.translate import *
from util.numbering import *
from util.docparams import *
from ref.label import *


class PartKey(object):
  "A key to identify a given document part (chapter, section...)."

  partkey = None
  tocentry = None
  tocsuffix = None
  anchortext = None
  number = None
  filename = None
  header = False

  def __init__(self):
    self.level = 0

  def createindex(self, partkey):
    "Create a part key for an index page."
    self.partkey = partkey
    self.tocentry = partkey
    self.filename = partkey
    return self

  def createfloat(self, partkey, number):
    "Create a part key for a float."
    self.partkey = partkey
    self.number = number
    self.tocentry = partkey
    self.tocsuffix = u':'
    return self

  def createformula(self, number):
    "Create the part key for a formula."
    self.number = number
    self.partkey = 'formula-' + number
    self.tocentry = '(' + number + ')'
    return self

  def createheader(self, headorfooter):
    "Create the part key for a header or footer."
    self.partkey = headorfooter
    self.tocentry = None
    self.header = True
    return self

  def createanchor(self, partkey):
    "Create an anchor for the page."
    self.partkey = partkey
    self.tocentry = partkey
    self.header = True
    return self

  def toclabel(self):
    "Create the label for the TOC."
    labeltext = ''
    if self.anchortext:
      labeltext = self.anchortext
    return Label().create(labeltext, self.partkey, type='toc')

  def __unicode__(self):
    "Return a printable representation."
    return 'Part key for ' + self.partkey

class LayoutPartKey(PartKey):
  "The part key for a layout."

  generator = NumberGenerator.instance
  unique = NumberingConfig.layouts['unique']
  ordered = NumberingConfig.layouts['ordered']

  def __init__(self, layout):
    "Create a part key for a layout."
    self.level = self.getlevel(layout.type)
    if LayoutPartKey.isunique(layout):
      self.number = self.generator.generateunique(layout.type)
    else:
      if self.isnumbered(layout):
        self.number = self.generator.generateordered(self.level)
      else:
        self.number = self.generator.generateunique(layout.type)
    anchortype = layout.type.replace('*', '-')
    self.partkey = 'toc-' + anchortype + '-' + self.number
    realtype = self.deasterisk(layout.type)
    self.tocentry = Translator.translate(realtype)
    self.tocsuffix = u': '
    if self.level == Options.splitpart and self.isnumbered(layout):
      self.filename = self.number
    elif self.level <= Options.splitpart:
      self.filename = self.partkey.replace('toc-', '').replace('*', '-')
    if self.isnumbered(layout):
      self.tocentry += ' ' + self.number
      self.tocsuffix = u':'
      if self.isunique(layout):
        self.anchortext = self.tocentry + '.'
      else:
        self.anchortext = self.number

  def getlevel(self, type):
    "Get the level that corresponds to a type."
    type = self.deasterisk(type)
    if type in self.unique:
      return 0
    level = self.ordered.index(type) + 1
    return level - DocumentParameters.startinglevel

  def isnumbered(self, layout):
    "Find out if a layout is numbered."
    if '*' in layout.type:
      return False
    if self.getlevel(layout.type) > DocumentParameters.maxdepth:
      return False
    return True

  def isunique(cls, layout):
    "Find out if the layout requires unique numbering."
    return cls.deasterisk(layout.type) in LayoutPartKey.unique

  def isinordered(cls, layout):
    "Find out if a layout is ordered or unordered."
    return cls.deasterisk(layout.type) in LayoutPartKey.ordered

  def needspartkey(cls, layout):
    "Find out if a layout needs a part key."
    if cls.isunique(layout):
      return True
    return cls.isinordered(layout)

  def deasterisk(cls, type):
    "Get the type without the asterisk for unordered types."
    return type.replace('*', '')

  def __unicode__(self):
    "Get a printable representation."
    return 'Part key for layout ' + self.tocentry

  isunique = classmethod(isunique)
  isinordered = classmethod(isinordered)
  needspartkey = classmethod(needspartkey)
  deasterisk = classmethod(deasterisk)

class PartKeyGenerator(object):
  "Number a layout with the relevant attributes."

  partkeyed = []

  def forlayout(cls, layout):
    "Get the part key for a layout."
    if not LayoutPartKey.needspartkey(layout):
      return None
    Label.lastlayout = layout
    cls.partkeyed.append(layout)
    return LayoutPartKey(layout)

  def forindex(cls, index):
    "Get the part key for an index or nomenclature."
    cls.partkeyed.append(index)
    return PartKey().createindex(index.name)

  forlayout = classmethod(forlayout)
  forindex = classmethod(forindex)
