#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090127
# Generate custom HTML version from Lyx document
# Main file generation

import sys
import codecs
import os.path
import shutil
sys.path.append('./elyxer')
from container import *
from link import *
from preprocess import Preprocessor
from table import *
from formula import Formula
from trace import Trace
from node import *


class HtmlFile(object):
  "HTML file out"

  def __init__(self):
    self.currentnode = None

  def writebook(self, book):
    "Write a full book"
    self.title = book.title
    self.checkrestart(book)
    try:
      for container in book.contents:
        self.checkrestart(container)
        html = container.gethtml()
        for line in html:
          self.file.write(line)
      self.end()
    finally:
      self.file.close()

  def checkrestart(self, container):
    "Check if file must be restarted"
    if not self.checknode(container):
      return
    if self.currentnode:
      self.end()
    self.currentnode = container.node
    self.open()

  def checknode(self, container):
    "Check a node, see if requires new file"
    if not hasattr(container, 'node'):
      return False
    if not self.currentnode:
      return True
    if self.currentnode.filename == container.node.filename:
      return False
    return True

  def open(self):
    "Open a new filename and write the preamble"
    node = self.currentnode
    Trace.debug('Writing file ' + node.filename)
    self.file = codecs.open(node.filename, 'w', 'utf-8')
    subst = {'$title':self.title}
    if node.last:
      subst['$last'] = node.last.filename
    if node.next:
      subst['$next'] = node.next.filename
    if node.parent:
      subst['$up'] = node.parent.filename
    self.readwrite('../elyxer/header.html', subst)

  def readwrite(self, filename, substitutions):
    "Read a file and write it with optional substitutions"
    "Every substitution must begin with $"
    headerfile = codecs.open(filename, 'r', 'utf-8')
    header = headerfile.readlines()
    for line in header:
      if '$' in line:
        for original in substitutions:
          line = line.replace(original, substitutions[original])
      self.file.write(line)

  def separator(self):
    self.file.write('<hr/>\n')

  def end(self):
    self.separator()
    self.readwrite('../elyxer/footer.html', {})

class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox,
        # do not add above this line
        Layout, EmphaticText, VersalitasText, Image, QuoteContainer,
        IndexEntry, BiblioEntry, BiblioCite, LangLine, Reference, Label,
        TextFamily, Formula, PrintIndex, LyxHeader, URL, ListOf,
        TableOfContents, Hfill, ColorText, SizeText, BoldText, LyxLine,
        Align, Table, TableHeader, Row, Cell, Bibliography,
        InsetText, Caption,
        # do not add below this line
        Float, StringContainer]

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

class Book(Container):
  "book in a lyx file"

  def parsecontents(self, reader):
    "Parse the contents of the reader"
    reader.nextline()
    while not reader.finished():
      container = ContainerFactory.create(reader)
      self.contents.append(container)

  def createhier(self):
    "Create a hierarchy of nodes"
    hier = Hierarchy('book.html')
    hier.add(self)
    self.node = hier.root

  def preprocess(self):
    "Preprocess the whole book"
    preprocessor = Preprocessor()
    round = 1
    counter = preprocessor.preprocess(self.contents)
    while counter > 0:
      Trace.debug('Round ' + str(round) + ': preprocessed ' + str(counter) + ' elements')
      counter = preprocessor.preprocess(self.contents)
      round += 1

  def show(self):
    Trace.debug('Book has ' + str(len(self.contents)) + ' layouts')

  def writeresult(self):
    file = HtmlFile()
    self.title = Layout.title
    file.writebook(self)

def makedir(filename):
  basedir = os.path.splitext(filename)[0]
  try:
    os.mkdir(basedir)
  except:
    pass
  shutil.copyfile('elyxer/lyx.css', basedir + '/lyx.css')
  os.chdir(basedir)

def createbook(filename):
  "Read the whole book, write it"
  reader = LineReader(filename)
  book = Book()
  book.parsecontents(reader)
  makedir(filename)
  Trace.debug('Numbering')
  book.createhier()
  Trace.debug('Preprocessing')
  book.preprocess()
  book.show()
  book.writeresult()

Trace.debugmode = True
biblio = dict()
args = sys.argv
del args[0]
for arg in args:
  createbook(arg)

