#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090131
# eLyXer trace library

import sys

class Trace(object):
  "A tracing class"

  debugmode = False

  def debug(cls, message):
    "Show a trace message"
    if Trace.debugmode:
      print message

  def error(cls, message):
    "Show an error message"
    message = message.encode('utf-8')
    sys.stderr.write(message + '\n')

  debug = classmethod(debug)
  error = classmethod(error)

