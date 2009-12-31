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
  "Ports a Java file."

  starttokens = {
      'if':'parensblock', 'catch':'parensblock', 'import':'ignorestatement',
      'public':'classormember', 'protected':'classormember', 'private':'classormember',
      'class':'parseclass', 'else':'tokenblock', 'try':'tokenblock',
      'return':'valuestatement', '{':'openblock', '}':'closeblock',
      'for':'forblock'
      }
  javatokens = {
      'new':'', 'this':'self'
      }

  def __init__(self):
    self.depth = 0
    self.inclass = None
    self.inmethod = None
    self.waitingforblock = False
    self.variables = ['this']

  def topy(self, inputfile, outputfile):
    "Port the Java input file to Python."
    tok = Tokenizer(FilePosition(inputfile))
    writer = LineWriter(outputfile)
    while not tok.pos.finished():
      statement = self.nextstatement(tok)
      Trace.debug('Statement: ' + statement)
      writer.writeline(statement)
    writer.close()

  def nextstatement(self, tok):
    "Return the next statement."
    statement = None
    while not statement and not tok.pos.finished():
      indent = '  ' * self.depth
      statement = self.parsestatement(tok)
    if not statement:
      return ''
    if statement.startswith('\n'):
      # displace newline
      return '\n' + indent + statement[1:]
    return indent + statement

  def parsestatement(self, tok):
    "Parse a single statement."
    token = tok.next()
    Trace.debug('Token: ' + token)
    if token in self.starttokens:
      function = getattr(self, self.starttokens[token])
      return function(token, tok)
    return self.assigninvoke(token, tok)

  def classormember(self, token, tok):
    "Parse a class or member (attribute or method)."
    if self.inclass:
      return self.translateinternal(tok)
    else:
      return self.translateclass(tok)

  def parensblock(self, token, tok):
    "Parse a parens () and then a block {} (if and catch)."
    parens = self.parseparens(tok)
    self.expectblock()
    if token == 'catch':
      return 'except:'
    return token + ' ' + parens + ':'

  def forblock(self, token, tok):
    "Parse a for parens (;;) and a block {}."
    return self.parensblock(token, tok)

  def tokenblock(self, token, tok):
    "Parse a block (after a try or an else)."
    self.expectblock()
    return token + ':'

  def openblock(self, token, tok):
    "Open a block of code."
    if self.waitingforblock:
      self.waitingforblock = False
    else:
      self.depth += 1
    return None

  def closeblock(self, token, tok):
    "Close a block of code."
    self.depth -= 1
    return None

  def expectblock(self):
    "Mark that a block is to be expected."
    self.depth += 1
    self.waitingforblock = True

  def valuestatement(self, token, tok):
    "A statement that contains a value."
    statement = token
    while tok.next() != ';':
      statement += ' ' + self.processtoken(tok)
    if self.waitingforblock:
      self.waitingforblock = False
      self.depth -= 1
    return statement

  def assigninvoke(self, token, tok):
    "An assignment or a method invocation."
    token2 = tok.next()
    if token2 == '=':
      # assignment
      if not token in self.variables:
        Trace.error('Undeclared variable ' + token)
      return self.valuestatement(token + ' =', tok)
    if token2 == '.':
      # member
      if not token in self.variables:
        Trace.error('Undeclared variable ' + token)
      member = tok.next()
      return self.assigninvoke(token + '.' + member, tok)
    if token2 == '(':
      parens = self.parseinparens(tok)
      return self.assigninvoke(token + '(' + parens + ')', tok)
    if token2 in tok.javasymbols:
      Trace.error('Unknown symbol ' + token2)
      return token + ' ' + token2
    token3 = tok.next()
    if token3 == '=':
      # a declaration
      self.variables.append(token2)
      return self.valuestatement(token2 + ' =', tok)
    Trace.error('Unknown combination ' + token + '+' + token2 + '+' + token3)
    return token + ' ' + token2 + ' ' + token

  def ignorestatement(self, token, tok):
    "Ignore a whole statement."
    tok.pos.globincluding(';')
    return None

  def translateclass(self, tok):
    "Translate a class definition."
    token = tok.next()
    if token != 'class':
      Trace.error('Unrecognized token: ' + token)
      return ''
    name = tok.next()
    self.inclass = name
    inheritance = ''
    while tok.next() != '{':
      inheritance += ' ' + tok.current()
    Trace.error('Unused inheritance ' + inheritance)
    self.openblock(tok.current(), tok)
    return 'class ' + name + '(object):'

  def translateinternal(self, tok):
    "Translate an internal element (attribute or method)."
    token = tok.next()
    name = tok.next()
    if token == self.inclass and name == '(':
      # constructor
      return self.translatemethod(token, tok)
    after = tok.next()
    if after == ';':
      return self.translateemptyattribute(name)
    if after == '(':
      return self.translatemethod(name, tok)
    if after != '=':
      Trace.error('Weird character after member: ' + token + ' ' + name + ' ' + after)
    return self.translateattribute(name)

  def translatemethod(self, name, tok):
    "Translate a class method."
    self.inmethod = name
    pars = self.parseparameters(tok)
    self.expectblock()
    return '\ndef ' + name + '(self' + '):'

  def translateemptyattribute(self, name):
    "Translate an empty attribute definition."
    return name + ' = None'

  def translateattribute(self, name, tok):
    "Translate a class attribute."
    return name + ' ' + self.parseupto(';')

  def parseparameters(self, tok):
    "Parse the parameters of a method definition."
    parens = self.parseinparens(tok)
    return parens.split(',')

  def processpart(self, tok):
    "Process a part of a statement."
    tok.next()
    return ' ' + self.processtoken(tok)

  def processtoken(self, tok):
    "Process a single token."
    if tok.current() in tok.javasymbols:
      return self.processsymbol(tok)
    if tok.current() in self.javatokens:
      return self.javatokens[tok.current()]
    return tok.current()
  
  def processsymbol(self, tok):
    "Process a single java symbol."
    if tok.current() == '"':
      result = tok.current() + tok.pos.globincluding('"')
      while result.endswith('\\"') and not result.endswith('\\\\"'):
        result += tok.pos.globincluding('"')
      Trace.debug('quoted sequence: ' + result)
      return result
    if tok.current() == '\'':
      result = tok.current()
      while not tok.pos.checkskip('\''):
        result += tok.pos.currentskip()
      return result + '\''
    if tok.current() == '}':
      Trace.error('Erroneously closing }')
      self.depth -= 1
      return ''
    if tok.current() == '(':
      result = self.parseinparens(tok)
      return result
    if tok.current() == ')':
      Trace.error('Erroneously closing )')
      return ')'
    if tok.current() in tok.modified:
      return tok.modified[tok.current()]
    return tok.current()

  def parseparens(self, tok):
    "Parse a couple of () and the contents inside."
    if tok.next() != '(':
      Trace.error('No opening ( for a parens, found ' + tok.current())
      return
    return self.parseinparens(tok)

  def parseinparens(self, tok):
    "Parse the contents inside ()."
    result = self.parseupto(')', tok)
    return '(' + result + ')'

  def parseupto(self, ending, tok):
    "Parse the tokenizer up to the supplied ending."
    result = ''
    while not tok.next() == ending:
      result += ' ' + self.processtoken(tok)
    if len(result) > 0:
      result = result[1:]
    return result

