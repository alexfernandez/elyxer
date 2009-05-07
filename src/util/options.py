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
# Alex 20090313
# eLyXer runtime options

import codecs
from util.trace import *
from util.clparse import *


class Options(object):
  "A set of runtime options"

  instance = None

  nocopy = False
  debug = False
  quiet = False
  version = False
  showlines = True
  css = 'http://www.nongnu.org/elyxer/lyx.css'
  title = 'Converted document'
  directory = '.'
  branches = dict()

  def parseoptions(self, args):
    "Parse command line options"
    parser = CommandLineParser(Options)
    result = parser.parseoptions(args)
    # set in Trace if necessary
    for param in dir(Options):
      if hasattr(Trace, param + 'mode'):
        setattr(Trace, param + 'mode', getattr(self, param))
    return result

class BranchOptions(object):
  "A set of options for a branch"

  def __init__(self):
    self.selected = 0
    self.color = '#ffffff'

  def set(self, key, value):
    "Set a branch option"
    if not key.startswith('\\'):
      Trace.error('Invalid branch option ' + key)
      return
    key = key.replace('\\', '')
    setattr(self, key, value)

