#!/usr/bin/python
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
from container import *
from link import *
from formula import *
from table import *
from image import *


class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox,
        # do not add above this line
        Title, Author, EmphaticText, VersalitasText, Image, QuoteContainer,
        IndexEntry, BiblioEntry, BiblioCite, LangLine, Reference, Label,
        TextFamily, Formula, PrintIndex, LyxHeader, LyxFooter, URL, ListOf,
        TableOfContents, Hfill, ColorText, SizeText, BoldText, LyxLine,
        Align, Table, TableHeader, Row, Cell, Bibliography,
        InsetText, Caption, ListItem,
        # do not add below this line
        Layout, Float, StringContainer]

  root = ParseTree(types)

  @classmethod
  def create(cls, reader):
    "Get the container and parse it"
    # Trace.debug('processing ' + reader.currentline().strip())
    type = ContainerFactory.root.find(reader)
    container = type.__new__(type)
    container.__init__()
    container.factory = ContainerFactory
    container.parse(reader)
    return container

class Book():
  "book in a lyx file"

  def parsecontents(self, reader, writer):
    "Parse the contents of the reader and write them"
    while not reader.finished():
      container = ContainerFactory.create(reader)
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

