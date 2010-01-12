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
# Alex 20090418
# eLyXer number generator

from util.trace import Trace
from conf.config import *


class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures"

  letters = '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  instance = None
  startinglevel = 0
  maxdepth = 10

  unique = NumberingConfig.layouts['unique']
  ordered = NumberingConfig.layouts['ordered']

  def __init__(self):
    self.number = []
    self.uniques = dict()
    self.chaptered = dict()

  def generateunique(self, type):
    "Generate unique numbering: a number to place in the title but not to "
    "append to others. Examples: Part 1, Book 3."
    if not type in self.uniques:
      self.uniques[type] = 0
    self.uniques[type] = self.increase(self.uniques[type])
    return unicode(self.uniques[type])

  def generateordered(self, type):
    "Generate ordered numbering: a number to use and possibly concatenate "
    "with others. Example: Chapter 1, Section 1.5."
    level = self.getlevel(type)
    if level == 0:
      Trace.error('Impossible level 0 for ' + type)
      return '.'
    if level > NumberGenerator.maxdepth:
      return ''
    if len(self.number) >= level:
      self.number = self.number[:level]
    else:
      while len(self.number) < level:
        self.number.append(0)
    self.number[level - 1] = self.increase(self.number[level - 1])
    return self.dotseparated(self.number)

  def generatechaptered(self, type):
    "Generate a number which goes with first-level numbers (chapters). "
    "For the article classes a unique number is generated."
    if NumberGenerator.startinglevel > 0:
      return self.generateunique(type)
    if len(self.number) == 0:
      chapter = 0
    else:
      chapter = self.number[0]
    if not type in self.chaptered or self.chaptered[type][0] != chapter:
      self.chaptered[type] = [chapter, 0]
    chaptered = self.chaptered[type]
    chaptered[1] = self.increase(chaptered[1])
    self.chaptered[type] = chaptered
    return self.dotseparated(chaptered)

  def getlevel(self, type):
    "Get the level that corresponds to a type."
    level = NumberGenerator.ordered.index(self.deasterisk(type)) + 1
    return level - NumberGenerator.startinglevel

  def isunique(self, container):
    "Find out if a container requires unique numbering."
    return container.type in NumberGenerator.unique

  def isinordered(self, container):
    "Find out if a container is ordered or unordered."
    return self.deasterisk(container.type) in NumberGenerator.ordered
  
  def isordered(self, container):
    "Find out if a container requires ordered numbering."
    return container.type in NumberGenerator.ordered

  def isunordered(self, container):
    "Find out if a container does not have a number."
    if not '*' in container.type:
      return False
    return self.isinordered(container)

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
    if len(number) == 0:
      Trace.error('Empty number')
      return '.'
    for piece in number:
      dotsep += '.' + unicode(piece)
    return dotsep[1:]

  def deasterisk(self, type):
    "Get the type without the asterisk for unordered types."
    return type.replace('*', '')

NumberGenerator.instance = NumberGenerator()

class LayoutNumberer(object):
  "Number a layout with the relevant attributes."

  instance = None

  def __init__(self):
    self.generator = NumberGenerator.instance

  def isnumbered(self, container):
    "Find out if a container requires numbering at all."
    return self.generator.deasterisk(container.type) \
        in NumberGenerator.unique + NumberGenerator.ordered

  def number(self, layout):
    "Set all attributes: number, entry, level..."
    if self.generator.isunique(layout):
      layout.number = self.generator.generateunique(layout.type)
      layout.entry = Translator.translate(layout.type) + ' ' + layout.number
      layout.partkey = 'toc-' + layout.type + '-' + layout.number
      layout.anchortext = layout.entry + '.'
      layout.level = 0
      return
    if not self.generator.isinordered(layout):
      Trace.error('Trying to number wrong ' + unicode(layout))
      return
    # ordered or unordered
    if self.generator.isordered(layout):
      layout.number = self.generator.generateordered(layout.type)
    elif self.generator.isunordered(layout):
      layout.number = ''
    number = layout.number
    if number == '':
      # ordered but bigger than maxdepth numbered or unordered
      number = self.generator.generateunique(layout.type)
    layout.partkey = 'toc-' + layout.type + '-' + number
    type = self.generator.deasterisk(layout.type)
    layout.anchortext = layout.number
    layout.entry = Translator.translate(type)
    if layout.number != '':
      layout.entry += ' ' + layout.number
    layout.level = self.generator.getlevel(type)
    layout.output.tag = layout.output.tag.replace('?', unicode(layout.level))

  def modifylayout(self, layout, type):
    "Modify a layout according to the given type."

LayoutNumberer.instance = LayoutNumberer()

