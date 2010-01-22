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
  outputfile = os.path.splitext(inputfile)[0].lower() + '.py'
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
      'class':'parseclass', 'else':'elseblock', 'try':'tryblock',
      'return':'returnstatement', '{':'openblock', '}':'closeblock',
      'for':'forparens0', 'new':'createstatement', 'throw':'throwstatement',
      'throws':'throwsdeclaration', ';':'ignorestatement', 'while':'conditionblock'
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
    self.autoincreases = []
    self.autodecreases = []

  def topy(self, inputfile, outputfile):
    "Port the Java input file to Python."
    tok = Tokenizer(FilePosition(inputfile))
    writer = LineWriter(outputfile)
    while not tok.finished():
      statement = self.nextstatement(tok)
      writer.writeline(statement)
    writer.close()

  def nextstatement(self, tok):
    "Return the next statement."
    statement = None
    while not statement and not tok.finished():
      indent = '  ' * self.depth
      statement = self.parsestatement(tok)
    if not statement:
      return ''
    # Trace.debug('Statement: ' + statement.strip())
    if statement.startswith('\n'):
      # displace newline
      return '\n' + indent + statement[1:]
    return indent + statement

  def parsestatement(self, tok):
    "Parse a single statement."
    pending = self.pendingstatement(tok)
    if pending:
      return pending
    token = tok.next()
    if not token:
      return None
    if token in self.starttokens:
      function = getattr(self, self.starttokens[token])
    else:
      function = self.assigninvoke
    return function(tok)

  def pendingstatement(self, tok):
    "Return any pending statement from before."
    if self.infor != 0:
      tok.next()
      function = getattr(self, 'forparens' + unicode(self.infor))
      return function(tok)
    if len(self.autoincreases) != 0:
      return self.autoincrease(tok)
    if len(self.autodecreases) != 0:
      return self.autodecrease(tok)
    return None

  def classormember(self, tok):
    "Parse a class or member (attribute or method)."
    if self.inclass:
      return self.translateinternal(tok)
    else:
      return self.translateclass(tok)

  def conditionblock(self, tok):
    "Parse a condition in () and then a block {} (if or while statements)."
    token = tok.current()
    tok.checknext('(')
    parens = self.parsecondition(tok, ')')
    self.expectblock()
    return token + ' ' + parens + ':'

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

  def tryblock(self, tok):
    "Parse a block after a try."
    self.expectblock()
    return tok.current() + ':'

  def elseblock(self, tok):
    "Parse a block after an else."
    self.expectblock()
    if tok.peek() == 'if':
      tok.next()
      self.closeblock(tok)
      return 'el' + self.conditionblock(tok)
    return 'else:'

  def openblock(self, tok):
    "Open a block of code."
    if self.waitingforblock:
      self.waitingforblock = False
    else:
      self.depth += 1
    if tok.peek() == '}':
      return 'pass'
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

  def createstatement(self, tok):
    "A statement to create an object and use it: new Class().do()."
    name = tok.next()
    return self.assigninvoke(tok, name)

  def throwstatement(self, tok):
    "A statement to throw (raise) an exception."
    exception = tok.next()
    if exception == 'new':
      return 'raise ' + self.createstatement(tok)
    token = tok.next()
    if token == ';':
      return 'raise ' + exception
    Trace.error('Invalid throw statement: "throw ' + exception + ' ' + token + '"')
    return 'raise ' + exception

  def throwsdeclaration(self, tok):
    "A throws clause, should be ignored."
    name = tok.next()
    return ''

  def assigninvoke(self, tok, token = None):
    "An assignment or a method invocation."
    self.onelineblock()
    if not token:
      token = tok.current()
    token2 = tok.next()
    if token2 == '=':
      # assignment
      return token + ' = ' + self.parsevalue(tok)
    if token2 == '.':
      member = tok.next()
      return self.assigninvoke(tok, token + '.' + member)
    if token2 == '(':
      parens = self.parseinparens(tok)
      return self.assigninvoke(tok, token + parens)
    if token2 == '[':
      square = self.parseinsquare(tok)
      return self.assigninvoke(tok, token + square)
    if token2 == '{':
      # ignore anonymous class
      self.parseupto('}', tok)
      return token
    if token2 == ';':
      # finished invocation
      return token
    if token2 == '++':
      self.autoincreases.append(token)
      return self.assigninvoke(tok, token + ' + 1')
    if token2 == '--':
      self.autodecreases.append(token)
      return self.assigninvoke(tok, token + ' - 1')
    if token2 in tok.javasymbols:
      Trace.error('Unknown symbol ' + token2 + ' for ' + token)
      return '*error ' + token + ' ' + token2 + ' error*'
    token3 = tok.next()
    if token3 == ';':
      # a declaration; ignore
      return ''
    if token3 == '=':
      # declaration + assignment
      self.variables.append(token2)
      return token2 + ' = ' + self.parsevalue(tok)
    if token3 == '[':
      # array declaration
      self.parseupto(']', tok)
      return self.assigninvoke(tok, token2)
    Trace.error('Unknown combination ' + token + '+' + token2 + '+' + token3)
    return '*error ' + token + ' ' + token2 + ' ' + token + ' error*'

  def checkvariable(self, token):
    "Check if the token is a valid variable name."
    for char in token:
      if not Tokenizer.isalphanumeric(char):
        return False
    return True

  def onelineblock(self):
    "Check if a block was expected."
    if self.waitingforblock:
      self.waitingforblock = False
      self.depth -= 1

  def ignorestatement(self, tok):
    "Ignore a whole statement."
    while tok.current() != ';':
      tok.next()
    return None

  def autoincrease(self, tok):
    "Process a Java autoincrease (++)."
    variable = self.autoincreases.pop()
    return variable + ' += 1'

  def autodecrease(self, tok):
    "Process a Java autodecrease (--)."
    variable = self.autodecreases.pop()
    return variable + ' -= 1'

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
    token = self.membertoken(tok)
    name = self.membertoken(tok)
    if token == self.inclass and name == '(':
      # constructor
      return self.translatemethod(token, tok)
    after = tok.next()
    while after == '[':
      tok.checknext(']')
      after = tok.next()
    if after == ';':
      return self.translateemptyattribute(name)
    if after == '(':
      return self.translatemethod(name, tok)
    if after != '=':
      Trace.error('Weird token after member: ' + token + ' ' + name + ' ' + after)
    return self.translateattribute(name, tok)

  def membertoken(self, tok):
    "Get the next member token, excluding static, []..."
    token = tok.next()
    if token in ['static', 'synchronized', 'final']:
      return self.membertoken(tok)
    if token == '[':
      tok.checknext(']')
      return self.membertoken(tok)
    return token

  def translatemethod(self, name, tok):
    "Translate a class method."
    self.inmethod = name
    pars = self.listparameters(tok)
    self.expectblock()
    parlist = ', '
    for par in pars:
      if not ' ' in par:
        Trace.error('Invalid parameter declaration: ' + par)
      else:
        newpar = par.strip().split(' ', 1)[1]
        parlist += newpar + ', '
    parlist = parlist[:-2]
    return '\ndef ' + name + '(self' + parlist + '):'

  def translateemptyattribute(self, name):
    "Translate an empty attribute definition."
    return name + ' = None'

  def translateattribute(self, name, tok):
    "Translate a class attribute."
    return name + ' = ' + self.parseupto(';', tok)

  def listparameters(self, tok):
    "Parse the parameters of a method definition, return them as a list."
    params = self.parseinparens(tok)[1:-1]
    pars = params.split(',')
    if pars[0] == '':
      return []
    return pars

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
    if tok.current() == '{':
      return '{' + self.parseupto('}', tok) + '}'
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
    return result

  def parseparens(self, tok):
    "Parse a couple of () and the contents inside."
    tok.checknext('(')
    return self.parseinparens(tok)

  def parseinparens(self, tok):
    "Parse the contents inside ()."
    contents = self.parseupto(')', tok)
    if '{' in contents:
      # anonymous function; ignore
      return '()'
    if Tokenizer.isalphanumeric(contents):
      if Tokenizer.isalphanumeric(tok.peek()):
        # type cast; ignore
        return ''
    result = '(' + contents + ')'
    return result
    result = self.parseinbrackets('(', ')', tok)

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
    parens = None
    return self.parseupto(ending, tok)
    if tok.peek() == '(':
      # type cast; ignore
      parens = self.parseparens(tok)
      if not parens[1:-1].isalpha():
        return parens + ' ' + self.parseupto(ending, tok)
    return self.parseupto(ending, tok)

  def parseupto(self, ending, tok):
    "Parse the tokenizer up to the supplied ending."
    return self.parsetoendings(tok, [ending])

  def parsetoendings(self, tok, endings):
    "Parse the tokenizer up to a number of endings."
    result = ''
    while not tok.next() in endings:
      processed = self.processtoken(tok)
      if processed != '.' and not result.endswith('.'):
        processed = ' ' + processed
      result += processed
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
    self.peeked = None

  def next(self):
    "Get the next single token, and store it for current()."
    if self.peeked:
      self.currenttoken = self.peeked
      self.peeked = None
    else:
      self.currenttoken = self.extractwithoutcomments()
    return self.currenttoken

  def checknext(self, token):
    "Check that the next token is the parameter."
    self.next()
    if self.currenttoken != token:
      Trace.error('Expected token ' + token + ', found ' + self.currenttoken)
      return False
    return True

  def extractwithoutcomments(self):
    "Get the next single token without comments."
    token = self.extracttoken()
    while token in self.comments:
      self.skipcomment(token)
      token = self.extracttoken()
    self.pos.skipspace()
    return token

  def extracttoken(self):
    "Extract the next token."
    if self.finished():
      return None
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

  def finished(self):
    "Find out if the tokenizer has finished tokenizing."
    self.pos.skipspace()
    return self.pos.finished()

  def isalphanumeric(cls, char):
    "Detect if a character is alphanumeric or underscore."
    if char.isalpha():
      return True
    if char.isdigit():
      return True
    if char == '_':
      return True
    return False

  def skipcomment(self, token):
    "Skip over a comment."
    if token == '//':
      comment = self.pos.globexcluding('\n')
      return
    if token == '/*':
      while not self.pos.checkskip('/'):
        comment = self.pos.globincluding('*')
      return
    Trace.error('Unknown comment type ' + token)
  
  def peek(self):
    "Look ahead at the next token, without advancing the parse position."
    token = self.extractwithoutcomments()
    self.peeked = token
    return token

  isalphanumeric = classmethod(isalphanumeric)

inputfile, outputfile = readargs(sys.argv)
Trace.debugmode = True
Trace.showlinesmode = True
if inputfile:
  JavaPorter().topy(inputfile, outputfile)
  Trace.message('Conversion done, running ' + outputfile)
  os.system('python ' + outputfile)


