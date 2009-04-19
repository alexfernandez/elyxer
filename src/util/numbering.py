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
      dotsep += '.' + str(piece)
    return dotsep[1:]

NumberGenerator.instance = NumberGenerator()

