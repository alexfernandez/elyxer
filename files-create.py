#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 27-01-2009
# Create the custom HTML version

import sys
import re
import codecs
import os.path
import subprocess

class Entry:
  "entry in bibliography"

  def __init__(self):
    self.key = ""
    self.text = list()

  def addtext(self, line):
    self.text.append(line)

  def write(self, file):
    for line in self.text:
      file.write(line)

class HtmlFactory(object):
  "Creates the necessary HTML converters"

  def getconverter(object):
    "Get the HTML converter for an object"
    if isinstance(object, basestring):
      return HtmlString(object)
    elif isinstance(object, StringContainer):
      return HtmlString(object.contents[0])
    elif isinstance(object, StyledText):
      styletags = { 'emph':'i', 'noun':'span style="font-variant: small-caps;"' }
      tag = styletags[object.type]
      return HtmlTagConverter(tag, object)
    elif isinstance(object, Layout):
      layouttags = { 'Quote':'blockquote', 'Standard':'p', 'Title':'h1', 'Author':'h2',
          'Subsubsection*':'h4', 'Enumerate':'li', 'Chapter':'h1', 'Section':'h2', 'Subsection': 'h3',
          'Bibliography':'p style="font-size: -1;"' }
      tag = layouttags[object.type]
      return HtmlTagConverter(tag, object)
    elif isinstance(object, Image):
      return HtmlImage(object)
    else:
      print 'Error with ' + str(object)

  getconverter = staticmethod(getconverter)

class HtmlString(object):
  "A string converter to HTML"

  def __init__(self, string):
    self.string = string

  def gethtml(self):
    "Get the HTML output of the converter as a list"
    return [self.string]

class HtmlImage(object):
  "An image converter to HTML"

  def __init__(self, image):
    self.image = image

  def gethtml(self):
    "Get the HTML output of the image as a list"
    origin = '../' + self.image.url
    destination = os.path.splitext(self.image.url)[0] + '.png'
    if not os.path.exists(origin):
      print 'error in image origin ' + origin
      return
    if not os.path.exists(destination):
      # new file; convert
      self.convert(origin, destination)
    elif os.path.getmtime(origin) > os.path.getmtime(destination):
      # file changed; convert again
      self.convert(origin, destination)
    return ['<img src="' + destination + '" alt="' + os.path.basename(destination) + '" />\n']

  def convert(self, origin, destination):
    "Convert an image to PNG"
    dir = os.path.dirname(destination)
    if not os.path.exists(dir):
      os.makedirs(dir)
    if debug:
      print 'converting ' + origin + ' to ' + destination
    subprocess.call('convert -density 100 ' + origin + ' ' + destination, shell=True)

class HtmlQuote(object):
  "A quote converter"

  def __init__(self, quote):
    self.quote = quote

  def gethtml(self):
    "Get the HTML output for the quote"
    return "“" + "”"

class HtmlTagConverter(object):
  "Converter from a kind of object to a tag in HTML"

  def __init__(self, tag, container):
    self.tag = tag
    self.container = container

  def gethtml(self):
    "Return the complete HTML text"
    html = [self.getopen()]
    for object in self.container.contents:
      converter = HtmlFactory.getconverter(object)
      html += converter.gethtml()
    html.append(self.getclose())
    return html

  def getopen(self):
    "Get opening line"
    return '<' + self.tag + '>\n'

  def getclose(self):
    "Get closing line"
    return '</' + self.tag.split()[0] + '>\n'

class HtmlFile(object):
  "HTML file out"

  def __init__(self, filename):
    if debug:
      print 'writing file ' + filename
    self.file = codecs.open(filename, 'w', 'utf-8')
    self.layouts = { 'Quote':['<blockquote>', '</blockquote>'], 'Standard':['<p>', '</p>'], 'Title':['<h1>', '</h1>'], 'Author':['<h2>', '</h2>'],
        'Subsubsection*':['<h3>', '</h3>'], 'Enumerate':['<ol>', '</ol>'] }
    self.insets = { 'Graphics':['<p>inset-graphics</p>', '<p>outset-graphics</p>'] }
    self.queue = list()

  def writebook(self, book, title):
    "Write a full book"
    try:
      self.init(title)
      for container in book.contents:
        converter = HtmlFactory.getconverter(container)
        html = converter.gethtml()
        for line in html:
          self.file.write(line)
      self.end()
    finally:
      self.file.close()

  def writepart(self, part):
    "Write a part"
    try:
      self.init(part)
      for line in part.text:
        self.writeline(line)
      #for key in self.keys:
      #  self.biblio[key].write(file)
      self.separator()
      for subpart in part.parts:
        self.link(subpart)
      self.end()
    finally:
      self.file.close()

  def init(self, title):
    "HTML preamble"
    self.file.write('<?xml version="1.0" encoding="UTF-8"?>')
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
    self.file.write('<h1>' + title + '</h1>\n')

  def separator(self):
    self.file.write('<hr>\n')

  def writeline(self, line):
    if line.startswith('\\begin_layout'):
      layouttype = line.split()[1]
      layout = self.layouts[layouttype]
      self.file.write(layout[0])
      self.queue.append(layout[1])
    elif line.startswith('\\end_layout'):
      self.file.write(self.queue.pop())
    else:
      self.file.write(line)

  def link(self, part):
    "Create a link to a part"
    self.file.write('<p><a href="' + part.getfilename(basedir) + '">' + part.gettitle() + '</a></p>\n')

  def end(self):
    self.separator()
    self.file.write(u'<p class="bottom">(C) 2009 Alex Fernández</p>\n')
    self.file.write('</div>\n')
    self.file.write('</body>\n')

  def close(self):
    self.end()
    self.file.close()

