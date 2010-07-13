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

  def create(self, partkey, tocentry, level):
    "Create the part key."
    self.partkey = partkey
    self.tocentry = tocentry
    self.level = level
    return self

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

  def toclabel(self):
    "Create the label for the TOC."
    labeltext = ''
    if self.anchortext:
      labeltext = self.anchortext
    return Label().create(labeltext, self.partkey, type='toc')

  def mustsplit(self):
    "Find out if the part should stand in its own page."
    if self.header:
      return False
    return self.level <= Options.splitpart

  def __unicode__(self):
    "Return a printable representation."
    return 'Part key for ' + self.partkey

class LayoutPartKey(PartKey):
  "The part key for a layout."

  unique = NumberingConfig.layouts['unique']
  ordered = NumberingConfig.layouts['ordered']

  def __init__(self, layout, number):
    "Create a part key for a layout."
    rawtype = layout.type
    self.level = self.getlevel(layout.type)
    self.partkey = 'toc-' + rawtype + '-' + number
    realtype = self.deasterisk(rawtype)
    self.tocentry = Translator.translate(realtype)
    self.tocsuffix = u': '
    self.number = number
    if self.level == Options.splitpart and self.isnumbered(layout):
      self.filename = number
    else:
      self.filename = self.partkey.replace('toc-', '').replace('*', '-')
    if self.isnumbered(layout):
      self.tocentry += ' ' + number
      self.tocsuffix = u':'
      if self.isunique(layout):
        self.anchortext = self.tocentry + '.'
      else:
        self.anchortext = number

  def deasterisk(self, type):
    "Get the type without the asterisk for unordered types."
    return type.replace('*', '')

  def getlevel(self, type):
    "Get the level that corresponds to a type."
    type = self.deasterisk(type)
    if type in self.unique:
      return 0
    level = self.ordered.index(type) + 1
    return level - DocumentParameters.startinglevel

  def isunique(self, layout):
    "Find out if the layout requires unique numbering."
    return layout.type in self.unique

  def isinordered(self, layout):
    "Find out if a layout is ordered or unordered."
    return layout.type in self.ordered

  def isnumbered(self, layout):
    "Find out if a layout is numbered."
    if '*' in layout.type:
      return False
    if self.level > DocumentParameters.maxdepth:
      return False
    return True

  def __unicode__(self):
    "Get a printable representation."
    return 'Part key for layout ' + self.tocentry

