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

  def __init__(self):
    self.partkey = None
    self.tocentry = None
    self.level = 0
    self.anchortext = None
    self.number = None

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
    self.number = ''
    return self

