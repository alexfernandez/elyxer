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
# Alex 20091107
# LyX header file cleanup.
# http://www.nongnu.org/elyxer/


import sys
import os.path
from io.convert import *
from util.trace import Trace
from util.options import *


class CParser(object):
  "A parser for a C-like file."

  builtins = [
      'if', 'const', 'return', 'new', 'delete', 'false', 'true', 'namespace',
      'typedef', 'using', 'struct', 'int', 'char', 'void', 'for'
      ]

  def __init__(self, filename):
    self.filename = filename
    self.keywords = dict()
    self.functions = dict()

class CppParser(CParser):
  "A parser for a .cpp file."

  def parse(self):
    "Parse the whole file."
    lines = BulkFile(self.filename).readall()
    text = ''.join(lines)
    tokens = self.parsetokens(text)
    if len(tokens) == 0:
      return
    last = None
    for token in tokens:
      self.processtoken(token, last)
      last = token

  def processtoken(self, token, last):
    "Process a single token."
    if token.startswith('('):
      if not last:
        Trace.error('Missing last token for ' + token)
        return
      if last in CParser.builtins:
        return
      self.addto(self.functions, last)
      self.removefrom(self.keywords, last)
      return
    if token in CParser.builtins:
      return
    self.addto(self.keywords, token)

  def parsetokens(self, text):
    "Parse all tokens in a text."
    tokens = []
    pos = Position(text)
    while not pos.finished():
      token = self.gettoken(pos)
      if token:
        tokens.append(token)
    return tokens

  def gettoken(self, pos):
    "Get the next token."
    if pos.checkskip('/*'):
      pos.pushending('*/')
      comment = pos.glob(lambda current: True)
      pos.popending()
      Trace.debug('Comment: ' + comment)
      return None
    if pos.checkskip('//'):
      comment = pos.globexcluding('\n')
      Trace.debug('Comment: ' + comment)
      return None
    if pos.current().isalpha() or pos.current() == '_':
      return pos.glob(lambda current: current.isalnum() or current == '_')
    if pos.checkskip('('):
      return '('
    if pos.checkskip('"'):
      literal = pos.globincluding('"')
      Trace.debug('Literal: ' + literal)
      return
    pos.skip(pos.current())

  def addto(self, anydict, token):
    "Add one to any dictionary."
    if not token in anydict:
      anydict[token] = 0
    anydict[token] += 1

  def removefrom(self, anydict, token):
    "Remove one from any dictionary."
    anydict[token] -= 1
    if anydict[token] == 0:
      del anydict[token]

  def showall(self):
    "Print all functions and tokens."
    Trace.debug('Keywords: ')
    self.printall(self.keywords)
    Trace.debug('Functions: ')
    self.printall(self.functions)
    Trace.message('Filename: ' + self.filename + ' - Keywords: ' +
        unicode(len(self.keywords)) + ', functions: ' + unicode(len(self.functions)))

  def printall(self, anydict):
    "Print all values in a dictionary."
    keys = anydict.keys()
    keys.sort()
    for value in keys:
      Trace.debug('  ' + value + ': ' + unicode(anydict[value]))

def processcpp(args):
  "Read a C++ file and parse it."
  Options().parseoptions(args)
  if len(args) == 0:
    Trace.error('No files to read.')
    return
  while len(args) > 0:
    parser = CppParser(args[0])
    parser.parse()
    parser.showall()
    del args[0]

def main():
  "Main function, called if invoked from the command line"
  processcpp(list(sys.argv))

if __name__ == '__main__':
  main()

