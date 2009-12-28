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
# Alex 20091226
# Port a Java program to a Python equivalent. Used to port MathToWeb.

import sys
import os.path
from io.fileline import *
from parse.position import *
from util.trace import Trace


def readargs(args):
  "Read arguments from the command line"
  del args[0]
  if len(args) == 0:
    usage()
    return
  inputfile = args[0]
  del args[0]
  outputfile = os.path.splitext(inputfile)[0] + '.py'
  if len(args) > 0:
    outputfile = args[0]
    del args[0]
  if len(args) > 0:
    usage()
    return
  return inputfile, outputfile

def usage():
  Trace.error('Usage: javatopy.py filein.java [fileout.py]')
  return

class JavaPorter(object):

  javasymbols = '&|=!(){}.+-",/*<>\'[]%'
  javatokens = [
      'if', 'do', 'while', '&&', '||', '=', '==', '!=', 'import', 'public',
      'class', 'private', 'protected'
      ]

  def __init__(self):
    self.depth = 0
    self.inclass = False
    self.inmethod = False

  def topy(self, inputfile, outputfile):
    "Port the Java input file to Python."
    pos = FilePosition(inputfile)
    writer = LineWriter(outputfile)
    while not pos.finished():
      line = self.processstatement(pos)
      if len(line.strip()) > 0:
        writer.writeline(line)
    writer.close()

  def processstatement(self, pos):
    "Process a single statement and return the result."
    indent = self.depth * '  '
    token = self.nexttoken(pos)
    if token in self.javatokens:
      return indent + self.translatetoken(token, pos)
    statement = indent + self.processtoken(token, pos)
    while not pos.checkskip(';') and not pos.finished():
      statement += self.processpart(pos)
    return statement

  def processpart(self, pos):
    "Process a part of a statement."
    token = self.nexttoken(pos)
    return ' ' + self.processtoken(token, pos)

  def processtoken(self, token, pos):
    "Process a single token."
    if token in self.javasymbols:
      return self.translatesymbol(token, pos)
    return token

  def nexttoken(self, pos):
    "Get the next single token."
    while not pos.finished():
      token = self.extracttoken(pos)
      if token:
        return token
    return ''

  def extracttoken(self, pos):
    "Extract a single token."
    pos.skipspace()
    if pos.finished():
      return None
    if pos.checkskip('//'):
      comment = pos.globexcluding('\n')
      Trace.debug('Comment: ' + comment)
      return None
    if pos.checkskip('/*'):
      while not pos.checkskip('/'):
        comment = pos.globincluding('*')
        Trace.debug('Comment: ' + comment)
      return None
    if self.isalphanumeric(pos.current()):
      return pos.glob(self.isalphanumeric)
    if pos.current() in self.javasymbols:
      return pos.currentskip()
    current = pos.currentskip()
    Trace.error('Unrecognized character: ' + current)
    return current

  def translatetoken(self, token, pos):
    "Translate a java token."
    if token == 'import':
      return self.translateimport(pos)
    if token in ['public', 'private', 'protected']:
      if self.inclass:
        return self.translateattr(pos)
      else:
        return self.translateclass(pos)
    Trace.error('Untranslated token ' + token)
    return token

  def translateimport(self, pos):
    "Translate an import statement."
    pos.globincluding(';')
    return ''

  def translateclass(self, pos):
    "Translate a class definition."
    token = self.nexttoken(pos)
    if token != 'class':
      Trace.error('Unrecognized token: ' + token)
      return ''
    name = self.nexttoken(pos)
    token = self.nexttoken(pos)
    while token != '{':
      Trace.error('Ignored token ' + token)
      token = self.nexttoken(pos)
    self.depth += 1
    return 'class ' + name + ':'

  def translateattr(self, pos):
    "Translate an attribute (method or variable)."
    return self.translateimport(pos)
  
  def translatesymbol(self, token, pos):
    "Translate a java symbol."
    if token == '"':
      result = token + pos.globincluding('"')
      while result.endswith('\\"') and not result.endswith('\\\\"'):
        result = token + pos.globincluding('"')
      Trace.debug('quoted sequence: ' + result)
      return result
    if token == '\'':
      result = token
      while not pos.checkskip('\''):
        result += pos.currentskip()
      return result + token
    return token

  def isalphanumeric(self, char):
    "Detect if a character is alphanumeric or underscore."
    if char.isalpha():
      return True
    if char.isdigit():
      return True
    if char == '_':
      return True
    return False

inputfile, outputfile = readargs(sys.argv)
Trace.debugmode = False
if inputfile:
  JavaPorter().topy(inputfile, outputfile)
  Trace.message('Conversion done, running ' + outputfile)
  os.system('python ' + outputfile)


