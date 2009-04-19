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
# Alex 20090324
# eLyXer postprocessor code

from gen.container import *
from util.trace import Trace
from gen.structure import *
from gen.layout import *
from ref.link import *
from post.postprocess import *


class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures"

  letters = '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  instance = None

  def __init__(self):
    self.startinglevel = 0
    self.number = []
    self.uniques = dict()
    self.chaptered = dict()

  def generateunique(self, type):
    "Generate a number to place in the title but not to append to others"
    if not type in self.uniques:
      self.uniques[type] = 0
    self.uniques[type] = self.increase(self.uniques[type])
    return type + ' ' + str(self.uniques[type]) + '.'

  def generate(self, level):
    "Generate a number in the given level"
    if self.number == [] and level == 1:
      self.startinglevel = 1
    level -= self.startinglevel
    if len(self.number) > level:
      self.number = self.number[:level + 1]
    else:
      while len(self.number) <= level:
        self.number.append(0)
    self.number[level] = self.increase(self.number[level])
    return self.dotseparated(self.number)

  def generatechaptered(self, type):
    "Generate a number which goes with first-level numbers"
    if not type in self.chaptered:
      self.chaptered[type] = [self.number[0], 0]
    chaptered = self.chaptered[type]
    chaptered[1] = self.increase(chaptered[1])
    return self.dotseparated(chaptered)

  def increase(self, number):
    "Increase the number (or letter)"
    if not isinstance(number, str):
      return number + 1
    if not number in NumberGenerator.letters:
      Trace.error('Unknown letter numeration ' + number)
      return 0
    index = NumberGenerator.letters.index(number) + 1
    return NumberGenerator.letters[index % len(NumberGenerator.letters)]

  def dotseparated(self, number):
    "Get the number separated by dots: 1.1.3"
    dotsep = ''
    if len(self.number) == 0:
      Trace.error('Empty number')
      return '.'
    for number in self.number:
      dotsep += '.' + str(number)
    return dotsep[1:]

NumberGenerator.instance = NumberGenerator()

class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout

  ordered = ['Chapter', 'Section', 'Subsection', 'Subsubsection', 'Paragraph']
  unique = ['Part', 'Book']

  def __init__(self):
    self.generator = NumberGenerator.instance

  def postprocess(self, layout, last):
    "Generate a number and place it before the text"
    if self.containsappendix(layout):
      self.activateappendix()
    if layout.type in PostLayout.unique:
      number = self.generator.generateunique(layout.type)
    elif layout.type in PostLayout.ordered:
      level = PostLayout.ordered.index(layout.type)
      number = self.generator.generate(level)
    elif layout.type == 'Standard':
      return self.checkforfloat(layout)
    else:
      return layout
    layout.contents.insert(0, Constant(number + u' '))
    return layout

  def containsappendix(self, layout):
    "Find out if there is an appendix somewhere in the layout"
    for element in layout.contents:
      if isinstance(element, Appendix):
        return True
    return False

  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    self.generator.number = ['-']

  def checkforfloat(self, standard):
    "Check a standard layout for a float inset"
    float = standard.searchfor(Float)
    if not float:
      return standard
    Trace.debug('Float type: ' + float.type)
    return self.numberfloat(float)

  def numberfloat(self, float):
    "Generate the number for the float"
    caption = float.searchfor(Caption)
    Trace.debug('Float: ' + str(caption.contents[0]))
    layout = caption.contents[0]
    index = 0
    while index < len(layout.contents):
      element = layout.contents[index]
      Trace.debug('Contains ' + str(element))
      if isinstance(element, Label):
        float.contents.insert(0, element)
        del layout.contents[index]
      elif isinstance(element, StringContainer):
        Trace.debug('Caption: "' + element.contents[0] + '"')
        index += 1
    number = self.generator.generatechaptered(float.type)
    caption.contents.insert(0, Constant(number + u' '))
    return float

Postprocessor.stages += [PostLayout]

