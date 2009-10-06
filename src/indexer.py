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


class Indexer(eLyXerConverter):
  "Creates a TOC from an already processed eLyXer HTML output."

  layouts = NumberingConfig.layouts['ordered'] + NumberingConfig.layouts['unique']

  def index(self):
    "Create the index (TOC)."
    self.tocwriter = TOCWriter(self.writer)
    self.writer.write(LyxHeader().gethtml())
    while not self.reader.finished():
      line = self.reader.currentline()
      tag, part = self.readtag(line)
      if tag:
        Trace.message('Tag: ' + tag + ' for part ' + part)
        self.writecontents(tag, part)
      self.reader.nextline()
    self.writer.write(LyxFooter().gethtml())
    self.reader.close()
    self.writer.close()

  def readtag(self, line):
    "Read the tag and the part name, from something like:"
    """<tag class="part">."""
    if not line.startswith('<') or not line.endswith('>'):
      return None, None
    tag, attrmap = self.extracttag(line)
    if not tag or not 'class' in attrmap:
      return None, None
    type = attrmap['class']
    if not type in Indexer.layouts or TagConfig.layouts[type] != tag:
      return None, None
    return tag, type

  def writecontents(self, tag, part):
    "Write the whole contents for a part."
    self.tocwriter.indent(part)
    self.writer.write(['<' + tag + ' class="' + part + '">' + '\n'])
    contents = []
    self.reader.nextline()
    while not self.reader.currentline().startswith('</' + tag):
      line = self.reader.currentline()
      if line.startswith('<a'):
        self.rewritelink(line, part)
      self.reader.nextline()
    self.writer.write(contents)

  def rewritelink(self, line, part):
    "Rewrite the part anchor to a real link."
    return

  def extracttag(self, wholetag):
    "Read the tag and all attributes from the whole tag,"
    """something like <tag attr1="value1"...>."""
    attrmap = dict()
    if not wholetag.startswith('<') or not wholetag.endswith('>'):
      Trace.error('Invalid tag ' + wholetag)
      return None, None
    middle = wholetag[1:-1]
    if '>' in middle or '<' in middle or '/' in middle or '?' in middle:
      return None, None
    words = middle.split()
    tag = words[0]
    for word in words[1:]:
      bits = word.split('=')
      if len(bits) != 2:
        Trace.error('Invalid attribute ' + word)
        return tag, attrmap
      name = bits[0]
      if not bits[1].startswith('"') or not bits[1].endswith('"'):
        Trace.error('Invalid value ' + bits[1] + ' for attribute ' + name)
        return tag, attrmap
      attrmap[name] = bits[1][1:-1]
    return tag, attrmap

def convertdoc(args):
  "Read a whole document and write it"
  ioparser = InOutParser().parse(args)
  indexer = Indexer(ioparser)
  indexer.index()

def main():
  "Main function, called if invoked from the command line"
  args = list(sys.argv)
  del args[0]
  Options().parseoptions(args)
  convertdoc(args)

if __name__ == '__main__':
  main()

