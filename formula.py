#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090207
# Generate custom HTML version from Lyx document
# Formula processing

import sys
sys.path.append('./elyxer')
from container import *
from trace import Trace


class Formula(Container):
  "A Latex formula"

  start = '\\begin_inset Formula'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TagOutput()

  def process(self):
    "Convert the formula to HTML"
    text = self.contents[0]
    original, result = self.convert(text, 0)
    #Trace.debug('Formula ' + original + ' -> ' + result)
    self.contents = result
    if self.header[0] == 'inline':
      self.tag = 'span class="formula"'
      self.breaklines = False
    else:
      self.tag = 'div class="formula"'
      self.breaklines = True

  unmodified = ['.', '*', u'€', '(', ')', '[', ']', ':']
  modified = {'\'':u'’', '=':u' = ', ' ':'', '<':u' &lt; ', '-':u' − ', '+':u' + ',
      ',':u', ', '/':u' ⁄ '}
  commands = {'\\, ':' ', '\\%':'%', '\\prime':u'’', '\\times':u' × ',
      '\\rightarrow':u' → ', '\\lambda':u'λ', '\\propto':u' ∝ ',
      '\\tilde{n}':u'ñ', '\\cdot':u'⋅', '\\approx':u' ≈ ',
      '\\rightsquigarrow':u' ⇝ ', '\\dashrightarrow':u' ⇢ ', '\\sim':u' ~ ',
      '\\pm':u'±', '\\Delta':u'Δ', '\\sum':u'∑', '\\sigma':u'σ',
      '\\beta':u'β', '\\acute{o}':u'ó', '\\acute{a}':u'á', '\\implies':u'  ⇒  ',
      '\\pi':u'π', '\\infty':u'∞', '\\left(':u'<span class="bigsymbol">(</span>',
      '\\right)':u'<span class="bigsymbol">)</span>',
      '\\intop':u'∫', '\\log':'log', '\\exp':'exp'}
  onefunctions = {'\\mathsf':'span class="mathsf"', '\\mathbf':'b', '^':'sup',
      '_':'sub', '\\underline':'u', '\\overline':'span class="overline"',
      '\\dot':'span class="overdot"', '\\sqrt':'span class="sqrt"',
      '\\bar':'span class="bar"', '\\mbox':'span class="mbox"',
      '\\textrm':'span class="mathrm"'}
  twofunctions = {
      '\\frac':['span class="fraction"', 'span class="numerator"', 'span class="denominator"'],
      '\\nicefrac':['span class="fraction"', 'span class="numerator"', 'span class="denominator"']
      }
  
  def convert(self, text, pos):
    "Convert a bit of text to HTML"
    processed = ''
    result = list()
    while pos < len(text) and text[pos] != '}':
      original, converted = self.convertchars(text, pos)
      #Trace.debug('converted: ' + unicode(converted))
      processed += original
      pos += len(original)
      result += converted
    return processed, result

  def convertchars(self, text, pos):
    "Convert one or more characters, return the conversion"
    #Trace.debug('Formula ' + text + ' @' + str(pos))
    for reader in Formula.readers:
      bit, result = reader(self, text, pos)
      if bit:
        return bit, result
    Trace.error('Unrecognized string in ' + unicode(text[pos:]))
    return '\\', [Constant('\\')]

  def readalpha(self, text, pos):
    "Read alphabetic sequence"
    alpha = str()
    while pos < len(text) and text[pos].isalpha():
      alpha += text[pos]
      pos += 1
    return alpha, [TaggedText().constant(alpha, 'i')]

  def readsymbols(self, text, pos):
    "Read a string of symbols"
    symbols = unicode()
    result = unicode()
    while pos + len(symbols) < len(text):
      char = text[pos + len(symbols)]
      if char.isdigit() or char in Formula.unmodified:
        symbols += char
        result += char
      elif char in Formula.modified:
        symbols += char
        result += Formula.modified[char]
      else:
        break
    if len(symbols) == 0:
      return None, None
    return symbols, [Constant(result)]

  def command(self, text, pos):
    "read a command"
    command, translated = self.find(text, pos, Formula.commands)
    if not command:
      return None, None
    return command, [Constant(translated)]

  def readone(self, text, pos):
    "read a one-parameter function"
    function, tag = self.find(text, pos, Formula.onefunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket, result = self.readbracket(text, pos)
    return function + bracket, [TaggedText().complete(result, tag)]

  def readtwo(self, text, pos):
    "read a two-parameter function"
    function, tags = self.find(text, pos, Formula.twofunctions)
    if not function:
      return None, None
    pos += len(function)
    bracket1, result1 = self.readbracket(text, pos)
    pos += len(bracket1)
    bracket2, result2 = self.readbracket(text, pos)
    original =  function + bracket1 + bracket2
    tagged1 = TaggedText().complete(result1, tags[1])
    tagged2 = TaggedText().complete(result2, tags[2])
    tagged0 = TaggedText().complete([tagged1, tagged2], tags[0])
    return original, [tagged0]

  def readbracket(self, text, pos):
    "Read a bracket as {result}"
    if text[pos] != u'{':
      Trace.error(u'Missing { in ' + text + '@' + str(pos))
      return '', [Constant('')]
    original, converted = self.convert(text, pos + 1)
    if text[pos + 1 + len(original)] != u'}':
      Trace.error(u'Missing } in ' + text + '@' + str(pos))
    return '{' + original + '}', converted

  def find(self, text, pos, map):
    "Read TeX command or function"
    bit = text[pos:]
    for element in map:
      if bit.startswith(element):
        return element, map[element]
    return None, []

  readers = [readalpha, readsymbols, command, readone, readtwo]

