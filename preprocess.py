#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090127
# Generate custom HTML version from Lyx document
# Preprocessor code

import sys
import os.path
import array
import subprocess
sys.path.append('./elyxer')
from container import *
from table import *
from link import *
from trace import Trace
from formula import Formula
import urlparse
import httplib
from threading import Thread


class PreStage(object):
  "Stage of preprocessing"

  def restyle(self, contents, type, restyler):
    "Restyle contents"
    i = 0
    while i < len(contents):
      element = contents[i]
      if isinstance(element, Container):
        self.restyle(element.contents, type, restyler)
      if isinstance(element, type):
        restyler(contents, i)
      i += 1

  def group(self, contents, index, group, isingroup):
    "Group some adjoining elements into a group"
    if hasattr(contents[index], 'grouped'):
      return
    while index < len(contents) and isingroup(contents[index]):
      contents[index].grouped = True
      group.contents.append(contents[index])
      contents.pop(index)
    contents.insert(index, group)

  def remove(self, contents, index):
    "Remove a container but leave its contents"
    container = contents[index]
    contents.pop(index)
    while len(container.contents) > 0:
      contents.insert(index, container.contents.pop())

class PreLayout(PreStage):
  "Preprocess a layout"

  processedclass = Layout

  groupings = {'Enumerate':'ol', 'Itemize':'ul'}

  def preprocess(self, contents, index):
    "Replace a set of items with a grouping"
    layout = contents[index]
    type = layout.type
    if type in PreLayout.groupings.keys():
      group = TaggedText().complete([], PreLayout.groupings[type])
      self.group(contents, index, group, lambda x: self.istype(x, type))
    if type == 'Standard':
      if self.nottext(contents[index]):
        self.remove(contents, index)

  def istype(self, element, type):
    "Check if the element has the right type"
    if not isinstance(element, Layout):
      return False
    return element.type == type

  def nottext(self, container):
    "Find out if the contents are not all text"
    for element in container.contents:
      if not self.istext(element):
        return True
      return False

  def istext(self, element):
    "Find out if the element is all text"
    if element.__class__ in [StringContainer, Formula]:
      return True
    return False

class PreFloat(PreStage):
  "Preprocess a float"

  processedclass = Float

  def preprocess(self, contents, index):
    "Enclose in a float div"
    float = contents[index]
    enclosing = TaggedText().complete([], 'div class="float"', True)
    self.group(contents, index, enclosing, lambda x: isinstance(x, Float))
    if float.type == 'figure':
      self.restyle(float.contents, Image, self.setfigure)

  def setfigure(self, contents, index):
    "Set the image as figure"
    contents[index].figure = True

class PreImage(PreStage):
  "Preprocess (convert) an image"

  processedclass = Image

  def preprocess(self, contents, index):
    "Put images as a figure"
    image = contents[index]
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
    Trace.message('Converting ' + origin + ' to ' + destination + ' with density ' + str(factor))
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

  def preprocess(self, contents, index):
    "Make style changes to the formula"
    formula = contents[index]
    self.restyle(formula.contents, TaggedText, self.restyletagged)

  def restyletagged(self, contents, index):
    "Restyle tagged text"
    tagged = contents[index]
    if tagged.tag == 'span class="mathsf"':
      self.restyle(tagged.contents, TaggedText, self.removeitalics)
      first = tagged.contents[0]
      if self.mustspaceunits(contents, index):
        first.contents[0] = u' ' + first.contents[0]
    elif tagged.tag == 'span class="sqrt"':
      tagged.tag = 'span class="root"'
      radical = TaggedText().constant(u'√', 'span class="radical"')
      contents.insert(index, radical)
    elif tagged.tag == 'span class="overdot"':
      dot = TaggedText().constant(u'⋅', 'span class="dot"')
      tagged.tag = 'span class="dotted"'
      #contents[index] = tagged.contents[0]
      contents.insert(index, dot)
    elif tagged.tag == 'i':
      group = TaggedText().complete([], 'i')
      self.group(contents, index, group, self.isalpha)
      self.restyle(group.contents, TaggedText, self.removeitalics)

  def removeitalics(self, contents, index):
    "Remove italics tag"
    if contents[index].tag == 'i':
      self.remove(contents, index)

  def isalpha(self, element):
    "Check if the element is all text"
    if isinstance(element, StringContainer):
      return element.contents[0].isalpha()
    for item in element.contents:
      if not self.isalpha(item):
        return False
    return True

  def mustspaceunits(self, contents, index):
    "Check if units must be spaced"
    if index == 0:
      return False
    first = contents[index].contents[0]
    if not isinstance(first, Constant):
      return False
    last = contents[index - 1]
    if isinstance(last, Constant):
      string = last.contents[-1]
      if string[-1].isdigit():
        return True
    return False