class Tokenizer(object):
  "Tokenizes a parse position."

  unmodified = [
      '&', '|', '=', '!', '(', ')', '{', '}', '.', '+', '-', '"', ',', '/',
      '*', '<', '>', '\'', '[', ']', '%', ';',
      '!=','++','--','<=','>=', '=='
      ]
  modified = {
      '&&':'and', '||':'or'
      }
  comments = ['//', '/*']
  javasymbols = comments + unmodified + modified.keys()

  def __init__(self, pos):
    self.pos = pos
    self.currenttoken = None

  def next(self):
    "Get the next single token, and store it for current()."
    self.currenttoken = self.extracttoken()
    while self.currenttoken in self.comments:
      self.skipcomment()
      self.currenttoken = self.extracttoken()
    self.pos.skipspace()
    return self.currenttoken

  def extracttoken(self):
    "Extract the next token."
    self.pos.skipspace()
    if self.pos.finished():
      raise Exception('Finished looking for next token.')
    if self.isalphanumeric(self.pos.current()):
      return self.pos.glob(self.isalphanumeric)
    if self.pos.current() in self.javasymbols:
      result = self.pos.currentskip()
      while result + self.pos.current() in self.javasymbols:
        result += self.pos.currentskip()
      return result
    current = self.pos.currentskip()
    raise Exception('Unrecognized character: ' + current)

  def current(self):
    "Get the current token."
    return self.currenttoken

  def isalphanumeric(self, char):
    "Detect if a character is alphanumeric or underscore."
    if char.isalpha():
      return True
    if char.isdigit():
      return True
    if char == '_':
      return True
    return False

  def skipcomment(self):
    "Skip over a comment."
    if self.current() == '//':
      comment = self.pos.globexcluding('\n')
      return
    if self.current() == '/*':
      while not self.pos.checkskip('/'):
        comment = self.pos.globincluding('*')
      return
    Trace.error('Unknown comment type ' + self.current())

inputfile, outputfile = readargs(sys.argv)
Trace.debugmode = True
if inputfile:
  JavaPorter().topy(inputfile, outputfile)
  Trace.message('Conversion done, running ' + outputfile)
  os.system('python ' + outputfile)


