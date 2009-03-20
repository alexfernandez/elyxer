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
# Alex 20090320
# eLyXer general configuration


class FormulaConfig(object):
  "Configuration for formulae"

  unmodified = ['.', '*', u'€', '(', ')', '[', ']', ':']
  modified = {'\'':u'’', '=':u' = ', ' ':'', '<':u' &lt; ', '-':u' − ', '+':u' + ',
      ',':u', ', '/':u' ⁄ '}
  commands = {'\\, ':' ', '\\%':'%', '\\prime':u'′', '\\times':u' × ',
      '\\rightarrow':u' → ', '\\lambda':u'λ', '\\propto':u' ∝ ',
      '\\tilde{n}':u'ñ', '\\cdot':u'⋅', '\\approx':u' ≈ ',
      '\\rightsquigarrow':u' ⇝ ', '\\dashrightarrow':u' ⇢ ', '\\sim':u' ~ ',
      '\\pm':u'±', '\\Delta':u'Δ', '\\sum':u'∑', '\\sigma':u'σ',
      '\\beta':u'β', '\\acute{o}':u'ó', '\\acute{a}':u'á', '\\implies':u'  ⇒  ',
      '\\pi':u'π', '\\infty':u'∞', '\\left(':u'<span class="bigsymbol">(</span>',
      '\\right)':u'<span class="bigsymbol">)</span>',
      '\\intop':u'∫', '\\log':'log', '\\exp':'exp', '\\_':'_', '\\\\':'<br/>',
      '\\not':u'¬', '\\ln':'ln', '\\blacktriangleright':u'▶', '\\bullet':u'•',
      '\\dagger':u'†', '\\ddagger':u'‡', '\\bigstar':u'★'}
  onefunctions = {'\\mathsf':'span class="mathsf"', '\\mathbf':'b', '^':'sup',
      '_':'sub', '\\underline':'u', '\\overline':'span class="overline"',
      '\\dot':'span class="overdot"', '\\sqrt':'span class="sqrt"',
      '\\bar':'span class="bar"', '\\mbox':'span class="mbox"',
      '\\textrm':'span class="mathrm"', '\\mathrm':'span class="mathrm"',
      '\\text':'span class="text"', '\\textipa':'span class="textipa"'}
  twofunctions = {
      '\\frac':['span class="fraction"', 'span class="numerator"', 'span class="denominator"'],
      '\\nicefrac':['span class="fraction"', 'span class="numerator"', 'span class="denominator"']
      }

class ContainerConfig(object):
  "Configuration for containers"

  escapes = {'&':'&amp;', '<':'&lt;', '>':'&gt;'}
  replaces = { '`':u'‘', '\'':u'’', '\n':'', '--':u'—' }
  commands = { '\\SpecialChar \\ldots{}':u'…', '\\InsetSpace ~':'&nbsp;',
      '\\InsetSpace \\space{}':'&nbsp;', '\\InsetSpace \\thinspace{}':u' ',
      '\\backslash':'\\', '\\SpecialChar \\@.':'.',
      '\\SpecialChar \\menuseparator':u'&nbsp;▷&nbsp;',
      '\\SpecialChar \\textcompwordmark{}':u'', '\\SpecialChar \\nobreakdash-':'-',
      '\\SpecialChar \\slash{}':'/'}

class BlackBoxConfig(object):
  "A container that does not output anything"

  starts = ['\\lyxformat', '\\begin_document', '\\begin_body',
      '\\family default', '\\color inherit',
      '\\shape default', '\\series default', '\\emph off',
      '\\bar no', '\\noun off', '\\emph default', '\\bar default',
      '\\noun default', '\\family roman', '\\series medium',
      '\\shape up', '\\size normal', '\\color none', '#LyX', '\\noindent',
      '\\labelwidthstring', '\\paragraph_spacing']

