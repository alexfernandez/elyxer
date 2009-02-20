#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 27-01-2009
# Create the custom HTML version

import sys
import re
import codecs
import os.path
import subprocess
import Numeric
import array
sys.path.append('./bin')
from container import *
from trace import Trace

class HtmlFile(object):
  "HTML file out"

  def __init__(self, filename):
    Trace.debug('writing file ' + filename)
    self.file = codecs.open(filename, 'w', 'utf-8')

  def writebook(self, book, title):
    "Write a full book"
    try:
      self.init(title)
      for container in book.contents:
        html = container.gethtml()
        for line in html:
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
    self.file.write('<link rel="stylesheet" href="lyx.css" type="text/css" media="screen"/>\n')
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

class PreGrouping(object):
  "Preprocess groupings of elements"

  groupings = {'Enumerate':'Ordered', 'Itemize':'Unordered'}

  def isnext(self, element):
    "Check if the stage comes next"
    if not isinstance(element, Layout):
      return False
    if element.type not in PreGrouping.groupings.keys():
      return False
    return True

  def preprocess(self, list, index):
    "Replace a list of items with a grouping"
    element = list[index]
    grouping = Layout()
    grouping.type = PreGrouping.groupings[element.type]
    grouping.contents.append(element)
    list[index] = grouping
    while self.isnext(list[index + 1]):
      grouping.contents.append(list[index + 1])
      list.remove(list[index + 1])

class PreFloat(object):
  "Preprocess a float"

  def isnext(self, element):
    "Check if it is a float"
    return isinstance(element, Float)

  def preprocess(self, list, index):
    "Enclose in a float div"
    float = list[index]
    enclosing = HtmlTag()
    enclosing.tag = 'div class="float"'
    enclosing.contents = [float]
    list[index] = enclosing
    self.checkforimages(float, float)

  def checkforimages(self, container, float):
    "Check for images, set figure class"
    for element in container.contents:
      if isinstance(element, Image):
        element.figure = True
        float.extratag = ' style="width:' + str(element.width) + ';"'
      if isinstance(element, Container):
        self.checkforimages(element, float)

class PreImage(object):
  "Preprocess (convert) an image"

  def isnext(self, element):
    "Check if it is an image"
    return isinstance(element, Image)

  def preprocess(self, list, index):
    "Put images as a figure"
    image = list[index]
    origin = '../' + image.url
    image.destination = os.path.splitext(image.url)[0] + '.png'
    factor = 100
    if hasattr(image, 'figure') and image.figure:
      factor = 120
    self.convert(origin, image.destination, factor)
    image.width, image.height = self.getdimensions(image.destination)

  def convert(self, origin, destination, factor):
    "Convert an image to PNG"
    if not os.path.exists(origin):
      Trace.error('Error in image origin ' + origin)
      return
    if os.path.exists(destination) and os.path.getmtime(origin) <= os.path.getmtime(destination):
      # file has not changed; do not convert
      return
    dir = os.path.dirname(destination)
    if not os.path.exists(dir):
      os.makedirs(dir)
    Trace.debug('converting ' + origin + ' to ' + destination + ' with density ' + str(factor))
    subprocess.call('convert -density ' + str(factor) + ' ' + origin + ' ' + destination, shell=True)

  dimensions = dict()

  def getdimensions(self, filename):
    "Get the dimensions of a PNG image"
    if filename in PreImage.dimensions:
      return PreImage.dimensions[filename]
    pngfile = codecs.open(filename, 'rb')
    pngfile.seek(16)
    dimensions = array.array('l')
    dimensions.fromfile(pngfile, 2)
    dimensions.byteswap()
    pngfile.close()
    PreImage.dimensions[filename] = dimensions
    return dimensions

class PreFormula(object):
  "Preprocess a formula"

  def isnext(self, element):
    "Check if it is a formula"
    return isinstance(element, Formula)

  def preprocess(self, list, index):
    "Convert the formula to HTML"
    formula = list[index].formula
    original, result = self.convert(formula, 0)
    list[index].formula = result

  unmodified = ['.', '*', '-', '/']
  modified = {'\'':u'’'}
  commands = {'\\, ':' ', '\\%':'%', '\\prime':u'’', '\\times':u'×'}
  functions = {'\\mathsf':'span class="sans"', '\\mathbf':'b', '^':'sup'}
  
  def convert(self, text, index):
    "Convert a bit of text to HTML"
    processed = ''
    result = ''
    while index < len(text) and text[index] != '}':
      original, converted = self.convertchars(text, index)
      processed += original
      result += converted
      index += len(original)
    return processed, result

  def convertchars(self, text, index):
    "Convert one or more characters, return the conversion"
    char = text[index]
    if char.isalpha():
      alpha = self.readalpha(text, index)
      return alpha, '<i>' + alpha + '</i>'
    if char.isdigit() or char in PreFormula.unmodified:
      return char, char
    if char in PreFormula.modified:
      return char, PreFormula.modified[char]
    command, result = self.find(text, index, PreFormula.commands)
    if command:
      return command, result
    function, result = self.find(text, index, PreFormula.functions)
    if not function:
      Trace.error('Unrecognized string in ' + text[index:])
      return '\\', '\\'
    index += len(function)
    if text[index] != '{':
      Trace.error('Missing {')
      return function, function
    index += 1
    original, converted = self.convert(text, index)
    index += len(original)
    if text[index] != '}':
      Trace.error('Missing }')
    html = HtmlTag()
    html.tag = result
    return function + '{' + original + '}', html.getopen() + converted + html.getclose()

  def readalpha(self, string, index):
    "Read alphabetic sequence"
    alpha = str()
    while index < len(string) and string[index].isalpha():
      alpha += string[index]
      index += 1
    return alpha

  def find(self, string, index, map):
    "Read TeX command or function"
    bit = string[index:]
    for element in map:
      if bit.startswith(element):
        return element, map[element]
    return None, None

class Preprocessor(object):
  "Preprocess a list of elements"

  stages = [PreGrouping(), PreImage(), PreFloat(), PreFormula()]

  def preprocess(self, list):
    "Preprocess a list of elements"
    i = 0
    while i < len((list)):
      element = list[i]
      if isinstance(element, Container):
        self.preprocess(element.contents)
      for stage in Preprocessor.stages:
        if stage.isnext(element):
          stage.preprocess(list, i)
      i += 1

class Book(object):
  "book in a lyx file"

  def __init__(self):
    self.contents = list()

  def parsecontents(self, reader):
    "Parse the contents of the reader"
    reader.nextline()
    while not reader.finished():
      container = ContainerFactory.createcontainer(reader)
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
  os.chdir(basedir)

def createbook(filename):
  "Read the whole book, write it"
  reader = LineReader(filename)
  book = Book()
  book.parsecontents(reader)
  makedir(filename)
  book.preprocess()
  book.show()
  book.writeresult()

Trace.debugmode = True
biblio = dict()
args = sys.argv
del args[0]
for arg in args:
  createbook(arg)

