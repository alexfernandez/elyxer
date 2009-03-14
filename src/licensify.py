#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# --start--
# Alex 20090314
# Modifies the license of a Python source file

import os
import sys
import codecs
from fileline import *
from trace import Trace


mark = '# Alex'

def readall(filename):
  "Read the whole file"
  filein = codecs.open(filename, 'r', "utf-8")
  return filein.readlines()

def getfiles(filename):
  "Get reader and writer for a file name"
  filein = codecs.open(filename, 'r', "utf-8")
  reader = LineReader(filein)
  fileout = codecs.open(filename + '.temp', 'w', "utf-8")
  writer = HtmlWriter(fileout)
  return reader, writer

def process(reader, writer, license):
  "Conflate all Python files used in filein to fileout"
  for line in license:
    writer.writeline(line)
  while not reader.currentline().startswith(mark):
    reader.nextline()
  while not reader.finished():
    line = reader.currentline()
    writer.writeline(line)
    reader.nextline()
  reader.close()

def processall(args):
  "Process all arguments"
  del args[0]
  license = readall('header-license')
  while len(args) > 0:
    filename = args[0]
    reader, writer = getfiles(filename)
    del args[0]
    process(reader, writer, license)
    os.rename(filename + '.temp', filename)

processall(sys.argv)

