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


class NumberCounter(object):
  "A counter for numbers (by default)."
  "The type can be changed to return letters, roman numbers..."

  name = None
  value = None
  mode = None

  letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  romannumerals = [
      ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100),
      ('XC', 90), ('L', 50), ('XL', 40), ('X', 10), ('IX', 9), ('V', 5),
      ('IV', 4), ('I', 1)
      ]

  def __init__(self, name):
    "Give a name to the counter."
    self.name = name

  def init(self, value):
    "Set an initial value."
    self.value = value

  def increase(self):
    "Increase the counter value and return the counter."
    if not self.value:
      self.value = 0
    self.value += 1
    return self

  def gettext(self):
    "Get the next value as a text string."
    return unicode(self.value)

  def getletter(self):
    "Get the next value as a letter."
    return self.letters[(self.value - 1) % len(self.letters)]

  def getroman(self):
    "Get the next value as a roman number."
    result = ''
    number = self.value
    for numeral, value in self.romannumerals:
      if number >= value:
        result += numeral * (number / value)
        number = number % value
    return result

  def getvalue(self):
    "Get the current value as configured in the current mode."
    if not self.mode or self.mode in ['text', '1']:
      return self.gettext()
    if self.mode == 'A':
      return self.getletter()
    if self.mode == 'I':
      return self.getroman()
    Trace.error('Unknown counter mode ' + self.mode)
    return self.gettext()

  def reset(self):
    "Reset the counter."
    self.value = 0

  def __unicode__(self):
    "Return a printable representation."
    result = 'Counter ' + self.name
    if self.mode:
      result += ' in mode ' + self.mode
    return result

class ChapteredCounter(NumberCounter):
  "A counter which depends on the chapter."

  chapter = None

  def setchapter(self, chapter):
    "Set the chapter counter."
    self.chapter = chapter
    self.last = self.chapter.getvalue()
    return self

  def increase(self):
    "Increase or, if in a new chapter, restart."
    if self.last != self.chapter.getvalue():
      self.reset()
    NumberCounter.increase(self)
    self.last = self.chapter.getvalue()

class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures. Used in:"
  "  * ordered part numbers: Chapter 3, Section 5.3."
  "  * unique part numbers: Footnote 15, Bibliography cite [15]."
  "  * chaptered part numbers: Figure 3.15, Equation (8.3)."
  "  * unique roman part numbers: Part I, Book IV."

  letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  unique = None
  ordered = None
  roman = None
  chaptered = None
  generator = None

  romanlayouts = [x.lower() for x in NumberingConfig.layouts['roman']]
  orderedlayouts = [x.lower() for x in NumberingConfig.layouts['ordered']]

  counters = dict()

  def increase(self, number):
    "Increase the number (or letter)."
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

  def deasterisk(self, type):
    "Remove the possible asterisk in a layout type."
    return type.replace('*', '')

  def isunique(self, type):
    "Find out if the layout type corresponds to a unique part."
    return self.deasterisk(type).lower() in self.romanlayouts

  def isinordered(self, type):
    "Find out if the layout type corresponds to an (un)ordered part."
    return self.deasterisk(type).lower() in self.orderedlayouts

  def isnumbered(self, type):
    "Find out if the type for a layout corresponds to a numbered layout."
    if '*' in type:
      return False
    if self.getlevel(type) > DocumentParameters.maxdepth:
      return False
    return True

  def isunordered(self, type):
    "Find out if the type contains an asterisk, basically."
    return '*' in type

  def getlevel(self, type):
    "Get the level that corresponds to a layout type."
    if self.isunique(type):
      return 0
    if not self.isinordered(type):
      Trace.error('Unknown layout type ' + type)
      return 0
    type = self.deasterisk(type).lower()
    level = self.orderedlayouts.index(type) + 1
    return level - DocumentParameters.startinglevel

  def getnumber(self, type):
    "Get the number for a layout type, can be unique or ordered."
    "Unique part types such as Part or Book generate roman numbers: Part I."
    "Ordered part types return dot-separated tuples: Chapter 5, Section 2.3."
    "Everything else generates unique numbers: Bibliography [1]."
    if self.isunique(type):
      return NumberGenerator.roman.generate(type)
    if self.isnumbered(type):
      return NumberGenerator.ordered.generate(type)
    return NumberGenerator.unique.generate(type)

  def getparttype(self, type):
    "Obtain the type for the part: without the asterisk, "
    "and switched to Appendix if necessary."
    if NumberGenerator.ordered.appendix and self.getlevel(type) == 1:
      return 'Appendix'
    return self.deasterisk(type)

  def getcounter(self, name):
    "Get the counter with the given name."
    name = name.lower()
    if not name in self.counters:
      self.counters[name] = NumberCounter(name)
      if name in self.romanlayouts:
        self.counters[name].mode = 'I'
    return self.counters[name]

  def getchapter(self):
    "Get the current chapter counter."
    return self.getcounter('Chapter')

