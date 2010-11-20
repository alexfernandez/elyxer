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

from util.docparams import *
from parse.parser import *
from parse.headerparse import *
from out.output import *
from out.template import *
from gen.container import *
from ref.partkey import *
from maths.command import *
from maths.macro import *
from gen.notes import *


class LyXHeader(Container):
  "Reads the header, outputs the HTML header"

  def __init__(self):
    self.contents = []
    self.parser = HeaderParser()
    self.output = HeaderOutput()
    self.parameters = dict()
    self.partkey = PartKey().createheader('header')

  def process(self):
    "Find pdf title"
    DocumentParameters.pdftitle = self.getheaderparameter('pdftitle')
    documentclass = self.getheaderparameter('documentclass')
    if documentclass in HeaderConfig.styles['article']:
      DocumentParameters.startinglevel = 1
    if documentclass in HeaderConfig.styles['book']:
      DocumentParameters.bibliography = 'bibliography'
    else:
      DocumentParameters.bibliography = 'references'
    if self.getheaderparameter('paragraphseparation') == 'indent':
      DocumentParameters.indentstandard = True
    DocumentParameters.tocdepth = self.getlevel('tocdepth')
    DocumentParameters.maxdepth = self.getlevel('secnumdepth')
    DocumentParameters.language = self.getheaderparameter('language')
    if self.getheaderparameter('outputchanges') == 'true':
      DocumentParameters.outputchanges = True
    return self

  def getheaderparameter(self, configparam):
    "Get a parameter configured in HeaderConfig."
    key = HeaderConfig.parameters[configparam]
    if not key in self.parameters:
      return None
    return self.parameters[key]

  def getlevel(self, configparam):
    "Get a level read as a parameter from HeaderConfig."
    paramvalue = self.getheaderparameter(configparam)
    if not paramvalue:
      return 0
    value = int(paramvalue)
    if DocumentParameters.startinglevel == 1:
      return value
    return value + 1

class LyXPreamble(Container):
  "The preamble at the beginning of a LyX file. Parsed for macros."

  def __init__(self):
    self.parser = PreambleParser()
    self.output = EmptyOutput()

  def process(self):
    "Parse the LyX preamble, if needed."
    if len(PreambleParser.preamble) == 0:
      return
    pos = TextPosition('\n'.join(PreambleParser.preamble))
    while not pos.finished():
      if self.detectfunction(pos):
        self.parsefunction(pos)
      else:
        pos.globincluding('\n')
    PreambleParser.preamble = []

  def detectfunction(self, pos):
    "Detect a macro definition or a preamble function."
    for function in FormulaConfig.definingfunctions:
      if pos.checkfor(function):
        return True
    for function in FormulaConfig.preamblefunctions:
      if pos.checkfor(function):
        return True
    return False

  def parsefunction(self, pos):
    "Parse a macro definition or a preamble function."
    command = FormulaFactory().parsetype(FormulaCommand, pos)
    if not isinstance(command, DefiningFunction) and not isinstance(command, PreambleFunction):
      Trace.error('Did not define a macro with ' + unicode(command))

class LyXFooter(Container):
  "Reads the footer, outputs the HTML footer"

  def __init__(self):
    self.contents = []
    self.parser = BoundedDummy()
    self.output = FooterOutput()
    self.partkey = PartKey().createheader('footer')

  def process(self):
    "Include any footnotes at the end."
    if EndFootnotes.footnotes:
      endnotes = EndFootnotes()
      self.contents = [endnotes]

class PreambleFunction(ParameterFunction):
  "A function which is used in the preamble to perform some operation."

  commandmap = FormulaConfig.preamblefunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    template = self.translated[0]
    self.readparams(template, pos)
    operation = self.translated[1]
    operate = getattr(self, operation)
    operate()

  def setcounter(self):
    "Set a global counter."
    counter = self.getliteralvalue('$p')
    value = self.getintvalue('$n')
    Trace.debug('Setting counter ' + unicode(counter) + ' to ' + unicode(value))
    NumberGenerator.generator.getcounter(counter).init(value)

FormulaCommand.types += [PreambleFunction]

