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
# Alex 20090503
# eLyXer formula parsing

import sys
from gen.container import *
from io.fileline import *
from util.trace import Trace
from conf.config import *


class Position(object):
  "A position in a text to parse"

  def __init__(self):
    self.endinglist = EndingList()

  def checkbytemark(self):
    "Check for a Unicode byte mark and skip it."
    if self.finished():
      return
    if ord(self.current()) == 0xfeff:
      self.currentskip()

  def skip(self, string):
    "Skip a string"
    Trace.error('Unimplemented skip()')

  def identifier(self):
    "Return an identifier for the current position."
    Trace.error('Unimplemented identifier()')
    return 'Error'

  def isout(self):
    "Find out if we are out of the position yet."
    Trace.error('Unimplemented isout()')
    return True

  def current(self):
    "Return the current character"
    Trace.error('Unimplemented current()')
    return ''

  def checkfor(self, string):
    "Check for a string at the given position."
    Trace.error('Unimplemented checkfor()')
    return False

  def finished(self):
    "Find out if the current formula has finished"
    if self.isout():
      self.endinglist.checkpending()
      return True
    return self.endinglist.checkin(self)

  def currentskip(self):
    "Return the current character and skip it."
    current = self.current()
    self.skip(current)
    return current

  def next(self):
    "Advance the position and return the next character."
    self.currentskip()
    return self.current()

  def checkskip(self, string):
    "Check for a string at the given position; if there, skip it"
    if not self.checkfor(string):
      return False
    self.skip(string)
    return True

  def glob(self, currentcheck):
    "Glob a bit of text that satisfies a check"
    glob = ''
    while not self.finished() and currentcheck(self.current()):
      glob += self.current()
      self.skip(self.current())
    return glob

  def globalpha(self):
    "Glob a bit of alpha text"
    return self.glob(lambda current: current.isalpha())

  def globnumber(self):
    "Glob a row of digits."
    return self.glob(lambda current: current.isdigit())

  def checkidentifier(self):
    "Check if the current character belongs to an identifier."
    return self.isidentifier(self.current())

  def isidentifier(self, char):
    "Return if the given character is alphanumeric or _."
    if char.isalnum() or char == '_':
      return True
    return False

  def globidentifier(self):
    "Glob alphanumeric and _ symbols."
    return self.glob(lambda current: self.isidentifier(current))

  def skipspace(self):
    "Skip all whitespace at current position"
    return self.glob(lambda current: current.isspace())

  def globincluding(self, magicchar):
    "Glob a bit of text up to (including) the magic char."
    glob = self.glob(lambda current: current != magicchar) + magicchar
    self.skip(magicchar)
    return glob

  def globexcluding(self, magicchar):
    "Glob a bit of text up until (excluding) the magic char."
    return self.glob(lambda current: current != magicchar)

  def pushending(self, ending, optional = False):
    "Push a new ending to the bottom"
    self.endinglist.add(ending, optional)

  def popending(self, expected = None):
    "Pop the ending found at the current position"
    ending = self.endinglist.pop(self)
    if expected and expected != ending:
      Trace.error('Expected ending ' + expected + ', got ' + ending)
    self.skip(ending)
    return ending

class TextPosition(Position):
  "A parse position based on a raw text."

  def __init__(self, text):
    "Create the position from some text."
    Position.__init__(self)
    self.pos = 0
    self.text = text
    self.checkbytemark()

  def skip(self, string):
    "Skip a string of characters."
    self.pos += len(string)

  def identifier(self):
    "Return a sample of the remaining text."
    length = 30
    if self.pos + length > len(self.text):
      length = len(self.text) - self.pos - 1
    return '*' + self.text[self.pos:self.pos + length]

  def isout(self):
    "Find out if we are out of the text yet."
    return self.pos >= len(self.text)

  def current(self):
    "Return the current character, assuming we are not out."
    return self.text[self.pos]

  def checkfor(self, string):
    "Check for a string at the given position."
    if self.pos + len(string) > len(self.text):
      return False
    return self.text[self.pos : self.pos + len(string)] == string

class FilePosition(Position):
  "A parse position based on an underlying file."

  def __init__(self, filename):
    "Create the position from a file."
    Position.__init__(self)
    self.reader = LineReader(filename)
    self.number = 1
    self.pos = 0
    self.checkbytemark()

  def skip(self, string):
    "Skip a string of characters."
    length = len(string)
    while self.pos + length > len(self.reader.currentline()):
      length -= len(self.reader.currentline()) - self.pos + 1
      self.nextline()
    self.pos += length

  def nextline(self):
    "Go to the next line."
    self.reader.nextline()
    self.number += 1
    self.pos = 0

  def identifier(self):
    "Return the current line and line number in the file."
    before = self.reader.currentline()[:self.pos - 1]
    after = self.reader.currentline()[self.pos:]
    return 'line ' + unicode(self.number) + ': ' + before + '*' + after

  def isout(self):
    "Find out if we are out of the text yet."
    if self.pos > len(self.reader.currentline()):
      if self.pos > len(self.reader.currentline()) + 1:
        Trace.error('Out of the line ' + self.reader.currentline() + ': ' + unicode(self.pos))
      self.nextline()
    return self.reader.finished()

  def current(self):
    "Return the current character, assuming we are not out."
    if self.pos == len(self.reader.currentline()):
      return '\n'
    if self.pos > len(self.reader.currentline()):
      Trace.error('Out of the line ' + self.reader.currentline() + ': ' + unicode(self.pos))
      return '*'
    return self.reader.currentline()[self.pos]

  def checkfor(self, string):
    "Check for a string at the given position."
    if self.pos + len(string) > len(self.reader.currentline()):
      return False
    return self.reader.currentline()[self.pos : self.pos + len(string)] == string

class EndingList(object):
  "A list of position endings"

  def __init__(self):
    self.endings = []

  def add(self, ending, optional):
    "Add a new ending to the list"
    self.endings.append(PositionEnding(ending, optional))

  def checkin(self, pos):
    "Search for an ending"
    if self.findending(pos):
      return True
    return False

  def pop(self, pos):
    "Remove the ending at the current position"
    ending = self.findending(pos)
    if not ending:
      Trace.error('No ending at ' + pos.current())
      return ''
    for each in reversed(self.endings):
      self.endings.remove(each)
      if each == ending:
        return each.ending
      elif not each.optional:
        Trace.error('Removed non-optional ending ' + each)
    Trace.error('No endings left')
    return ''

  def findending(self, pos):
    "Find the ending at the current position"
    if len(self.endings) == 0:
      return None
    for index, ending in enumerate(reversed(self.endings)):
      if ending.checkin(pos):
        return ending
      if not ending.optional:
        return None
    return None

  def checkpending(self):
    "Check if there are any pending endings"
    if len(self.endings) != 0:
      Trace.error('Pending ' + unicode(self) + ' left open')

  def __unicode__(self):
    "Printable representation"
    string = 'endings ['
    for ending in self.endings:
      string += unicode(ending) + ','
    if len(self.endings) > 0:
      string = string[:-1]
    return string + ']'

class PositionEnding(object):
  "An ending for a parsing position"

  def __init__(self, ending, optional):
    self.ending = ending
    self.optional = optional

  def checkin(self, pos):
    "Check for the ending"
    return pos.checkfor(self.ending)

  def __unicode__(self):
    "Printable representation"
    string = 'Ending ' + self.ending
    if self.optional:
      string += ' (optional)'
    return string

