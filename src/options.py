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


class Options(object):
  "A set of runtime options"

  nocopy = False
  debug = False
  quiet = False
  css = 'http://www.nongnu.org/elyxer/lyx.css'
  title = 'Converted document'
  directory = '.'

  def parseoptions(self, args):
    "Parse command line options"
    while args[0].startswith('--'):
      if args[0] == '--help':
        return 'eLyXer help'
      key, value = self.readoption(args)
      if not key:
        return 'Option ' + original + ' not recognized'
      if not value:
        return 'Option ' + key + ' needs a value'
      setattr(Options, key, value)
    return None

  def readoption(self, args):
    "Read the key and value for an option"
    arg = args[0][2:]
    del args[0]
    if '=' in arg:
      return self.readequals(arg, args)
    key = arg
    if not hasattr(Options, key):
      return None, None
    current = getattr(Options, key)
    if current.__class__ == bool:
      return key, True
    # read value
    if len(args) == 0:
      return key, None
    if args[0].startswith('"'):
      initial = args[0]
      del args[0]
      return key, self.readquoted(args, initial)
    value = args[0]
    del args[0]
    return key, value

  def readquoted(self, args, initial):
    "Read a value between quotes"
    value = initial[1:]
    while len(args) > 0 and not args[0].endswith('"') and not args[0].startswith('--'):
      value += ' ' + args[0]
      del args[0]
    if len(args) == 0 or args[0].startswith('--'):
      return None
    value += ' ' + args[0:-1]
    return value

  def readequals(self, arg, args):
    "Read a value with equals"
    split = arg.split('=', 1)
    key = split[0]
    value = split[1]
    if not value.startswith('"'):
      return key, value
    return key, self.readquoted(args, value)

