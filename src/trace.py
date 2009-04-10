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
# Alex 20090131
# eLyXer trace library

import sys

class Trace(object):
  "A tracing class"

  debugmode = False
  quietmode = False

  prefix = None

  def debug(cls, message):
    "Show a debug message"
    if Trace.debugmode and not Trace.quietmode:
      print message

  def message(cls, message):
    "Show a trace message"
    if Trace.quietmode:
      return
    if Trace.prefix:
      message = Trace.prefix + message
    print message

  def error(cls, message):
    "Show an error message"
    if Trace.prefix:
      message = Trace.prefix + message
    message = message.encode('utf-8')
    sys.stderr.write(message + '\n')

  debug = classmethod(debug)
  message = classmethod(message)
  error = classmethod(error)

