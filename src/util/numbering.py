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
  master = None

  letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  romannumerals = [
      ('M', 1000), ('CM', 900), ('D', 500), ('CD', 400), ('C', 100),
      ('XC', 90), ('L', 50), ('XL', 40), ('X', 10), ('IX', 9), ('V', 5),
      ('IV', 4), ('I', 1)
      ]

  def __init__(self, name):
    "Give a name to the counter."
    self.name = name

  def setmode(self, mode):
    "Set the counter mode. Can be changed at runtime."
    self.mode = mode
    return self

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
    if self.mode == 'a':
      return self.getletter().lower()
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

class DependentCounter(NumberCounter):
  "A counter which depends on another one (the master)."

  def setmaster(self, master):
    "Set the master counter."
    self.master = master
    self.last = self.master.getvalue()
    return self

  def increase(self):
    "Increase or, if the master counter has changed, restart."
    if self.last != self.master.getvalue():
      self.reset()
    NumberCounter.increase(self)
    self.last = self.master.getvalue()
    return self

  def getvalue(self):
    "Get the value of the combined counter: master.dependent."
    return self.master.getvalue() + '.' + NumberCounter.getvalue(self)

class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures. Used in:"
  "  * ordered part numbers: Chapter 3, Section 5.3."
  "  * unique part numbers: Footnote 15, Bibliography cite [15]."
  "  * chaptered part numbers: Figure 3.15, Equation (8.3)."
  "  * unique roman part numbers: Part I, Book IV."

  unique = None
  ordered = None
  roman = None
  chaptered = None
  generator = None

  romanlayouts = [x.lower() for x in NumberingConfig.layouts['roman']]
  orderedlayouts = [x.lower() for x in NumberingConfig.layouts['ordered']]

  counters = dict()

  def deasterisk(self, type):
    "Remove the possible asterisk in a layout type."
    return type.replace('*', '')

  def isunique(self, type):
    "Find out if the layout type corresponds to a unique part."
    return self.isroman(type)

  def isroman(self, type):
    "Find out if the layout type should have roman numeration."
    return self.deasterisk(type).lower() in self.romanlayouts

  def isinordered(self, type):
    "Find out if the layout type corresponds to an (un)ordered part."
    return self.deasterisk(type).lower() in self.orderedlayouts

  def isnumbered(self, type):
    "Find out if the type for a layout corresponds to a numbered layout."
    if '*' in type:
      return False
    if self.isroman(type):
      return True
    if not self.isinordered(type):
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
    "Each invocation results in a new number."
    return self.getcounter(type).increase().getvalue()

  def getparttype(self, type):
    "Obtain the type for the part: without the asterisk, "
    "and switched to Appendix if necessary."
    if NumberGenerator.ordered.appendix and self.getlevel(type) == 1:
      return 'Appendix'
    return self.deasterisk(type)

  def getcounter(self, type):
    "Get the counter for the given type."
    type = type.lower()
    if not type in self.counters:
      self.counters[type] = self.create(type)
    return self.counters[type]

  def create(self, type):
    "Create a counter for the given type."
    if self.isnumbered(type) and self.getlevel(type) > 1:
      index = self.orderedlayouts.index(type)
      above = self.orderedlayouts[index - 1]
      master = self.getcounter(above)
      return self.createdependent(type, master)
    counter = NumberCounter(type)
    if self.isroman(type):
      counter.setmode('I')
    return counter

  def getchapter(self):
    "Get the current chapter counter."
    return self.getcounter('Chapter')

  def getdependentcounter(self, type, master):
    "Get (or create) a counter of the given type that depends on another."
    if not type in self.counters or not self.counters[type].master:
      self.counters[type] = self.createdependent(type, master)
    return self.counters[type]

  def createdependent(self, type, master):
    "Create a dependent counter given the master."
    return DependentCounter(type).setmaster(master)

  def startappendix(self):
    "Start appendices here."
    firsttype = self.orderedlayouts[DocumentParameters.startinglevel]
    Trace.debug('First type: ' + firsttype)
    counter = self.getcounter(firsttype)
    counter.setmode('A').reset()
    self.appendix = True

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

  appendix = False
  sequence = []

  def createsequence(self):
    "Create the original sequence."
    sequence = []
    for type in self.orderedlayouts:
      if sequence == []:
        counter = self.getcounter(type)
      else:
        counter = self.getdependentcounter(type, sequence[-1])
      sequence.append(counter)
      if len(sequence) + 1 > DocumentParameters.maxdepth:
        return sequence
    return sequence

  def generate(self, type):
    "Generate ordered numbering: a number to use and possibly concatenate "
    "with others. Example: Chapter 1, Section 1.5."
    if self.sequence == []:
      self.sequence = self.createsequence()
    level = self.getlevel(type)
    if level == 0:
      Trace.error('Impossible level 0 for ordered part')
      return '.'
    if level > len(self.sequence):
      return NumberGenerator.unique.generate(type)
    counter = self.sequence[level - 1]
    return counter.increase().getvalue()

class ChapteredGenerator(OrderedGenerator):
  "Generate chaptered numbers, as in Chapter.Number."
  "Used in equations, figures: Equation (5.3), figure 8.15."

  def generate(self, type):
    "Generate a number which goes with first-level numbers (chapters). "
    "For the article classes a unique number is generated."
    if DocumentParameters.startinglevel > 0:
      return NumberGenerator.unique.generate(type)
    chapter = NumberGenerator.ordered.getchapter()
    counter = self.getdependentcounter(type, chapter)
    counter.increase()
    return counter.getvalue()

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

