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
# Alex 20101218
# eLyXer big symbol generation.

from util.trace import Trace
from conf.config import *


class BigSymbol(object):
  "A big symbol generator."

class CasesBrace(BigSymbol):
  "A big brace used for a case statement."

  def __init__(self, size):
    "Set the size for the brace."
    self.size = size

  def getpiece(self, index):
    "Get the nth piece from the brace."
    if index == 0:
      return u'⎧'
    if index == self.size - 1:
      return u'⎩'
    if index == (self.size - 1)/2:
      return u'⎨'
    return u'⎪'

