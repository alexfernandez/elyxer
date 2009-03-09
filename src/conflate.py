#!/usr/bin/python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090309
# conflates all into one file to generate an executable

import sys
import codecs
from fileline import *
from trace import Trace


files = list()

def getreader(filename):
  "Get a reader for lines"
  if filename in files:
    # already parsed; skip
    return None
  files.append(filename)
  filein = codecs.open(filename, 'r', "utf-8")
  return LineReader(filein)

def readargs(args):
  "Read arguments from the command line"
  del args[0]
  if len(args) == 0:
    Trace.error('Usage: conflate.py filein [fileout]')
    return
  reader = getreader(args[0])
  del args[0]
  fileout = sys.stdout
  if len(args) > 0:
    fileout = codecs.open(args[0], 'w', "utf-8")
    del args[0]
  if len(args) > 0:
    Trace.error('Usage: conflate.py filein [fileout]')
    return
  writer = HtmlWriter(fileout)
  return reader, writer

def conflate(reader, writer):
  "Conflate all Python files used in filein to fileout"
  if not reader:
    return
  while not reader.finished():
    line = reader.currentline()
    if line.startswith('from'):
      filename = line.split()[1] + '.py'
      newreader = getreader(filename)
      conflate(newreader, writer)
    else:
      writer.writeline(line)
    reader.nextline()
  reader.close()

reader, writer = readargs(sys.argv)
if reader:
  conflate(reader, writer)
  writer.close()

  

