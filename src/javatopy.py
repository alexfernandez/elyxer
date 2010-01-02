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
      'if':'conditionblock', 'catch':'parametersblock', 'import':'ignorestatement',
      'public':'classormember', 'protected':'classormember', 'private':'classormember',
      'class':'parseclass', 'else':'tokenblock', 'try':'tokenblock',
      'return':'returnstatement', '{':'openblock', '}':'closeblock',
      'for':'forparens0'
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
    self.infor = 0

  def topy(self, inputfile, outputfile):
    "Port the Java input file to Python."
    tok = Tokenizer(FilePosition(inputfile))
    writer = LineWriter(outputfile)
    while not tok.pos.finished():
      statement = self.nextstatement(tok)
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
    Trace.debug('Statement: ' + statement.strip())
    if statement.startswith('\n'):
      # displace newline
      return '\n' + indent + statement[1:]
    return indent + statement

  def parsestatement(self, tok):
    "Parse a single statement."
    token = tok.next()
    if token in self.starttokens:
      function = getattr(self, self.starttokens[token])
    elif self.infor > 0:
      function = getattr(self, 'forparens' + unicode(self.infor))
    else:
      function = self.assigninvoke
    return function(tok)

  def classormember(self, tok):
    "Parse a class or member (attribute or method)."
    if self.inclass:
      return self.translateinternal(tok)
    else:
      return self.translateclass(tok)

  def conditionblock(self, tok):
    "Parse a condition in () and then a block {} (if statement)."
    tok.checknext('(')
    parens = self.parsecondition(tok, ')')
    self.expectblock()
    return 'if ' + parens + ':'

  def parametersblock(self, tok):
    "Parse a parameters () and then a block {} (catch statement)."
    tok.checknext('(')
    parens = self.listparameters(tok)
    self.expectblock()
    return 'except:'

  def forparens0(self, tok):
    "Parse the first statement of a for loop."
    "The remaining parts of the for(;;){} are parsed later."
    tok.checknext('(')
    first = self.assigninvoke(tok, tok.next())
    self.infor = 1
    return first

  def forparens1(self, tok):
    "Read the condition in a for loop."
    condition = tok.current() + ' ' + self.parseupto(';', tok)
    self.depth += 1
    self.infor = 2
    return 'while ' + condition + ':'
  
  def forparens2(self, tok):
    "Read the repeating statement in a for loop."
    statement = tok.current() + ' ' + self.parseupto(')', tok)
    self.depth -= 1
    self.infor = 0
    self.expectblock()
    return statement

  def tokenblock(self, tok):
    "Parse a block (after a try or an else)."
    self.expectblock()
    return tok.current() + ':'

  def openblock(self, tok):
    "Open a block of code."
    if self.waitingforblock:
      self.waitingforblock = False
    else:
      self.depth += 1
    return None

  def closeblock(self, tok):
    "Close a block of code."
    self.depth -= 1
    return None

  def expectblock(self):
    "Mark that a block is to be expected."
    self.depth += 1
    self.waitingforblock = True

  def returnstatement(self, tok):
    "A statement that contains a value (a return statement)."
    self.onelineblock()
    return 'return ' + self.parsevalue(tok)

  def assigninvoke(self, tok, token = None):
    "An assignment or a method invocation."
    self.onelineblock()
    if not token:
      token = tok.current()
    token2 = tok.next()
    if token2 == '=':
      # assignment
      if not token in self.variables:
        Trace.error('Undeclared variable ' + token)
      return token + ' = ' + self.parsevalue(tok)
    if token2 == '.':
      # member
      if not token in self.variables:
        Trace.error('Undeclared variable ' + token)
      member = tok.next()
      return self.assigninvoke(tok, token + '.' + member)
    if token2 == '(':
      parens = self.parseinparens(tok)
      return self.assigninvoke(tok, token + '(' + parens + ')')
    if token2 == '[':
      index = self.parseinsquare(tok)
      return self.assigninvoke(tok, token + '[' + index + ']')
    if token2 == ';':
      # finished invocation
      return token
    if token2 in tok.javasymbols:
      Trace.error('Unknown symbol ' + token2 + ' for ' + token)
      return token + ' ' + token2
    token3 = tok.next()
    if token3 == '=':
      # a declaration
      self.variables.append(token2)
      return token2 + ' = ' + self.parsevalue(tok)
    Trace.error('Unknown combination ' + token + '+' + token2 + '+' + token3)
    return token + ' ' + token2 + ' ' + token

  def onelineblock(self):
    "Check if a block was expected."
    if self.waitingforblock:
      self.waitingforblock = False
      self.depth -= 1

  def ignorestatement(self, tok):
    "Ignore a whole statement."
    tok.pos.globincluding(';')
    return None

  def translateclass(self, tok):
    "Translate a class definition."
    tok.checknext('class')
    name = tok.next()
    self.inclass = name
    inheritance = ''
    while tok.next() != '{':
      inheritance += ' ' + tok.current()
    Trace.error('Unused inheritance ' + inheritance)
    self.openblock(tok)
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
    return self.translateattribute(name, tok)

  def translatemethod(self, name, tok):
    "Translate a class method."
    self.inmethod = name
    pars = self.listparameters(tok)
    self.expectblock()
    return '\ndef ' + name + '(self' + '):'

  def translateemptyattribute(self, name):
    "Translate an empty attribute definition."
    return name + ' = None'

  def translateattribute(self, name, tok):
    "Translate a class attribute."
    return name + ' ' + self.parseupto(';', tok)

  def listparameters(self, tok):
    "Parse the parameters of a method definition, return them as a list."
    parens = self.parseinparens(tok)
    return parens.split(',')

  def processtoken(self, tok):
    "Process a single token."
    if tok.current() in tok.javasymbols:
      return self.processsymbol(tok)
    if tok.current() in self.javatokens:
      return self.javatokens[tok.current()]
    return tok.current()
  
  def processsymbol(self, tok):
    "Process a single java symbol."
    if tok.current() == '"' or tok.current() == '\'':
      return self.parsequoted(tok.current(), tok)
    if tok.current() == '}':
      Trace.error('Erroneously closing }')
      self.depth -= 1
      return ''
    if tok.current() == '(':
      result = self.parseinparens(tok)
      return result
    if tok.current() == '[':
      result = self.parseinsquare(tok)
      return result
    if tok.current() == ')':
      Trace.error('Erroneously closing )')
      return ')'
    if tok.current() in tok.modified:
      return tok.modified[tok.current()]
    return tok.current()

  def parsequoted(self, quote, tok):
    "Parse a quoted sentence, with variable quotes."
    result = tok.current() + tok.pos.globincluding(quote)
    while result.endswith('\\' + quote) and not result.endswith('\\\\' + quote):
      result += tok.pos.globincluding(quote)
    Trace.debug('Quoted sequence: ' + result)
    return result

  def parseparens(self, tok):
    "Parse a couple of () and the contents inside."
    tok.checknext('(')
    return self.parseinparens(tok)

  def parseinparens(self, tok):
    "Parse the contents inside ()."
    return self.parseinbrackets('(', ')', tok)

  def parseinsquare(self, tok):
    "Parse the contents inside []."
    return self.parseinbrackets('[', ']', tok)

  def parseinbrackets(self, opening, closing, tok):
    "Parse the contents in any kind of brackets."
    result = self.parseupto(closing, tok)
    return opening + result + closing

  def parsecondition(self, tok, ending):
    "Parse a condition given the ending token."
    return self.parseupto(ending, tok)

  def parsevalue(self, tok, ending = ';'):
    "Parse a value (to be assigned or returned)."
    return self.parseupto(ending, tok)

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
      '&', '|', '=', '(', ')', '{', '}', '.', '+', '-', '"', ',', '/',
      '*', '<', '>', '\'', '[', ']', '%', ';',
      '!=','<=','>=', '=='
      ]
  modified = {
      '&&':'and', '||':'or', '++':' += 1', '--':' -= 1', '!':'not'
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

  def checknext(self, token):
    "Check that the next token is the parameter."
    self.next()
    if self.currenttoken != token:
      Trace.error('Expected token ' + token + ', found ' + self.currenttoken)

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