class LineReader:
  "Reads a file line by line"

  def __init__(self, arg):
    self.contents = list()
    self.index = 0
    self.readfile(arg)

  def readfile(self, filename):
    file = codecs.open(filename, 'r', "utf-8")
    try:
      self.contents = file.readlines()
    finally:
      file.close()

  def currentline(self):
    return self.contents[self.index]

  def nextline(self):
    "Go to next line"
    self.index += 1

  def finished(self):
    return self.index >= len(self.contents)

class ContainerFactory:
  "Creates containers depending on the first line"

  def createcontainer(reader):
    "Get the container corresponding to the reader contents"
    containerlist = [Layout, StyledText, Image, StringContainer]
    for type in containerlist:
      if type.comesnext(reader):
        container = type.__new__(type, reader)
        container.__init__(reader)
        return container
    print 'error en ' + reader.currentline()

  createcontainer = staticmethod(createcontainer)

class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  def parse(self, reader):
    "Parse the contents of the container"
    # skip first line
    reader.nextline()
    while not self.finished(reader):
      container = ContainerFactory.createcontainer(reader)
      container.parse(reader)
      self.contents.append(container)
    # skip last line
    reader.nextline()

  def finished(self, reader):
    if self.getendingline() and reader.currentline().startswith(self.getendingline()):
      return True
    return False

class StringContainer(Container):
  "A container for a single string"

  def __init__(self, reader):
    Container.__init__(self)

  def parse(self, reader):
    "Read the single line"
    self.contents.append(reader.currentline())
    reader.nextline()

  def comesnext(reader):
    "Return if the next line is a string, always true"
    return True

  comesnext = staticmethod(comesnext)

class Image(Container):
  "An embedded image"

  def __init__(self, reader):
    Container.__init__(self)
    reader.nextline()
    self.url = reader.currentline().split()[1]

  def comesnext(reader):
    "Return if the next line has an image"
    return reader.currentline().startswith('\\begin_inset Graphics')

  comesnext = staticmethod(comesnext)

  def getendingline(self):
    return '\\end_inset'

class StyledText(Container):
  "A bit of styled text"

  def __init__(self, reader):
    Container.__init__(self)
    self.type = reader.currentline().split()[0].strip('\\')

  def comesnext(reader):
    "Return if the next line is a style"
    line = reader.currentline()
    if not line.startswith('\\'):
      return False
    split = line.split()
    if len(split) < 2:
      return False
    return line.split()[1] == 'on'

  comesnext = staticmethod(comesnext)

  def getendingline(self):
    return '\\' + self.type + ' default'

class Layout(Container):
  "A layout (block of text) inside a lyx file"

  def __init__(self, reader):
    Container.__init__(self)
    self.type = reader.currentline().split()[1]

  def comesnext(reader):
    "Return if the next line has a layout"
    return reader.currentline().startswith('\\begin_layout ')

  comesnext = staticmethod(comesnext)

  def getendingline(self):
    return '\\end_layout'

