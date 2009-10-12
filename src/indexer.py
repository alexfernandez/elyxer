#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   eLyXer -- convert LyX source files to HTML output.
#
#   Copyright (C) 2009 Alex Fernández
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# --end--
# Alex 20091006
# eLyXer indexer: creates a TOC just like elyxer.py --toc
# http://www.nongnu.org/elyxer/


from io.convert import *
from util.trace import Trace
from util.options import *
from gen.structure import *


class HtmlTag(object):
  "Represents an HTML tag."

  def __init__(self):
    self.tag = None
    self.attrs = dict()
    self.contents = None

  def isopen(self, text):
    """Check if a text contains just an open tag: <tag attr="value"...>."""
    if not text.startswith('<') or not text.endswith('>'):
      return False
    middle = text[1:-1]
    if '>' in middle or '<' in middle or '/' in middle or '?' in middle:
      return False
    return True

  def hasopenclose(self, text):
    "Check if a text has both open and close tags: <tag...>contents</tag>"
    if text.count('<') != 2 or text.count('>') != 2:
      return False
    if text.find('<') > text.rfind('>'):
      return False
    middle = text[text.find('<') + 1 : text.rfind('>')]
    if middle.count('>') != 1 or middle.count('<') != 1 or middle.count('/') != 1:
      return False
    if middle.find('>') > middle.find('<'):
      return False
    if middle.find('<') > middle.find('/'):
      return False
    return True

  def parseopen(self, pos):
    """Parse the tag and all attributes, like <tag attr1="value1"...>."""
    pos.skipspace()
    if not pos.checkskip('<'):
      Trace.error('Invalid open tag at ' + pos.remaining())
      return
    pos.pushending('>')
    pos.skipspace()
    self.tag = pos.glob(lambda current: not current.isspace())
    pos.skipspace()
    while not pos.finished():
      name = pos.globexcluding('=')
      if not pos.checkskip('="'):
        Trace.error('Missing =" in attribute value ' + pos.remaining())
        return
      value = pos.globexcluding('"')
      if not pos.checkskip('"'):
        Trace.error('Missing closing " in attribute value ' + pos.remaining())
        return
      self.attrs[name] = value
    if not pos.checkskip('>'):
      Trace.error('Missing closing > in tag ' + pos.remaining())

  def parseopenclose(self, pos):
    "Parse an open and close tags, with contents in between:"
    """<tag attr1="value1"...>contents</tag>"""
    self.parseopen(pos)
    self.contents = pos.globexcluding('<')
    if not pos.checkskip('</'):
      Trace.error('Closing tag should start with "</": ' + pos.remaining())
      return
    pos.skipspace()
    if not pos.checkskip(self.tag):
      Trace.error('Tag open ' + self.tag + ' not closed ' + pos.remaining())
      return
    pos.skipspace()
    if not pos.checkskip('>'):
      Trace.error('Closed tag not closed by ">": ' + pos.remaining())
      return

class Indexer(eLyXerConverter):
  "Creates a TOC from an already processed eLyXer HTML output."

  ordered = NumberingConfig.layouts['ordered']
  unique = NumberingConfig.layouts['unique']

  def index(self):
    "Create the index (TOC)."
    self.tocwriter = TOCWriter(self.writer)
    while not self.reader.finished():
      self.processline(self.reader.currentline())
      self.reader.nextline()
    self.tocwriter.closeindent(self.tocwriter.depth)
    self.writer.write(LyxFooter().gethtml())
    self.reader.close()
    self.writer.close()

  def processline(self, line):
    "Process a line from inside the HTML document."
    title = self.readtitle(line)
    if title and not Options.title:
      Options.title = title
      self.writer.write(LyxHeader().gethtml())
      return
    type = self.readparttype(line)
    if type:
      self.writecontents(type)

  def readparttype(self, text):
    "Read the tag and the part name, from something like:"
    """<tag class="part">."""
    tag = HtmlTag()
    if not tag.isopen(text):
      return None
    tag.parseopen(Position(text))
    if not 'class' in tag.attrs:
      return None
    type = tag.attrs['class']
    if not type in Indexer.ordered + Indexer.unique:
      return None
    if TagConfig.layouts[type] != tag.tag:
      return None
    return type

  def readtitle(self, text):
    "Read the title from <title>contents</title>."
    if not text.startswith('<'):
      return None
    tag = HtmlTag()
    if not tag.hasopenclose(text):
      return None
    tag.parseopenclose(Position(text))
    return tag.contents

  def writecontents(self, type):
    "Write the whole contents for a part type."
    self.tocwriter.indent(type)
    contents = ''
    self.reader.nextline()
    ending = '</' + TagConfig.layouts[type]
    while not self.reader.currentline().startswith(ending):
      contents += self.reader.currentline() + '\n'
      self.reader.nextline()
    self.rewritelink(contents, type)

  def rewritelink(self, contents, type):
    "Rewrite the part anchor to a real link."
    tag = HtmlTag()
    if not tag.hasopenclose(contents):
      Trace.error('Anchor should open and close: ' + contents)
      return
    pos = Position(contents)
    tag.parseopenclose(pos)
    if tag.tag != 'a':
      Trace.error('Anchor should be <a...>: ' + contents)
      return
    if not 'class' in tag.attrs or tag.attrs['class'] != 'toc':
      Trace.error('Classless link in ' + contents)
      return
    number = tag.contents
    if type in Indexer.unique:
      number = number.split()[1].replace('.', '')
    title = pos.globexcluding('\n')
    self.tocwriter.createlink(type, number, title)

def convertdoc(args):
  "Read a whole document and write it"
  Options().parseoptions(args)
  ioparser = InOutParser().parse(args)
  if ioparser.parsedin:
    Options.toc = ioparser.filein
  else:
    Options.toc = ''
  indexer = Indexer(ioparser)
  indexer.index()

def main():
  "Main function, called if invoked from the command line"
  convertdoc(list(sys.argv))

if __name__ == '__main__':
  main()