class UniqueGenerator(NumberGenerator):
  "Generate unique part numbers."
  "Used in footnotes or bibliographical entry numbers: [3]."

  def generate(self, type):
    "Generate unique numbering: a number to place in the title,"
    "but not to append to others. Example: Footnote 15."
    return self.getcounter(type).increase().getvalue()

class OrderedGenerator(NumberGenerator):
  "Generate ordered part numbers separated by a dot, as in 2.3 or 7.5.4."
  "Used in chapters, sections... as in Chapter 5, Section 5.3."

  def __init__(self):
    self.sequence = [self.getchapter()]
    self.appendix = False

  def generate(self, type):
    "Generate ordered numbering: a number to use and possibly concatenate "
    "with others. Example: Chapter 1, Section 1.5."
    level = self.getlevel(type)
    if level == 0:
      Trace.error('Impossible level 0 for ordered part')
      return '.'
    if len(self.sequence) >= level:
      self.sequence = self.sequence[:level]
    else:
      while len(self.sequence) < level:
        self.sequence.append(NumberCounter(type))
    self.sequence[level - 1].increase()
    return self.dotseparated(self.sequence)

  def dotseparated(self, sequence):
    "Get the sequence of counters as a number separated by dots: 1.1.3."
    dotsep = ''
    if len(sequence) == 0:
      Trace.error('Empty number sequence')
      return '.'
    for counter in sequence:
      dotsep += '.' + counter.getvalue()
    return dotsep[1:]

  def startappendix(self):
    "Start appendices here."
    self.sequence = self.sequence[:1]
    self.sequence[0].reset()
    self.sequence[0].mode = 'A'
    self.appendix = True

class ChapteredGenerator(OrderedGenerator):
  "Generate chaptered numbers, as in Chapter.Number."
  "Used in equations, figures: Equation (5.3), figure 8.15."

  def generate(self, type):
    "Generate a number which goes with first-level numbers (chapters). "
    "For the article classes a unique number is generated."
    if DocumentParameters.startinglevel > 0:
      return NumberGenerator.unique.generate(type)
    chapter = NumberGenerator.ordered.getchapter()
    counter = self.getchapteredcounter(type)
    counter.increase()
    return self.dotseparated([chapter, counter])

  def getchapteredcounter(self, type):
    "Get (or create) a chaptered counter of the given type."
    if not type in self.counters or not isinstance(self.counters[type], ChapteredCounter):
      counter = ChapteredCounter(type).setchapter(self.getchapter())
      self.counters[type] = counter
    return self.counters[type]

class RomanGenerator(UniqueGenerator):
  "Generate roman numerals for part numbers."
  "Used in parts and books: Part I, Book IV."

  def generate(self, type):
    "Generate a part number in roman numerals, to use in unique part numbers."
    "E.g.: Part I, Book IV."
    return self.getcounter(type).increase().getroman()


NumberGenerator.unique = UniqueGenerator()
NumberGenerator.ordered = OrderedGenerator()
NumberGenerator.chaptered = ChapteredGenerator()
NumberGenerator.roman = RomanGenerator()
NumberGenerator.generator = NumberGenerator()

