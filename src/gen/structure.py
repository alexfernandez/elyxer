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
# Alex 20090312
# LyX structure in containers

from util.trace import Trace
from util.numbering import *
from parse.parser import *
from io.output import *
from gen.container import *


class LyXHeader(Container):
  "Reads the header, outputs the HTML header"

  indentstandard = False
  tocdepth = 10

  def __init__(self):
    self.contents = []
    self.parser = HeaderParser()
    self.output = HeaderOutput()

  def process(self):
    "Find pdf title"
    TitleOutput.pdftitle = self.getparameter('pdftitle')
    if self.getparameter('documentclass') in HeaderConfig.styles['article']:
      NumberGenerator.startinglevel = 1
    if self.getparameter('paragraphseparation') == 'indent':
      LyXHeader.indentstandard = True
    LyXHeader.tocdepth = self.getlevel('tocdepth')
    Trace.debug('TOC depth: ' + unicode(LyXHeader.tocdepth))
    NumberGenerator.maxdepth = self.getlevel('secnumdepth')
    Trace.debug('Max depth: ' + unicode(NumberGenerator.maxdepth))

  def getparameter(self, configparam):
    "Get a parameter configured in HeaderConfig."
    key = HeaderConfig.parameters[configparam]
    if not key in self.parameters:
      return None
    return self.parameters[key]

  def getlevel(self, configparam):
    "Get a level read as a parameter from HeaderConfig."
    value = int(self.getparameter(configparam))
    if NumberGenerator.startinglevel == 1:
      return value
    return value + 1

class LyXFooter(Container):
  "Reads the footer, outputs the HTML footer"

  def __init__(self):
    self.contents = []
    self.parser = BoundedDummy()
    self.output = FooterOutput()

class Align(Container):
  "Bit of aligned text"

  def __init__(self):
    self.parser = ExcludingParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.output.tag = 'div class="' + self.header[1] + '"'

class Newline(Container):
  "A newline"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.html = ['<br/>\n']

class NewPage(Newline):
  "A new page"

  def process(self):
    "Process contents"
    self.html = ['<p><br/>\n</p>\n']

class Appendix(Container):
  "An appendix to the main document"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class ListItem(Container):
  "An element in a list"

  def __init__(self):
    "Output should be empty until the postprocessor can group items"
    self.contents = list()
    self.parser = BoundedParser()
    self.output = EmptyOutput()

  def process(self):
    "Set the correct type and contents."
    self.type = self.header[1]
    tag = TaggedText().complete(self.contents, 'li', True)
    self.contents = [tag]

  def __unicode__(self):
    return self.type + ' item @ ' + unicode(self.begin)

class DeeperList(Container):
  "A nested list"

  def __init__(self):
    "Output should be empty until the postprocessor can group items"
    self.parser = BoundedParser()
    self.output = EmptyOutput()

  def process(self):
    "Create the deeper list"
    if len(self.contents) == 0:
      Trace.error('Empty deeper list')
      return

  def __unicode__(self):
    result = 'deeper list @ ' + unicode(self.begin) + ': ['
    for element in self.contents:
      result += unicode(element) + ', '
    return result[:-2] + ']'

class ERT(Container):
  "Evil Red Text"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

