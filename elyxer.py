#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090308
# eLyXer: create HTML file from LyX document


import sys
import codecs
from trace import Trace
from fileline import *


class Book():
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    while not reader.finished():
      line = reader.currentline()
      writer.write(line)
      reader.nextline()

def createbook(args):
  "Read a whole book, write it"
  Trace.debugmode = False
  filein = sys.stdin
  fileout = sys.stdout
  if len(args) > 0:
    filein = codecs.open(args[0], 'r', "utf-8")
    del args[0]
  if len(args) > 0:
    fileout = codecs.open(args[0], 'w', "utf-8")
    del args[0]
    Trace.debugmode = True
  if len(args) > 0:
    Trace.error('Usage: eLyXer [filein] [fileout]')
    return
  reader = LineReader(filein)
  writer = LineWriter(fileout)
  book = Book()
  book.parsecontents(reader, writer)

biblio = dict()
args = sys.argv
del args[0]
createbook(args)

