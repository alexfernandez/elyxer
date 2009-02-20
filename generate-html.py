#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 27-01-2009
# Generate custom HTML version from Lyx document
# Main file and preprocessor

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
    Trace.debug('Writing file ' + filename)
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

class PreStage(object):
  "Stage of preprocessing"

  def isnext(self, element):
    "Check if it is the given class"
    return isinstance(element, self.processedclass)

class PreGrouping(PreStage):
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
    grouping.tag = Layout.typetags[grouping.type]
    grouping.contents = [element]
    list[index] = grouping
    while self.isnext(list[index + 1]):
      grouping.contents.append(list[index + 1])
      list.remove(list[index + 1])

class PreFloat(PreStage):
  "Preprocess a float"

  processedclass = Float

  def preprocess(self, list, index):
    "Enclose in a float div"
    float = list[index]
    enclosing = Layout()
    enclosing.tag = 'div class="float"'
    enclosing.contents = [float]
    list[index] = enclosing
    self.checkforimages(float, float)

  def checkforimages(self, container, float):
    "Check for images, set figure class"
    for element in container.contents:
      if isinstance(element, Image):
        element.figure = True
      if isinstance(element, Container):
        self.checkforimages(element, float)

class PreAlign(PreStage):
  "Preprocess an aligned layout"

  def isnext(self, element):
    "Check if it is a layout"
    if not isinstance(element, Layout):
      return False
    if len(element.contents) == 0:
      return False
    first = element.contents[0]
    return isinstance(first, Align)

  def preprocess(self, list, index):
    "Center the layout"
    list[index].type = 'Center'

class PreImage(PreStage):
  "Preprocess (convert) an image"

  processedclass = Image

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

class PreFormula(PreStage):
  "Preprocess a formula"

  processedclass = Formula

  def preprocess(self, list, index):
    "Convert the formula to HTML"
    formula = list[index]
    original, result = self.convert(formula.contents[0], 0)
    #Trace.debug('Formula ' + original + ' -> ' + result)
    container = StringContainer()
    container.contents = [result]
    formula.contents = [container]

  unmodified = ['.', '*', '-', '/', u'€', '+', '(', ')']
  modified = {'\'':u'’', '=':' = '}
  commands = {'\\, ':' ', '\\%':'%', '\\prime':u'’', '\\times':u'×',
      '\\rightarrow ':u'→', '\\lambda':u'λ', '\\propto ':u'∝',
      '\\tilde{n}':u'ñ', '\\cdot ':u'·', '\\approx':u'≈',
      '\\rightsquigarrow ':u'⇝', '\\dashrightarrow':'⇢', '\\sim':u'~'}
  onefunctions = {'\\mathsf':'span class="sans"', '\\mathbf':'b', '^':'sup',
      '_':'sub', '\\underline':'u', '\\overline':'span class="overline"'}
  twofunctions = {
      '\\frac':['div class="frac"', 'span class="fracup"', 'span class="fracdown"']}
  
  def convert(self, text, pos):
    "Convert a bit of text to HTML"
    processed = ''
    result = ''
    while pos < len(text) and text[pos] != '}':
      original, converted = self.convertchars(text, pos)
      #Trace.debug('converted: ' + unicode(converted))
      processed += original
      pos += len(original)
      result += converted
    return processed, result

  def convertchars(self, text, pos):
    "Convert one or more characters, return the conversion"
    #Trace.debug('Formula ' + text + ' @' + str(pos))
    char = text[pos]
    if char.isalpha():
      alpha = self.readalpha(text, pos)
      return alpha, '<i>' + alpha + '</i>'
    if char.isdigit() or char in PreFormula.unmodified:
      return char, char
    if char in PreFormula.modified:
      return char, PreFormula.modified[char]
    command, result = self.find(text, pos, PreFormula.commands)
    if command:
      return command, result
    onefunction, result = self.readone(text, pos)
    if onefunction:
      return onefunction, result
    twofunction, result = self.readtwo(text, pos)
    if twofunction:
      return twofunction, result
    Trace.error('Unrecognized string in ' + unicode(text[pos:]))
    return '\\', '\\'

  def readone(self, text, pos):
    "read a one-parameter function"
    function, result = self.find(text, pos, PreFormula.onefunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket, parameter = self.readbracket(text, pos)
    return function + bracket, self.createtag(result, parameter)

  def readtwo(self, text, pos):
    "read a two-parameter function"
    function, result = self.find(text, pos, PreFormula.twofunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket1, parameter1 = self.readbracket(text, pos)
    pos += len(bracket1)
    bracket2, parameter2 = self.readbracket(text, pos)
    original =  function + bracket1 + bracket2
    tag1 = self.createtag(result[1], parameter1)
    tag2 = self.createtag(result[2], parameter2)
    result = self.createtag(result[0], tag1 + tag2)
    return original, result

  def createtag(self, tag, text):
    "Create a custom tag"
    output = TagOutput()
    container = Container()
    container.tag = tag
    container.breaklines = False
    return output.getopen(container) + text + output.getclose(container)

  def readbracket(self, text, pos):
    "Read a bracket as {result}"
    if text[pos] != u'{':
      Trace.error(u'Missing { in ' + text + '@' + str(pos))
      return '', ''
    pos += 1
    original, converted = self.convert(text, pos)
    pos += len(original)
    if text[pos] != u'}':
      Trace.error(u'Missing } in ' + text + '@' + str(pos))
    return '{' + original + '}', converted

  def readalpha(self, text, pos):
    "Read alphabetic sequence"
    alpha = str()
    while pos < len(text) and text[pos].isalpha():
      alpha += text[pos]
      pos += 1
    return alpha

  def find(self, text, pos, map):
    "Read TeX command or function"
    bit = text[pos:]
    for element in map:
      if bit.startswith(element):
        return element, map[element]
    return None, None

class Preprocessor(object):
  "Preprocess a list of elements"

  stages = [PreGrouping(), PreImage(), PreFloat(), PreFormula(), PreAlign()]

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

