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
from util.translate import *
from util.docparams import *
from conf.config import *


class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures"

  letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  instance = None

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

  def generateordered(self, level):
    "Generate ordered numbering: a number to use and possibly concatenate "
    "with others. Example: Chapter 1, Section 1.5."
    if level == 0:
      Trace.error('Impossible level 0 for ordered part')
      return '.'
    if len(self.number) >= level:
      self.number = self.number[:level]
    else:
      while len(self.number) < level:
        self.number.append(0)
    self.number[level - 1] = self.increase(self.number[level - 1])
    return self.dotseparated(self.number)

  def generatechaptered(self, type, chapter = None):
    "Generate a number which goes with first-level numbers (chapters). "
    "For the article classes a unique number is generated."
    if DocumentParameters.startinglevel > 0:
      return self.generateunique(type)
    if not chapter:
      chapter = self.getchapter()
    if not type in self.chaptered or self.chaptered[type][0] != chapter:
      self.chaptered[type] = [chapter, 0]
    chaptered = self.chaptered[type]
    chaptered[1] = self.increase(chaptered[1])
    self.chaptered[type] = chaptered
    return self.dotseparated(chaptered)

  def getchapter(self):
    "Get the current chapter number."
    if len(self.number) == 0:
      return 0
    else:
      return self.number[0]

  def increase(self, number):
    "Increase the number (or letter)"
    if not isinstance(number, str):
      return number + 1
    if number == '-':
      index = 0
    elif not number in NumberGenerator.letters:
      Trace.error('Unknown letter numeration ' + number)
      return 0
    else:
      index = NumberGenerator.letters.index(number) + 1
    return self.letter(index)

  def letter(self, index):
    "Get the letter that corresponds to the given index."
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

  def startappendix(self):
    "Start appendices here."
    self.number = ['-']

NumberGenerator.instance = NumberGenerator()

