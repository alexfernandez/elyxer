#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 31-01-2009
# Generate custom HTML version from Lyx document
# Trace library

class Trace(object):
  "A tracing class"

  debugmode = False

  @classmethod
  def debug(cls, message):
    "Show a trace message"
    if Trace.debug:
      print message

  @classmethod
  def error(cls, message):
    "Show an error message"
    print message