class Part(object):
  "Any part of a lyx file"

  def __init__(self, type):
    Layout.__init__(self, type)
    self.keys = list()
    self.parts = list()
    self.number = list()
    self.name = ''
    self.label = None

  def addkey(self, keylist):
    keys = keylist.split(',')
    for key in keys:
      if not key in self.keys:
        self.keys.append(key)

  def parsetext(self, reader):
    while not self.finished(reader):
      self.parseline(reader)

  def finished(self, reader):
    if self.getendingline() and reader.currentline().startswith(self.getendingline()):
      return True
    return False

  def parsesubpart(self, reader):
    part = self.createsubpart()
    self.parts.append(part)
    part.number = self.number + [len(self.parts)]
    reader.nextline()
    part.name = reader.currentline().strip()
    if debug:
      print part.composenumber(part.__class__.__name__ + ' ', '-') + ': ' + part.name
    while not reader.currentline().startswith('\\end_layout'):
      if reader.currentline().startswith('\\begin_inset LatexCommand label'):
        # read label
        reader.nextline()
        part.label = reader.currentline().split('\"')[1]
        if debug:
          print 'Label: ' + part.label
      reader.nextline()
    reader.nextline()
    part.parsetext(reader)

  def parseline(self, reader):
    line = reader.currentline()
    if self.getsubpartline() and line.startswith(self.getsubpartline()):
      self.parsesubpart(reader)
    elif line.startswith('key \"'):
      self.parsekey(reader)
    elif line.startswith('\\begin_layout Bibliography'):
      self.parseentry(reader)
    else:
      self.readline(reader)

  def parsekey(self, reader):
    line = reader.currentline()
    key = line.split('\"')[1]
    self.addkey(key)
    reader.nextline()

  def parseentry(self, reader):
    entry = Entry()
    line = reader.currentline()
    while not line.startswith('\\end_layout'):
      entry.addtext(line)
      if line.startswith('key \"'):
        entry.key = line.split('\"')[1]
      reader.nextline()
      line = reader.currentline()
    entry.addtext(line)
    biblio[entry.key] = entry
    reader.nextline()

  def readline(self, reader):
    self.text.append(reader.currentline())
    reader.nextline()

  def write(self):
    file = HtmlFile(self)
    file.writepart(self)
    for part in self.parts:
      part.write()

  def composenumber(self, base, separator):
    "compose the number with the given separator, as in Chapter 10-4-8"
    name = base
    if self.number:
      for bit in self.number:
        name += str(bit) + separator
    return name.rstrip(separator)

  def createsubpart(self):
    "create a subpart"
    return None

  def gettitle(self):
    return self.composenumber(self.__class__.__name__ + ' ', '.') + ': ' + self.name

  def getfilename(self):
    "get the filename to use"
    return self.composenumber(basedir + '-', '-') + '.html'

  def getendingline(self):
    "get the last line of the part"
    return None

  def getsubpartline(self):
    "get the line that will start a subpart"
    return None

class Subsection(Part):
  "Subsection in a lyx file"

  def __init__(self):
    Part.__init__(self, 'Subsection')

  def getendingline(self):
    "Get the last line of the part"
    return '\\begin_layout Subsection'

  def createsubpart(self):
    "create a subpart"
    return None

class Section(Part):
  "Section in a lyx file"

  def __init__(self):
    Part.__init__(self, 'Section')

  def getendingline(self):
    "get the last line of the part"
    return '\\begin_layout Section'

  def getsubpartline(self):
    "get the line that will start a subpart"
    return 'tantariroriro'

  def getsubpartline(self):
    "get the line that will start a subpart"
    return '\\begin_layout Subsection'

  def createsubpart(self):
    "create a subpart"
    return Subsection()

class Chapter(Part):
  "chapter in a lyx file"

  def __init__(self):
    Part.__init__(self, 'Chapter')

  def getendingline(self):
    "get the last line of the part"
    return '\\begin_layout Chapter'

  def getsubpartline(self):
    "get the line that will start a subpart"
    return '\\begin_layout Section'

  def createsubpart(self):
    "create a subpart"
    return Section()

class Book(object):
  "book in a lyx file"

  def __init__(self):
    self.contents = list()

  def parsecontents(self, reader):
    "Parse the contents of the reader"
    while not reader.finished():
      container = ContainerFactory.createcontainer(reader)
      container.parse(reader)
      self.contents.append(container)

  def getendingline(self):
    "Get the last line of the part"
    return '\\end_body'

  def getsubpartline(self):
    "Get the line that will start a subpart"
    return '\\begin_layout Chapter'

  def createsubpart(self):
    "Create a subpart"
    return Chapter()

  def show(self):
    if debug:
      # print 'book has ' + str(len(self.parts)) + ' chapters'
      print 'book has ' + str(len(self.contents)) + ' layouts'

  def writeresult(self):
    try:
      os.mkdir(basedir)
    except:
      pass
    os.chdir(basedir)
    file = HtmlFile('book.html')
    file.writebook(self, 'El libro gordo')

debug = True
biblio = dict()
args = sys.argv
del args[0]
for arg in args:
  reader = LineReader(arg)
  book = Book()
  book.parsecontents(reader)
  book.show()
  basedir = os.path.splitext(arg)[0]
  book.writeresult()

