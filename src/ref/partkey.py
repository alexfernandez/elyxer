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


class PartKey(object):
  "A key to identify a given document part (chapter, section...)."

  partkey = None
  tocentry = None
  tocsuffix = None
  anchortext = None
  number = None
  header = False

  def __init__(self):
    self.level = 0

  def create(self, partkey, tocentry, level):
    "Create the part key."
    self.partkey = partkey
    self.tocentry = tocentry
    self.level = level
    return self

  def createlayout(self, type, level, number):
    "Create a part key for a layout."
    self.partkey = 'toc-' + type + '-' + number
    self.tocentry = Translator.translate(type) + ' ' + number
    self.tocsuffix = u':'
    self.level = level
    self.number = number
    return self

  def createindex(self, partkey):
    "Create a part key for an index page."
    self.partkey = partkey
    self.tocentry = partkey
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
    self.tocentry = '(' + number + ') :'
    return self

  def createheader(self, headorfooter):
    "Create the part key for a header or footer."
    self.partkey = headorfooter
    self.tocentry = None
    self.header = True
    return self

  def mustsplit(self):
    "Find out if the part should stand in its own page."
    if self.header:
      return False
    return self.level <= Options.splitpart

  def __unicode__(self):
    "Return a printable representation."
    return 'Part key for ' + self.partkey

