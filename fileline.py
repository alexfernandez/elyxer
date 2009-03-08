#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    if not self.current:
      self.current = self.file.readline()
      if self.file == sys.stdin:
        self.current = self.current.decode('utf-8')
    return self.current

  def currentsplit(self):
    if not self.split:
      self.split = self.currentline().split()
    return self.split

  def nextline(self):
    "Go to next line"
    self.inc()
    if not self.finished():
      self.skipempties()

  def finished(self):
    if len(self.currentline()) == 0:
      return True
    return False

  def skipempties(self):
    "Skip empty lines"
    while self.currentline() == '\n':
      self.inc()

  def inc(self):
    self.current = None
    self.split = None
    self.index += 1
    if self.index % 1000 == 0:
      Trace.debug('Parsing line ' + str(self.index))

  def close(self):
    self.file.close()

class LineWriter:
  "Writes a file, line by line"

  def __init__(self, file):
    self.file = file
    self.index = 0

  def write(self, line):
    if self.file == sys.stdout:
      line = line.encode('utf-8')
    self.file.write(line)

