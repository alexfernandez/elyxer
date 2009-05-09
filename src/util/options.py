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
  hardversion = False
  versiondate = False
  html = False
  help = False
  showlines = True
  css = 'http://www.nongnu.org/elyxer/lyx.css'
  title = 'Converted document'
  directory = '.'
  branches = dict()

  def parseoptions(self, args):
    "Parse command line options"
    parser = CommandLineParser(Options)
    result = parser.parseoptions(args)
    if result:
      Trace.error(result)
      self.usage()
    if Options.help:
      self.usage()
    if Options.version:
      self.showversion()
    if Options.hardversion:
      self.showhardversion()
    if Options.versiondate:
      self.showversiondate()
    # set in Trace if necessary
    for param in dir(Options):
      if hasattr(Trace, param + 'mode'):
        setattr(Trace, param + 'mode', getattr(self, param))

  def usage(self):
    "Show correct usage"
    Trace.error('Usage: elyxer.py [filein] [fileout].')
    Trace.error('  Options:')
    Trace.error('    --nocopy: disables the copyright notice at the bottom')
    Trace.error('    --quiet: disables all runtime messages')
    Trace.error('    --debug: enable debugging messages (for developers)')
    Trace.error('    --title <title>: set the generated page title')
    Trace.error('    --css <file.css>: use a custom CSS file')
    Trace.error('    --version: show version number and release date')
    Trace.error('    --html: output HTML 4.0 instead of the default XHTML')
    exit()

  def showversion(self):
    "Return the current eLyXer version string"
    string = 'eLyXer version ' + GeneralConfig.version['number']
    string += ' (' + GeneralConfig.version['date'] + ')'
    Trace.error(string)
    exit()

  def showhardversion(self):
    "Return just the version string"
    Trace.message(GeneralConfig.version['number'])
    exit()

  def showversiondate(self):
    "Return just the version dte"
    Trace.message(GeneralConfig.version['date'])
    exit()

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

