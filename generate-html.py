#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090127
# Generate custom HTML version from Lyx document
# Main file and preprocessor

import sys
import codecs
import os.path
import shutil
sys.path.append('./bin')
from container import *
from preprocess import Preprocessor
from table import *
from formula import Formula
from trace import Trace


class HtmlFile(object):
  "HTML file out"

  def __init__(self, filename):
    Trace.debug('Writing file ' + filename)
    self.file = codecs.open(filename, 'w', 'utf-8')

  def writebook(self, book, title):
    "Write a full book"
    try:
      self.init(title)
      for container in book.contents:
        html = container.gethtml()
        for line in html:
          # Trace.debug('writing ' + line)
          self.file.write(line)
      self.end()
    finally:
      self.file.close()

  def init(self, title):
    "HTML preamble"
    self.file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    self.file.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
    self.file.write('<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n')
    self.file.write('<head>\n')
    self.file.write('<title>\n')
    self.file.write(title + '\n')
    self.file.write('</title>\n')
    self.file.write('<link rel="stylesheet" href="../lyx.css" type="text/css" media="screen"/>\n')
    self.file.write('</head>\n')
    self.file.write('<body>\n')
    self.file.write('<div id="globalWrapper">\n')

  def separator(self):
    self.file.write('<hr/>\n')

  def end(self):
    self.separator()
    self.file.write(u'<p class="bottom">(C) 2009 Alex Fernández</p>\n')
    self.file.write('</div>\n')
    self.file.write('</body>\n')
    self.file.write('</html>\n')

class ContainerFactory(object):
  "Creates containers depending on the first line"

  types = [BlackBox,
        # do not add above this line
        Layout, EmphaticText, VersalitasText, Image, QuoteContainer,
        IndexEntry, BiblioEntry, BiblioCite, LangLine, Reference, Label,
        TextFamily, Formula, PrintIndex, LyxHeader, URL, ListOf,
        TableOfContents, Hfill, ColorText, SizeText, BoldText, LyxLine,
        Align, Table, TableHeader, Row, Cell,
        # do not add below this line
        Float, Inset, StringContainer]

  root = ParseTree(types)

  @classmethod
  def create(cls, reader):
    "Get the container and parse it"
    # Trace.debug('processing ' + reader.currentline().strip())
    type = ContainerFactory.root.find(reader.currentline())
    container = type.__new__(type)
    container.__init__()
    if hasattr(container, 'ending'):
      container.parser.ending = container.ending
    container.parser.factory = ContainerFactory
    container.header = container.parser.parseheader(reader)
    container.contents = container.parser.parse(reader)
    container.process()
    container.parser = []
    return container

class Book(object):
  "book in a lyx file"

  def __init__(self):
    self.contents = list()

  def parsecontents(self, reader):
    "Parse the contents of the reader"
    reader.nextline()
    while not reader.finished():
      container = ContainerFactory.create(reader)
      self.contents.append(container)

  def preprocess(self):
    "Preprocess the whole book"
    preprocessor = Preprocessor()
    preprocessor.preprocess(self.contents)

  def show(self):
    Trace.debug('Book has ' + str(len(self.contents)) + ' layouts')

  def writeresult(self):
    file = HtmlFile('book.html')
    file.writebook(self, Layout.title)

def makedir(filename):
  basedir = os.path.splitext(filename)[0]
  try:
    os.mkdir(basedir)
  except:
    pass
  # shutil.copyfile('lyx.css', basedir + '/lyx.css')
  os.chdir(basedir)

def createbook(filename):
  "Read the whole book, write it"
  reader = LineReader(filename)
  book = Book()
  book.parsecontents(reader)
  makedir(filename)
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
