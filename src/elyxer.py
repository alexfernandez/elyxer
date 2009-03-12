#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090308
# eLyXer main script


import sys
import codecs
from trace import Trace
from fileline import *
from styles import *
from link import *
from formula import *
from table import *
from image import *
from structure import *
from container import *


class Book():
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    factory = ContainerFactory()
    while not reader.finished():
      container = factory.create(reader)
      writer.write(container.gethtml())

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
  writer = HtmlWriter(fileout)
  book = Book()
  book.parsecontents(reader, writer)

biblio = dict()
args = sys.argv
del args[0]
createbook(args)

