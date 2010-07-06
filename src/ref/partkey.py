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


class PartKey(object):
  "A key to identify a given document part (chapter, section...)."

  partkey = None
  tocentry = None
  anchortext = None
  number = None

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
    self.level = 0
    return self

  def createfloat(self, partkey, number):
    "Create a part key for a float."
    self.partkey = partkey
    self.level = 0
    self.number = number
    self.tocentry = partkey
    return self

  def createformula(self, number):
    "Create the part key for a formula."
    self.number = number
    self.partkey = '(' + number + ')'
    self.entry = self.partkey
    return self

