#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090308
# File line management for eLyXer

import sys
from trace import Trace


class LineReader(object):
  "Reads a file line by line"

  def __init__(self, file):
    self.file = file
    self.index = 0
    self.current = None
    self.split = None

  def currentline(self):
    "Get the current line"
    if not self.current:
      self.current = self.file.readline()
      if self.file == sys.stdin:
        self.current = self.current.decode('utf-8')
    return self.current

  def currentnonblank(self):
    "Get the current nonblank line"
    while (self.currentline() == '\n'):
      self.nextline()
    return self.currentline()

  def currentsplit(self):
    "Get the current nonblank line, split into words"
    if not self.split:
      self.split = self.currentnonblank().split()
    return self.split

  def nextline(self):
    "Go to next line"
    self.current = None
    self.split = None
    self.index += 1
    if self.index % 1000 == 0:
      Trace.message('Parsing line ' + str(self.index))

  def finished(self):
    "Have we finished reading the file"
    if len(self.currentline()) == 0:
      return True
    return False

  def close(self):
    self.file.close()

class HtmlWriter(object):
  "Writes an HTML file as a series of lists"

  def __init__(self, file):
    self.file = file

  def write(self, html):
    "Write a list of lines"
    for line in html:
      self.writeline(line)

  def writeline(self, line):
    "Write a line to file"
    if self.file == sys.stdout:
      line = line.encode('utf-8')
    self.file.write(line)

  def close(self):
    self.file.close()