class PreConstant(PreStage):
  "Preprocess a constant"

  processedclass = Constant

  bigsymbols = [u'∫', u'∑']

  def preprocess(self, contents, index):
    "Look for a constant value"
    if not self.isbigsymbol(contents[index]):
      return
    group = TaggedText().complete([], 'span class="bigsymbol"')
    self.group(contents, index, group, self.insidebigsymbol)

  def isbigsymbol(self, element):
    "Find if we are looking at a big symbol"
    if not isinstance(element, Constant):
      return False
    return element.contents[0] in PreConstant.bigsymbols

  def insidebigsymbol(self, element):
    "Check if big symbol or related limit"
    if self.isbigsymbol(element):
      return True
    if isinstance(element, TaggedText):
      if element.tag == 'sub' or element.tag == 'sup':
        element.tag += ' class="bigsymbol"'
        return True
    return False

class PreTableCell(PreStage):
  "Preprocess a table cell"

  processedclass = Cell

  def preprocess(self, contents, index):
    "Group multicolumn cells, restyle"
    cell = contents[index]
    self.restyle(cell.contents, Layout, self.removestandard)
    self.align(cell)
    width = 1
    mc = self.multicolumn(contents, index)
    if mc != 1:
      if mc == 2:
        Trace.error('Unbound multicolumn value of 2')
      return width
    while self.multicolumn(contents, index + 1) == 2:
      contents.pop(index + 1)
      width += 1
    cell.tag += ' colspan="' + str(width) + '"'

  def removestandard(self, contents, index):
    "Remove a standard layout"
    if contents[index].type == 'Standard':
      self.remove(contents, index)

  def multicolumn(self, contents, index):
    "Get the multicolumn attribute"
    if len(contents) <= index:
      return None
    cell = contents[index]
    if len(cell.header) < 2:
      return None
    mc = cell.header[1]
    if not mc.startswith('multicolumn'):
      return None
    return int(mc.split('"')[1])

  def align(self, cell):
    "Align the cell according to its contents"
    if self.isempty(cell.contents):
      cell.tag += ' class="empty"'
    elif self.isnumeric(cell.contents[0]):
      cell.tag += ' class="numeric"'

  def isempty(self, contents):
    "Find out if the contents are empty"
    if len(contents) == 0:
      return True
    if len(contents) > 1:
      return False
    first = contents[0]
    if first == '-':
      return True
    if hasattr(first, 'contents'):
      return self.isempty(first.contents)
    return False

  def isnumeric(self, contained):
    "Find out if the text contained is numeric"
    if isinstance(contained, StringContainer):
      string = contained.contents[0]
      return string[0].isdigit()
    if not isinstance(contained, Container):
      return False
    firstpart = contained.contents[0]
    return self.isnumeric(firstpart)

class PreBiblio(PreStage):
  "Preprocess a complete bibliography"

  processedclass = Bibliography

  def preprocess(self, contents, index):
    "Group all entries in a div with a header"
    header = TaggedText().constant(u'Bibliografía', 'h2')
    group = TaggedText().complete([header], 'div class="biblio"', True)
    self.group(contents, index, group, lambda x: isinstance(x, Bibliography))

class PreURL(PreStage):
  "Preprocess a URL"

  processedclass = URL

  def preprocess(self, contents, index):
    "Check a URL"
    checker = URLChecker(contents[index].name)
    checker.start()

class URLChecker(Thread):
  "A threaded URL checker"

  def __init__(self, url):
    Thread.__init__(self)
    self.url = url
    self.valid = False
    self.finished = False

  def run(self):
    "Check that the URL is working"
    Trace.message('Accessing ' + self.url)
    host = urlparse.urlparse(self.url).netloc
    con = httplib.HTTPConnection(host)
    con.request('GET', self.url)
    res = con.getresponse()
    res.read()
    if res.status == 200:
      self.valid = True
    else:
      Trace.error('URL ' + self.url + ' not found: ' + str(res.status))
    self.finished = True

class Preprocessor(object):
  "Preprocess a list of elements"

  stages = [PreLayout(), PreImage(), PreFloat(), PreFormula(),
      PreConstant(), PreTableCell(), PreBiblio()]

  stagedict = dict([(x.processedclass, x) for x in stages])

  def preprocess(self, list):
    "Preprocess a list of elements"
    i = 0
    preprocessed = 0
    while i < len(list):
      if isinstance(list[i], Container):
        preprocessed += self.preprocess(list[i].contents)
      preprocessed += self.preprocessitem(list, i)
      i += 1
    return preprocessed

  def preprocessitem(self, contents, index):
    "Preprocess an element recursively"
    if index >= len(contents):
      return 0
    if hasattr(contents[index], 'processed'):
      return 0
    element = contents[index]
    if not element.__class__ in Preprocessor.stagedict:
      return 0
    Preprocessor.stagedict[element.__class__].preprocess(contents, index)
    element.processed = True
    return 1

