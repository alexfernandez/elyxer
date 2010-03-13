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
import os.path
from util.trace import *
from util.clparse import *


class Options(object):
  "A set of runtime options"

  instance = None

  location = None
  nocopy = False
  debug = False
  quiet = False
  version = False
  hardversion = False
  versiondate = False
  html = False
  help = False
  showlines = True
  unicode = False
  iso885915 = False
  css = 'http://www.nongnu.org/elyxer/lyx.css'
  title = None
  directory = None
  destdirectory = None
  toc = False
  toctarget = ''
  forceformat = None
  lyxformat = False
  target = None
  splitpart = None
  memory = True
  lowmem = False
  nobib = False
  converter = 'imagemagick'
  numberfoot = False
  raw = False

  branches = dict()

  def parseoptions(self, args):
    "Parse command line options"
    Options.location = args[0]
    del args[0]
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
    if Options.lyxformat:
      self.showlyxformat()
    if Options.splitpart:
      try:
        Options.splitpart = int(Options.splitpart)
        if Options.splitpart <= 0:
          Trace.error('--splitpart requires a number bigger than zero')
          self.usage()
      except:
        Trace.error('--splitpart needs a numeric argument, not ' + Options.splitpart)
        self.usage()
    if Options.lowmem or Options.toc:
      Options.memory = False
    # set in Trace if necessary
    for param in dir(Options):
      if hasattr(Trace, param + 'mode'):
        setattr(Trace, param + 'mode', getattr(self, param))

  def usage(self):
    "Show correct usage"
    Trace.error('Usage: ' + os.path.basename(Options.location) + ' [options] [filein] [fileout]')
    Trace.error('Convert LyX input file "filein" to HTML file "fileout".')
    Trace.error('If filein (or fileout) is not given use standard input (or output).')
    self.showoptions()

  def showoptions(self):
    "Show all possible options"
    Trace.error('  Common options:')
    Trace.error('    --nocopy:               disables the copyright notice at the bottom')
    Trace.error('    --quiet:                disables all runtime messages')
    Trace.error('    --debug:                enable debugging messages (for developers)')
    Trace.error('    --title "title":        set the generated page title')
    Trace.error('    --directory "img_dir":  look for images in the specified directory')
    Trace.error('    --destdirectory "dest": put converted images into this directory')
    Trace.error('    --css "file.css":       use a custom CSS file')
    Trace.error('    --html:                 output HTML 4.0 instead of the default XHTML')
    Trace.error('    --unicode:              full Unicode output')
    Trace.error('    --iso885915:            output a document with ISO-8859-15 encoding')
    Trace.error('')
    Trace.error('  Esoteric options:')
    Trace.error('    --version:              show version number and release date')
    Trace.error('    --forceformat ".ext":   force image output format')
    Trace.error('    --lyxformat:            return the highest LyX version supported')
    Trace.error('    --toc:                  create a table of contents')
    Trace.error('    --target "frame":       make all links point to the given frame')
    Trace.error('    --lowmem:               do the conversion on the fly (conserve memory)')
    Trace.error('    --converter inkscape:   use Inkscape to convert images')
    Trace.error('    --numberfoot:           label footnotes with numbers instead of letters')
    Trace.error('    --raw:                  generate HTML without header or footer.')
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

  def showlyxformat(self):
    "Return just the lyxformat parameter"
    Trace.message(GeneralConfig.version['lyxformat'])
    exit()

class BranchOptions(object):
  "A set of options for a branch"

  def __init__(self, name):
    self.name = name
    self.options = {'color':'#ffffff'}

  def set(self, key, value):
    "Set a branch option"
    if not key.startswith(ContainerConfig.string['startcommand']):
      Trace.error('Invalid branch option ' + key)
      return
    key = key.replace(ContainerConfig.string['startcommand'], '')
    self.options[key] = value

  def isselected(self):
    "Return if the branch is selected"
    if not 'selected' in self.options:
      return False
    return self.options['selected'] == '1'

  def __unicode__(self):
    "String representation"
    return 'options for ' + self.name + ': ' + unicode(self.options)

