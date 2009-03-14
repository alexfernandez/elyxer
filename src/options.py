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

  def parseoptions(self, args):
    "Parse command line options"
    while args[0].startswith('--'):
      option = args[0].replace('-', '')
      if option == 'help':
        return 'eLyXer help'
      if not hasattr(Options, option):
        return 'Option ' + option + ' not recognized'
      setattr(Options, option, True)
      del args[0]
    return None

