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
from options import *


class Book(object):
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    factory = ContainerFactory()
    while not reader.finished():
      container = factory.create(reader)
      writer.write(container.gethtml())

def createbook(args):
  "Read a whole book, write it"
  filein = sys.stdin
  fileout = sys.stdout
  if len(args) < 2:
    Options.quiet = true
  if len(args) > 0:
    filein = codecs.open(args[0], 'r', "utf-8")
    del args[0]
  if len(args) > 0:
    fileout = codecs.open(args[0], 'w', "utf-8")
    del args[0]
  if len(args) > 0:
    usage('Too many arguments')
    return
  reader = LineReader(filein)
  writer = HtmlWriter(fileout)
  book = Book()
  book.parsecontents(reader, writer)

def usage(error):
  "Show an error message and correct usage"
  if not error:
    return
  Trace.error(error)
  Trace.error('Usage: eLyXer [filein] [fileout].')
  Trace.error('  Options:')
  Trace.error('    --nocopy: disables the copyright notice at the bottom')
  Trace.error('    --quiet: disables all runtime messages')
  exit()

biblio = dict()
args = sys.argv
del args[0]
error = Options().parseoptions(args)
if error:
  usage(error)
  exit()
createbook(args)

