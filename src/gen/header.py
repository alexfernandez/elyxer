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

from util.numbering import *
from parse.parser import *
from parse.headerparse import *
from out.output import *
from out.template import *
from gen.container import *


class LyXHeader(Container):
  "Reads the header, outputs the HTML header"

  indentstandard = False
  tocdepth = 10

  def __init__(self):
    self.contents = []
    self.parser = HeaderParser()
    self.output = HeaderOutput()
    self.parameters = dict()

  def process(self):
    "Find pdf title"
    DocumentTitle.pdftitle = self.getparameter('pdftitle')
    if self.getparameter('documentclass') in HeaderConfig.styles['article']:
      NumberGenerator.startinglevel = 1
    if self.getparameter('paragraphseparation') == 'indent':
      LyXHeader.indentstandard = True
    LyXHeader.tocdepth = self.getlevel('tocdepth')
    NumberGenerator.maxdepth = self.getlevel('secnumdepth')
    Translator.language = self.getparameter('language')
    return self

  def getparameter(self, configparam):
    "Get a parameter configured in HeaderConfig."
    key = HeaderConfig.parameters[configparam]
    if not key in self.parameters:
      return None
    return self.parameters[key]

  def getlevel(self, configparam):
    "Get a level read as a parameter from HeaderConfig."
    paramvalue = self.getparameter(configparam)
    if not paramvalue:
      return 0
    value = int(paramvalue)
    if NumberGenerator.startinglevel == 1:
      return value
    return value + 1

class LyXFooter(Container):
  "Reads the footer, outputs the HTML footer"

  def __init__(self):
    self.contents = []
    self.parser = BoundedDummy()
    self.output = FooterOutput()

