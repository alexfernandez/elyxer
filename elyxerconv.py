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
# Alex 20090913
# eLyXer document processing
# http://www.nongnu.org/elyxer/





import sys

class Trace(object):
  "A tracing class"

  debugmode = False
  quietmode = False
  showlinesmode = False

  prefix = None

  def debug(cls, message):
    "Show a debug message"
    if not Trace.debugmode or Trace.quietmode:
      return
    Trace.show(message, sys.stdout)

  def message(cls, message):
    "Show a trace message"
    if Trace.quietmode:
      return
    if Trace.prefix and Trace.showlinesmode:
      message = Trace.prefix + message
    Trace.show(message, sys.stdout)

  def error(cls, message):
    "Show an error message"
    if Trace.prefix and Trace.showlinesmode:
      message = Trace.prefix + message
    Trace.show(message, sys.stderr)

  def fatal(cls, message):
    "Show an error message and terminate"
    Trace.error('FATAL: ' + message)
    exit(-1)

  def show(cls, message, channel):
    "Show a message out of a channel"
    message = message.encode('utf-8')
    channel.write(message + '\n')

  debug = classmethod(debug)
  message = classmethod(message)
  error = classmethod(error)
  fatal = classmethod(fatal)
  show = classmethod(show)




import sys
import codecs


class LineReader(object):
  "Reads a file line by line"

  def __init__(self, filename):
    if isinstance(filename, file):
      self.file = filename
    else:
      self.file = codecs.open(filename, 'rU', "utf-8")
    self.linenumber = 0
    self.current = None
    self.mustread = True
    self.depleted = False

  def currentline(self):
    "Get the current line"
    if self.mustread:
      self.readline()
    return self.current

  def nextline(self):
    "Go to next line"
    if self.depleted:
      Trace.fatal('Read beyond file end')
    self.mustread = True

  def readline(self):
    "Read a line from file"
    self.current = self.file.readline()
    if self.file == sys.stdin:
      self.current = self.current.decode('utf-8')
    if len(self.current) == 0:
      self.depleted = True
    self.current = self.current.rstrip('\n\r')
    self.linenumber += 1
    self.mustread = False
    Trace.prefix = 'Line ' + unicode(self.linenumber) + ': '
    if self.linenumber % 1000 == 0:
      Trace.message('Parsing')

  def finished(self):
    "Find out if the file is finished"
    if self.mustread:
      self.readline()
    return self.depleted

  def close(self):
    self.file.close()

class LineWriter(object):
  "Writes a file as a series of lists"

  def __init__(self, filename):
    if isinstance(filename, file):
      self.file = filename
    else:
      self.file = codecs.open(filename, 'w', "utf-8")

  def write(self, strings):
    "Write a list of strings"
    for string in strings:
      if not isinstance(string, basestring):
        Trace.error('Not a string: ' + unicode(string) + ' in ' + unicode(strings))
        return
      self.writestring(string)

  def writestring(self, string):
    "Write a string"
    if self.file == sys.stdout:
      string = string.encode('utf-8')
    self.file.write(string)

  def writeline(self, line):
    "Write a line to file"
    self.writestring(line + '\n')

  def close(self):
    self.file.close()




import codecs



import codecs


class BibStylesConfig(object):
  "Configuration class from config file"

  authordate2 = {
      
      u'@article':u'$author. $year. $title. <i>$journal</i>, <b>$volume</b>($number), $pages.', 
      u'@book':u'$author. $year. <i>$title</i>. $publisher.', 
      u'default':u'$author. $year. <i>$title</i>. $publisher.', 
      }

  default = {
      u'@article':u'$author, “$title”, <i>$journal</i>, pp. $pages, $year.', 
      u'@book':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@booklet':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@conference':u'$author, “$title”, <i>$journal</i>, pp. $pages, $year.', 
      u'@inbook':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@incollection':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@inproceedings':u'$author, “$title”, <i>$journal</i>, pp. $pages, $year.', 
      u'@manual':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@mastersthesis':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@misc':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@phdthesis':u'$author, <i>$title</i>. $publisher, $year.', 
      u'@proceedings':u'$author, “$title”, <i>$journal</i>, pp. $pages, $year.', 
      u'@techreport':u'$author, <i>$title</i>, $year.', 
      u'@unpublished':u'$author, “$title”, <i>$journal</i>, $year.', 
      u'default':u'$author, <i>$title</i>. $publisher, $year.', 
      }

  ieeetr = {
      
      u'@article':u'$author, “$title”, <i>$journal</i>, vol. $volume, no. $number, pp. $pages, $year.', 
      u'@book':u'$author, <i>$title</i>. $publisher, $year.', 
      }

  plain = {
      
      u'@article':u'$author. $title. <i>$journal</i>, $volumen($number):$pages, $year.', 
      u'@book':u'$author. <i>$title</i>. $publisher, $month $year.', 
      u'default':u'$author. <i>$title</i>. $publisher, $year.', 
      }

class ContainerConfig(object):
  "Configuration class from config file"

  endings = {
      u'Align':u'\\end_layout', u'BarredText':u'\\bar', 
      u'BoldText':u'\\series', u'Cell':u'</cell', u'ColorText':u'\\color', 
      u'EmphaticText':u'\\emph', u'Hfill':u'\\hfill', u'Inset':u'\\end_inset', 
      u'Layout':u'\\end_layout', u'LyxFooter':u'\\end_document', 
      u'LyxHeader':u'\\end_header', u'Row':u'</row', u'ShapedText':u'\\shape', 
      u'SizeText':u'\\size', u'TextFamily':u'\\family', 
      u'VersalitasText':u'\\noun', 
      }

  header = {
      u'branch':u'\\branch', u'endbranch':u'\\end_branch', 
      u'pdftitle':u'\\pdf_title', 
      }

  startendings = {
      u'\\begin_deeper':u'\\end_deeper', u'\\begin_inset':u'\\end_inset', 
      u'\\begin_layout':u'\\end_layout', 
      }

  starts = {
      u'':u'StringContainer', u'#LyX':u'BlackBox', u'</lyxtabular':u'BlackBox', 
      u'<cell':u'Cell', u'<column':u'Column', u'<row':u'Row', 
      u'\\align':u'Align', u'\\bar':u'BarredText', 
      u'\\bar default':u'BlackBox', u'\\bar no':u'BlackBox', 
      u'\\begin_body':u'BlackBox', u'\\begin_deeper':u'DeeperList', 
      u'\\begin_document':u'BlackBox', u'\\begin_header':u'LyxHeader', 
      u'\\begin_inset':u'Inset', u'\\begin_inset Box':u'BoxInset', 
      u'\\begin_inset Branch':u'Branch', u'\\begin_inset Caption':u'Caption', 
      u'\\begin_inset CommandInset bibitem':u'BiblioEntry', 
      u'\\begin_inset CommandInset bibtex':u'BibTeX', 
      u'\\begin_inset CommandInset citation':u'BiblioCite', 
      u'\\begin_inset CommandInset href':u'URL', 
      u'\\begin_inset CommandInset index_print':u'PrintIndex', 
      u'\\begin_inset CommandInset label':u'Label', 
      u'\\begin_inset CommandInset nomencl_print':u'NomenclaturePrint', 
      u'\\begin_inset CommandInset nomenclature':u'NomenclatureEntry', 
      u'\\begin_inset CommandInset ref':u'Reference', 
      u'\\begin_inset CommandInset toc':u'TableOfContents', 
      u'\\begin_inset ERT':u'ERT', 
      u'\\begin_inset Flex CharStyle:Code':u'FlexCode', 
      u'\\begin_inset Flex URL':u'FlexURL', u'\\begin_inset Float':u'Float', 
      u'\\begin_inset FloatList':u'ListOf', u'\\begin_inset Foot':u'Footnote', 
      u'\\begin_inset Formula':u'Formula', u'\\begin_inset Graphics':u'Image', 
      u'\\begin_inset Index':u'IndexEntry', u'\\begin_inset Info':u'InfoInset', 
      u'\\begin_inset LatexCommand bibitem':u'BiblioEntry', 
      u'\\begin_inset LatexCommand bibtex':u'BibTeX', 
      u'\\begin_inset LatexCommand cite':u'BiblioCite', 
      u'\\begin_inset LatexCommand citealt':u'BiblioCite', 
      u'\\begin_inset LatexCommand citep':u'BiblioCite', 
      u'\\begin_inset LatexCommand citet':u'BiblioCite', 
      u'\\begin_inset LatexCommand htmlurl':u'URL', 
      u'\\begin_inset LatexCommand index':u'IndexEntry', 
      u'\\begin_inset LatexCommand label':u'Label', 
      u'\\begin_inset LatexCommand nomenclature':u'NomenclatureEntry', 
      u'\\begin_inset LatexCommand prettyref':u'Reference', 
      u'\\begin_inset LatexCommand printindex':u'PrintIndex', 
      u'\\begin_inset LatexCommand printnomenclature':u'NomenclaturePrint', 
      u'\\begin_inset LatexCommand ref':u'Reference', 
      u'\\begin_inset LatexCommand tableofcontents':u'TableOfContents', 
      u'\\begin_inset LatexCommand url':u'URL', 
      u'\\begin_inset LatexCommand vref':u'Reference', 
      u'\\begin_inset Marginal':u'Footnote', 
      u'\\begin_inset Newline':u'NewlineInset', u'\\begin_inset Note':u'Note', 
      u'\\begin_inset OptArg':u'ShortTitle', 
      u'\\begin_inset Quotes':u'QuoteContainer', 
      u'\\begin_inset Tabular':u'Table', u'\\begin_inset Text':u'InsetText', 
      u'\\begin_inset Wrap':u'Wrap', u'\\begin_inset listings':u'Listing', 
      u'\\begin_inset space':u'Space', u'\\begin_layout':u'Layout', 
      u'\\begin_layout Abstract':u'Abstract', 
      u'\\begin_layout Author':u'Author', 
      u'\\begin_layout Bibliography':u'Bibliography', 
      u'\\begin_layout Description':u'Description', 
      u'\\begin_layout Enumerate':u'ListItem', 
      u'\\begin_layout Itemize':u'ListItem', u'\\begin_layout List':u'List', 
      u'\\begin_layout Plain':u'PlainLayout', 
      u'\\begin_layout Standard':u'StandardLayout', 
      u'\\begin_layout Title':u'Title', u'\\color':u'ColorText', 
      u'\\color inherit':u'BlackBox', u'\\color none':u'BlackBox', 
      u'\\emph default':u'BlackBox', u'\\emph off':u'BlackBox', 
      u'\\emph on':u'EmphaticText', u'\\end_body':u'LyxFooter', 
      u'\\family':u'TextFamily', u'\\family default':u'BlackBox', 
      u'\\family roman':u'BlackBox', u'\\hfill':u'Hfill', 
      u'\\labelwidthstring':u'BlackBox', u'\\lang':u'LangLine', 
      u'\\length':u'BlackBox', u'\\lyxformat':u'LyXFormat', 
      u'\\lyxline':u'LyxLine', u'\\newline':u'Newline', 
      u'\\newpage':u'NewPage', u'\\noindent':u'BlackBox', 
      u'\\noun default':u'BlackBox', u'\\noun off':u'BlackBox', 
      u'\\noun on':u'VersalitasText', u'\\paragraph_spacing':u'BlackBox', 
      u'\\series bold':u'BoldText', u'\\series default':u'BlackBox', 
      u'\\series medium':u'BlackBox', u'\\shape':u'ShapedText', 
      u'\\shape default':u'BlackBox', u'\\shape up':u'BlackBox', 
      u'\\size':u'SizeText', u'\\size normal':u'BlackBox', 
      u'\\start_of_appendix':u'Appendix', 
      }

  string = {
      u'startcommand':u'\\', 
      }

  table = {
      u'headers':[u'<lyxtabular',u'<features',], 
      }

class EscapeConfig(object):
  "Configuration class from config file"

  chars = {
      u'\n':u'', u' -- ':u' — ', u'\'':u'’', u'`':u'‘', 
      }

  commands = {
      u'\\InsetSpace \\space{}':u'&nbsp;', u'\\InsetSpace \\thinspace{}':u' ', 
      u'\\InsetSpace ~':u'&nbsp;', u'\\SpecialChar \\-':u'', 
      u'\\SpecialChar \\@.':u'.', u'\\SpecialChar \\ldots{}':u'…', 
      u'\\SpecialChar \\menuseparator':u'&nbsp;▷&nbsp;', 
      u'\\SpecialChar \\nobreakdash-':u'-', u'\\SpecialChar \\slash{}':u'/', 
      u'\\SpecialChar \\textcompwordmark{}':u'', u'\\backslash':u'\\', 
      }

  entities = {
      u'&':u'&amp;', u'<':u'&lt;', u'>':u'&gt;', 
      }

  html = {
      u'/>':u'>', 
      }

  nonunicode = {
      u' ':u' ', 
      }

class FileConfig(object):
  "Configuration class from config file"

  parsing = {
      u'encodings':[u'utf-8',u'Cp1252',], 
      }

class FootnoteConfig(object):
  "Configuration class from config file"

  constants = {
      u'postfrom':u'] ', u'postto':u'→] ', u'prefrom':u'[→', u'preto':u' [', 
      }

class FormulaConfig(object):
  "Configuration class from config file"

  alphacommands = {
      u'\\Delta':u'Δ', u'\\Gamma':u'Γ', u'\\Upsilon':u'Υ', u'\\acute{A}':u'Á', 
      u'\\acute{E}':u'É', u'\\acute{I}':u'Í', u'\\acute{O}':u'Ó', 
      u'\\acute{U}':u'Ú', u'\\acute{a}':u'á', u'\\acute{e}':u'é', 
      u'\\acute{i}':u'í', u'\\acute{o}':u'ó', u'\\acute{u}':u'ú', 
      u'\\alpha':u'α', u'\\beta':u'β', u'\\delta':u'δ', u'\\epsilon':u'ε', 
      u'\\gamma':u'γ', u'\\lambda':u'λ', u'\\mu':u'μ', u'\\nu':u'ν', 
      u'\\pi':u'π', u'\\sigma':u'σ', u'\\tau':u'τ', u'\\tilde{N}':u'Ñ', 
      u'\\tilde{n}':u'ñ', u'\\varphi':u'φ', 
      }

  array = {
      u'begin':u'\\begin', u'cellseparator':u'&', u'end':u'\\end', 
      u'rowseparator':u'\\\\', 
      }

  commands = {
      u'\\!':u'', u'\\%':u'%', u'\\,':u' ', u'\\:':u' ', u'\\CIRCLE':u'●', 
      u'\\CheckedBox':u'☑', u'\\Circle':u'○', u'\\Delta':u'Δ', 
      u'\\Downarrow':u'⇓', u'\\Gamma':u'Γ', u'\\Im':u'ℑ', u'\\LEFTCIRCLE':u'◖', 
      u'\\LEFTcircle':u'◐', u'\\Lambda':u'Λ', u'\\Leftarrow':u'⇐', 
      u'\\Leftrightarrow':u' ⇔ ', u'\\Longleftarrow':u'⟸', 
      u'\\Longrightarrow':u'⟹', u'\\Omega':u'Ω', u'\\Phi':u'Φ', u'\\Pi':u'Π', 
      u'\\Pr':u'Pr', u'\\Psi':u'Ψ', u'\\RIGHTCIRCLE':u'◗', 
      u'\\RIGHTcircle':u'◑', u'\\Re':u'ℜ', u'\\Rightarrow':u' ⇒ ', 
      u'\\Sigma':u'Σ', u'\\Square':u'☐', u'\\Theta':u'Θ', u'\\Uparrow':u'⇑', 
      u'\\Updownarrow':u'⇕', u'\\Upsilon':u'Υ', u'\\XBox':u'☒', u'\\Xi':u'Ξ', 
      u'\\\\':u'<br/>', u'\\_':u'_', u'\\acute{A}':u'Á', u'\\acute{C}':u'Ć', 
      u'\\acute{E}':u'É', u'\\acute{G}':u'Ǵ', u'\\acute{I}':u'Í', 
      u'\\acute{K}':u'Ḱ', u'\\acute{L}':u'Ĺ', u'\\acute{M}':u'Ḿ', 
      u'\\acute{N}':u'Ń', u'\\acute{O}':u'Ó', u'\\acute{P}':u'Ṕ', 
      u'\\acute{R}':u'Ŕ', u'\\acute{S}':u'Ś', u'\\acute{U}':u'Ú', 
      u'\\acute{W}':u'Ẃ', u'\\acute{Y}':u'Ý', u'\\acute{Z}':u'Ź', 
      u'\\acute{a}':u'á', u'\\acute{c}':u'ć', u'\\acute{e}':u'é', 
      u'\\acute{g}':u'ǵ', u'\\acute{k}':u'ḱ', u'\\acute{l}':u'ĺ', 
      u'\\acute{m}':u'ḿ', u'\\acute{n}':u'ń', u'\\acute{o}':u'ó', 
      u'\\acute{p}':u'ṕ', u'\\acute{r}':u'ŕ', u'\\acute{s}':u'ś', 
      u'\\acute{u}':u'ú', u'\\acute{w}':u'ẃ', u'\\acute{y}':u'ý', 
      u'\\acute{z}':u'ź', u'\\aleph':u'ℵ', u'\\alpha':u'α', u'\\amalg':u'∐', 
      u'\\angle':u'∠', u'\\approx':u' ≈ ', u'\\aquarius':u'♒', 
      u'\\arccos':u'arccos', u'\\arcsin':u'arcsin', u'\\arctan':u'arctan', 
      u'\\arg':u'arg', u'\\aries':u'♈', u'\\ast':u'∗', u'\\asymp':u'≍', 
      u'\\backslash':u'\\', u'\\bar{A}':u'Ā', u'\\bar{E}':u'Ē', 
      u'\\bar{I}':u'Ī', u'\\bar{O}':u'Ō', u'\\bar{U}':u'Ū', u'\\bar{Y}':u'Ȳ', 
      u'\\bar{a}':u'ā', u'\\bar{e}':u'ē', u'\\bar{o}':u'ō', u'\\bar{u}':u'ū', 
      u'\\bar{y}':u'ȳ', u'\\beta':u'β', u'\\beth':u'ℶ', u'\\bigcap':u'∩', 
      u'\\bigcirc':u'○', u'\\bigcup':u'∪', u'\\bigodot':u'⊙', 
      u'\\bigoplus':u'⊕', u'\\bigotimes':u'⊗', u'\\bigsqcup':u'⊔', 
      u'\\bigstar':u'★', u'\\biguplus':u'⊎', u'\\bigvee':u'∨', 
      u'\\bigwedge':u'∧', u'\\blacksmiley':u'☻', u'\\blacktriangleright':u'▶', 
      u'\\bot':u'⊥', u'\\bowtie':u'⋈', u'\\box':u'▫', u'\\breve{A}':u'Ă', 
      u'\\breve{E}':u'Ĕ', u'\\breve{G}':u'Ğ', u'\\breve{I}':u'Ĭ', 
      u'\\breve{O}':u'Ŏ', u'\\breve{U}':u'Ŭ', u'\\breve{a}':u'ă', 
      u'\\breve{e}':u'ĕ', u'\\breve{g}':u'ğ', u'\\breve{o}':u'ŏ', 
      u'\\breve{u}':u'ŭ', u'\\bullet':u'•', u'\\cancer':u'♋', u'\\cap':u'∩', 
      u'\\capricornus':u'♑', u'\\cdot':u'⋅', u'\\cdots':u'⋯', 
      u'\\cedilla{C}':u'Ç', u'\\cedilla{D}':u'Ḑ', u'\\cedilla{E}':u'Ȩ', 
      u'\\cedilla{G}':u'Ģ', u'\\cedilla{H}':u'Ḩ', u'\\cedilla{K}':u'Ķ', 
      u'\\cedilla{L}':u'Ļ', u'\\cedilla{N}':u'Ņ', u'\\cedilla{R}':u'Ŗ', 
      u'\\cedilla{S}':u'Ş', u'\\cedilla{T}':u'Ţ', u'\\cedilla{c}':u'ç', 
      u'\\cedilla{d}':u'ḑ', u'\\cedilla{e}':u'ȩ', u'\\cedilla{h}':u'ḩ', 
      u'\\cedilla{k}':u'ķ', u'\\cedilla{l}':u'ļ', u'\\cedilla{n}':u'ņ', 
      u'\\cedilla{r}':u'ŗ', u'\\cedilla{s}':u'ş', u'\\cedilla{t}':u'ţ', 
      u'\\centerdot':u'∙', u'\\check{A}':u'Ǎ', u'\\check{C}':u'Č', 
      u'\\check{D}':u'Ď', u'\\check{E}':u'Ě', u'\\check{G}':u'Ǧ', 
      u'\\check{H}':u'Ȟ', u'\\check{I}':u'Ǐ', u'\\check{K}':u'Ǩ', 
      u'\\check{N}':u'Ň', u'\\check{O}':u'Ǒ', u'\\check{R}':u'Ř', 
      u'\\check{S}':u'Š', u'\\check{T}':u'Ť', u'\\check{U}':u'Ǔ', 
      u'\\check{Z}':u'Ž', u'\\check{a}':u'ǎ', u'\\check{c}':u'č', 
      u'\\check{d}':u'ď', u'\\check{e}':u'ě', u'\\check{g}':u'ǧ', 
      u'\\check{h}':u'ȟ', u'\\check{k}':u'ǩ', u'\\check{n}':u'ň', 
      u'\\check{o}':u'ǒ', u'\\check{r}':u'ř', u'\\check{s}':u'š', 
      u'\\check{u}':u'ǔ', u'\\check{z}':u'ž', u'\\chi':u'χ', u'\\circ':u'○', 
      u'\\clubsuit':u'♣', u'\\cong':u'≅', u'\\coprod':u'∐', u'\\cos':u'cos', 
      u'\\cosh':u'cosh', u'\\cot':u'cot', u'\\coth':u'coth', u'\\csc':u'csc', 
      u'\\cup':u'∪', u'\\dacute{O}':u'Ő', u'\\dacute{U}':u'Ű', 
      u'\\dacute{o}':u'ő', u'\\dacute{u}':u'ű', u'\\dagger':u'†', 
      u'\\daleth':u'ℸ', u'\\dashrightarrow':u' ⇢ ', u'\\dashv':u'⊣', 
      u'\\ddagger':u'‡', u'\\ddots':u'⋱', u'\\ddot{A}':u'Ä', u'\\ddot{E}':u'Ë', 
      u'\\ddot{H}':u'Ḧ', u'\\ddot{I}':u'Ï', u'\\ddot{O}':u'Ö', 
      u'\\ddot{U}':u'Ü', u'\\ddot{W}':u'Ẅ', u'\\ddot{X}':u'Ẍ', 
      u'\\ddot{Y}':u'Ÿ', u'\\ddot{a}':u'ä', u'\\ddot{e}':u'ë', 
      u'\\ddot{h}':u'ḧ', u'\\ddot{o}':u'ö', u'\\ddot{t}':u'ẗ', 
      u'\\ddot{u}':u'ü', u'\\ddot{w}':u'ẅ', u'\\ddot{x}':u'ẍ', 
      u'\\ddot{y}':u'ÿ', u'\\deg':u'deg', u'\\delta':u'δ', u'\\det':u'det', 
      u'\\dgrave{A}':u'Ȁ', u'\\dgrave{E}':u'Ȅ', u'\\dgrave{I}':u'Ȉ', 
      u'\\dgrave{O}':u'Ȍ', u'\\dgrave{R}':u'Ȑ', u'\\dgrave{U}':u'Ȕ', 
      u'\\dgrave{a}':u'ȁ', u'\\dgrave{e}':u'ȅ', u'\\dgrave{o}':u'ȍ', 
      u'\\dgrave{r}':u'ȑ', u'\\dgrave{u}':u'ȕ', u'\\diamond':u'◇', 
      u'\\diamondsuit':u'♦', u'\\dim':u'dim', u'\\displaystyle':u'', 
      u'\\div':u'÷', u'\\doteq':u'≐', u'\\dot{A}':u'Ȧ', u'\\dot{B}':u'Ḃ', 
      u'\\dot{C}':u'Ċ', u'\\dot{D}':u'Ḋ', u'\\dot{E}':u'Ė', u'\\dot{F}':u'Ḟ', 
      u'\\dot{G}':u'Ġ', u'\\dot{H}':u'Ḣ', u'\\dot{I}':u'İ', u'\\dot{M}':u'Ṁ', 
      u'\\dot{N}':u'Ṅ', u'\\dot{O}':u'Ȯ', u'\\dot{P}':u'Ṗ', u'\\dot{R}':u'Ṙ', 
      u'\\dot{S}':u'Ṡ', u'\\dot{T}':u'Ṫ', u'\\dot{W}':u'Ẇ', u'\\dot{X}':u'Ẋ', 
      u'\\dot{Y}':u'Ẏ', u'\\dot{Z}':u'Ż', u'\\dot{a}':u'ȧ', u'\\dot{b}':u'ḃ', 
      u'\\dot{c}':u'ċ', u'\\dot{d}':u'ḋ', u'\\dot{e}':u'ė', u'\\dot{f}':u'ḟ', 
      u'\\dot{g}':u'ġ', u'\\dot{h}':u'ḣ', u'\\dot{m}':u'ṁ', u'\\dot{n}':u'ṅ', 
      u'\\dot{o}':u'ȯ', u'\\dot{p}':u'ṗ', u'\\dot{r}':u'ṙ', u'\\dot{s}':u'ṡ', 
      u'\\dot{t}':u'ṫ', u'\\dot{w}':u'ẇ', u'\\dot{x}':u'ẋ', u'\\dot{y}':u'ẏ', 
      u'\\dot{z}':u'ż', u'\\downarrow':u'↓', u'\\earth':u'♁', u'\\ell':u'ℓ', 
      u'\\emptyset':u'∅', u'\\epsilon':u'ε', u'\\equiv':u' ≡ ', u'\\eta':u'η', 
      u'\\exists':u'∃', u'\\exp':u'exp', u'\\female':u'♀', u'\\forall':u'∀', 
      u'\\frownie':u'☹', u'\\gamma':u'γ', u'\\gcd':u'gcd', u'\\ge':u' ≥ ', 
      u'\\gemini':u'♊', u'\\geq':u' ≥ ', u'\\gets':u'←', u'\\gg':u'≫', 
      u'\\gimel':u'ℷ', u'\\grave{A}':u'À', u'\\grave{E}':u'È', 
      u'\\grave{I}':u'Ì', u'\\grave{N}':u'Ǹ', u'\\grave{O}':u'Ò', 
      u'\\grave{U}':u'Ù', u'\\grave{W}':u'Ẁ', u'\\grave{Y}':u'Ỳ', 
      u'\\grave{a}':u'à', u'\\grave{e}':u'è', u'\\grave{n}':u'ǹ', 
      u'\\grave{o}':u'ò', u'\\grave{u}':u'ù', u'\\grave{w}':u'ẁ', 
      u'\\grave{y}':u'ỳ', u'\\hat{A}':u'Â', u'\\hat{C}':u'Ĉ', u'\\hat{E}':u'Ê', 
      u'\\hat{G}':u'Ĝ', u'\\hat{H}':u'Ĥ', u'\\hat{I}':u'Î', u'\\hat{J}':u'Ĵ', 
      u'\\hat{O}':u'Ô', u'\\hat{S}':u'Ŝ', u'\\hat{U}':u'Û', u'\\hat{W}':u'Ŵ', 
      u'\\hat{Y}':u'Ŷ', u'\\hat{Z}':u'Ẑ', u'\\hat{a}':u'â', u'\\hat{c}':u'ĉ', 
      u'\\hat{e}':u'ê', u'\\hat{g}':u'ĝ', u'\\hat{h}':u'ĥ', u'\\hat{o}':u'ô', 
      u'\\hat{s}':u'ŝ', u'\\hat{u}':u'û', u'\\hat{w}':u'ŵ', u'\\hat{y}':u'ŷ', 
      u'\\hat{z}':u'ẑ', u'\\hbar':u'ℏ', u'\\heartsuit':u'♥', u'\\hom':u'hom', 
      u'\\hookleftarrow':u'↩', u'\\hookrightarrow':u'↪', u'\\imath':u'ı', 
      u'\\implies':u'  ⇒  ', u'\\in':u' ∈ ', u'\\inf':u'inf', u'\\infty':u'∞', 
      u'\\int':u'<span class="bigsymbol">∫</span>', 
      u'\\intop':u'<span class="bigsymbol">∫</span>', u'\\invneg':u'⌐', 
      u'\\iota':u'ι', u'\\jmath':u'ȷ', u'\\jupiter':u'♃', u'\\kappa':u'κ', 
      u'\\ker':u'ker', u'\\lambda':u'λ', u'\\langle':u'⟨', u'\\ldots':u'…', 
      u'\\le':u'≤', u'\\leadsto':u'⇝', u'\\leftarrow':u' ← ', 
      u'\\leftharpoondown':u'↽', u'\\leftharpoonup':u'↼', u'\\leftmoon':u'☾', 
      u'\\leftrightarrow':u'↔', u'\\leo':u'♌', u'\\leq':u' ≤ ', u'\\lg':u'lg', 
      u'\\libra':u'♎', u'\\lim':u'lim', u'\\liminf':u'liminf', 
      u'\\limsup':u'limsup', u'\\ll':u'≪', u'\\ln':u'ln', u'\\log':u'log', 
      u'\\longleftarrow':u'⟵', u'\\longrightarrow':u'⟶', u'\\lozenge':u'◊', 
      u'\\lyxlock':u'', u'\\male':u'♂', u'\\mapsto':u'↦', u'\\mathbb{C}':u'ℂ', 
      u'\\mathbb{H}':u'ℍ', u'\\mathbb{N}':u'ℕ', u'\\mathbb{P}':u'ℙ', 
      u'\\mathbb{Q}':u'ℚ', u'\\mathbb{R}':u'ℝ', u'\\mathbb{Z}':u'ℤ', 
      u'\\mathfrak{C}':u'ℭ', u'\\mathfrak{H}':u'ℌ', u'\\mathfrak{I}':u'ℑ', 
      u'\\mathfrak{R}':u'ℜ', u'\\mathfrak{Z}':u'ℨ', u'\\mathring{A}':u'Å', 
      u'\\mathring{U}':u'Ů', u'\\mathring{a}':u'å', u'\\mathring{u}':u'ů', 
      u'\\mathring{w}':u'ẘ', u'\\mathring{y}':u'ẙ', u'\\mathscr{B}':u'ℬ', 
      u'\\mathscr{E}':u'ℰ', u'\\mathscr{F}':u'ℱ', u'\\mathscr{H}':u'ℋ', 
      u'\\mathscr{I}':u'ℐ', u'\\mathscr{L}':u'ℒ', u'\\mathscr{M}':u'ℳ', 
      u'\\mathscr{R}':u'ℛ', u'\\max':u'max', u'\\mercury':u'☿', u'\\mho':u'℧', 
      u'\\mid':u'∣', u'\\min':u'min', u'\\models':u'⊨', u'\\mp':u'∓', 
      u'\\mu':u'μ', u'\\nabla':u'∇', u'\\ne':u' ≠ ', u'\\nearrow':u'↗', 
      u'\\neg':u'¬', u'\\neptune':u'♆', u'\\neq':u' ≠ ', u'\\ni':u'∋', 
      u'\\nonumber':u'', u'\\not':u'¬', u'\\not\\in':u' ∉ ', u'\\nu':u'ν', 
      u'\\nwarrow':u'↖', u'\\odot':u'⊙', u'\\ogonek{A}':u'Ą', 
      u'\\ogonek{E}':u'Ę', u'\\ogonek{I}':u'Į', u'\\ogonek{O}':u'Ǫ', 
      u'\\ogonek{U}':u'Ų', u'\\ogonek{a}':u'ą', u'\\ogonek{e}':u'ę', 
      u'\\ogonek{i}':u'į', u'\\ogonek{o}':u'ǫ', u'\\ogonek{u}':u'ų', 
      u'\\oint':u'∮', u'\\omega':u'ω', u'\\ominus':u'⊖', u'\\oplus':u'⊕', 
      u'\\oslash':u'⊘', u'\\otimes':u'⊗', u'\\parallel':u'∥', 
      u'\\partial':u'∂', u'\\perp':u'⊥', u'\\phi':u'φ', u'\\pi':u'π', 
      u'\\pisces':u'♓', u'\\pluto':u'♇', u'\\pm':u'±', u'\\prec':u'≺', 
      u'\\preceq':u'≼', u'\\prime':u'′', 
      u'\\prod':u'<span class="bigsymbol">∏</span>', u'\\prompto':u'∝', 
      u'\\propto':u' ∝ ', u'\\psi':u'ψ', u'\\qquad':u'  ', u'\\quad':u' ', 
      u'\\quarternote':u'♩', u'\\rangle':u'⟩', u'\\rcap{A}':u'Ȃ', 
      u'\\rcap{E}':u'Ȇ', u'\\rcap{I}':u'Ȋ', u'\\rcap{O}':u'Ȏ', 
      u'\\rcap{R}':u'Ȓ', u'\\rcap{U}':u'Ȗ', u'\\rcap{a}':u'ȃ', 
      u'\\rcap{e}':u'ȇ', u'\\rcap{o}':u'ȏ', u'\\rcap{r}':u'ȓ', 
      u'\\rcap{u}':u'ȗ', u'\\rho':u'ρ', u'\\rightarrow':u' → ', 
      u'\\rightharpooondown':u'⇁', u'\\rightharpooonup':u'⇀', 
      u'\\rightleftharpoons':u'⇌', u'\\rightmoon':u'☽', 
      u'\\rightsquigarrow':u' ⇝ ', u'\\sagittarius':u'♐', u'\\saturn':u'♄', 
      u'\\scorpio':u'♏', u'\\scriptscriptstyle':u'', u'\\scriptstyle':u'', 
      u'\\searrow':u'↘', u'\\sec':u'sec', u'\\setminus':u'∖', u'\\sigma':u'σ', 
      u'\\sim':u' ~ ', u'\\simeq':u'≃', u'\\sin':u'sin', u'\\sinh':u'sinh', 
      u'\\slash':u'∕', u'\\slashed{O}':u'Ø', u'\\slashed{o}':u'ø', 
      u'\\smiley':u'☺', u'\\spadesuit':u'♠', u'\\sqcap':u'⊓', u'\\sqcup':u'⊔', 
      u'\\sqsubset':u'⊏', u'\\sqsubseteq':u'⊑', u'\\sqsupset':u'⊐', 
      u'\\sqsupseteq':u'⊒', u'\\square':u'□', u'\\star':u'⋆', 
      u'\\subdot{A}':u'Ạ', u'\\subdot{B}':u'Ḅ', u'\\subdot{D}':u'Ḍ', 
      u'\\subdot{E}':u'Ẹ', u'\\subdot{H}':u'Ḥ', u'\\subdot{I}':u'Ị', 
      u'\\subdot{K}':u'Ḳ', u'\\subdot{L}':u'Ḷ', u'\\subdot{M}':u'Ṃ', 
      u'\\subdot{N}':u'Ṇ', u'\\subdot{O}':u'Ọ', u'\\subdot{R}':u'Ṛ', 
      u'\\subdot{S}':u'Ṣ', u'\\subdot{T}':u'Ṭ', u'\\subdot{U}':u'Ụ', 
      u'\\subdot{V}':u'Ṿ', u'\\subdot{W}':u'Ẉ', u'\\subdot{Y}':u'Ỵ', 
      u'\\subdot{Z}':u'Ẓ', u'\\subdot{a}':u'ạ', u'\\subdot{b}':u'ḅ', 
      u'\\subdot{d}':u'ḍ', u'\\subdot{e}':u'ẹ', u'\\subdot{h}':u'ḥ', 
      u'\\subdot{i}':u'ị', u'\\subdot{k}':u'ḳ', u'\\subdot{l}':u'ḷ', 
      u'\\subdot{m}':u'ṃ', u'\\subdot{n}':u'ṇ', u'\\subdot{o}':u'ọ', 
      u'\\subdot{r}':u'ṛ', u'\\subdot{s}':u'ṣ', u'\\subdot{t}':u'ṭ', 
      u'\\subdot{u}':u'ụ', u'\\subdot{v}':u'ṿ', u'\\subdot{w}':u'ẉ', 
      u'\\subdot{y}':u'ỵ', u'\\subdot{z}':u'ẓ', u'\\subhat{D}':u'Ḓ', 
      u'\\subhat{E}':u'Ḙ', u'\\subhat{L}':u'Ḽ', u'\\subhat{N}':u'Ṋ', 
      u'\\subhat{T}':u'Ṱ', u'\\subhat{U}':u'Ṷ', u'\\subhat{d}':u'ḓ', 
      u'\\subhat{e}':u'ḙ', u'\\subhat{l}':u'ḽ', u'\\subhat{n}':u'ṋ', 
      u'\\subhat{t}':u'ṱ', u'\\subhat{u}':u'ṷ', u'\\subring{A}':u'Ḁ', 
      u'\\subring{a}':u'ḁ', u'\\subset':u' ⊂ ', u'\\subseteq':u'⊆', 
      u'\\subtilde{E}':u'Ḛ', u'\\subtilde{I}':u'Ḭ', u'\\subtilde{U}':u'Ṵ', 
      u'\\subtilde{e}':u'ḛ', u'\\subtilde{i}':u'ḭ', u'\\subtilde{u}':u'ṵ', 
      u'\\succ':u'≻', u'\\succeq':u'≽', 
      u'\\sum':u'<span class="bigsymbol">∑</span>', u'\\sun':u'☼', 
      u'\\sup':u'sup', u'\\supset':u' ⊃ ', u'\\supseteq':u'⊇', u'\\surd':u'√', 
      u'\\swarrow':u'↙', u'\\tan':u'tan', u'\\tanh':u'tanh', u'\\tau':u'τ', 
      u'\\taurus':u'♉', u'\\textstyle':u'', u'\\theta':u'θ', 
      u'\\tilde{A}':u'Ã', u'\\tilde{E}':u'Ẽ', u'\\tilde{I}':u'Ĩ', 
      u'\\tilde{N}':u'Ñ', u'\\tilde{O}':u'Õ', u'\\tilde{U}':u'Ũ', 
      u'\\tilde{V}':u'Ṽ', u'\\tilde{Y}':u'Ỹ', u'\\tilde{a}':u'ã', 
      u'\\tilde{e}':u'ẽ', u'\\tilde{n}':u'ñ', u'\\tilde{o}':u'õ', 
      u'\\tilde{u}':u'ũ', u'\\tilde{v}':u'ṽ', u'\\tilde{y}':u'ỹ', 
      u'\\times':u' × ', u'\\to':u'→', u'\\top':u'⊤', u'\\triangleleft':u'⊲', 
      u'\\triangleright':u'▷', u'\\twonotes':u'♫', u'\\unlhd':u'⊴', 
      u'\\unrhl':u'⊵', u'\\uparrow':u'↑', u'\\updownarrow':u'↕', 
      u'\\uplus':u'⊎', u'\\upsilon':u'υ', u'\\uranus':u'♅', 
      u'\\varclubsuit':u'♧', u'\\vardiamondsuit':u'♦', u'\\varheartsuit':u'♥', 
      u'\\varphi':u'φ', u'\\varpi':u'ϖ', u'\\varrho':u'ϱ', u'\\varsigma':u'ς', 
      u'\\varspadesuit':u'♤', u'\\vartheta':u'ϑ', u'\\vdash':u'⊢', 
      u'\\vee':u'∨', u'\\virgo':u'♍', u'\\wedge':u'∧', u'\\wp':u'℘', 
      u'\\wr':u'≀', u'\\xi':u'ξ', u'\\zeta':u'ζ', u'\\{':u'{', u'\\}':u'}', 
      }

  decoratingfunctions = {
      u'\\acute':u'´', u'\\breve':u'˘', u'\\check':u'ˇ', u'\\ddot':u'¨', 
      u'\\dot':u'˙', u'\\grave':u'`', u'\\hat':u'^', u'\\overleftarrow':u'⟵', 
      u'\\overrightarrow':u'⟶', u'\\tilde':u'˜', u'\\vec':u'→', 
      }

  endings = {
      u'bracket':u'}', u'complex':u'\\]', u'endafter':u'}', 
      u'endbefore':u'\\end{', u'squarebracket':u']', 
      }

  fontfunctions = {
      u'\\boldsymbol':u'b', u'\\mathbb':u'span class="blackboard"', 
      u'\\mathbf':u'b', u'\\mathcal':u'span class="script"', 
      u'\\mathfrak':u'span class="fraktur"', u'\\mathit':u'i', 
      u'\\mathrm':u'span class="mathrm"', u'\\mathsf':u'span class="mathsf"', 
      u'\\mathtt':u'tt', u'\\textrm':u'span class="mathrm"', 
      }

  fractionfunctions = {
      
      u'\\frac':[u'span class="fraction"',u'span class="numerator"',u'',u'span class="denominator"',], 
      u'\\nicefrac':[u'span class="fraction"',u'sup class="numerator"',u'⁄',u'sub class="denominator"',], 
      }

  hybridfunctions = {
      u'\\sqrt':[u'sqrt',u'span class="sqrt"',u'sup',], 
      u'\\unit':[u'font',u'span class="unit"',u'',], 
      }

  labelfunctions = {
      u'\\label':u'a class="eqnumber" name="#"', 
      }

  limits = {
      u'commands':[u'\\sum',u'\\int',u'\\intop',], u'operands':[u'^',u'_',], 
      }

  literalfunctions = {
      u'\\mbox':u'span class="mbox"', u'\\text':u'span class="text"', 
      u'\\textipa':u'span class="textipa"', 
      }

  modified = {
      u'\n':u'', u' ':u'', u'&':u'	', u'\'':u'’', u'+':u' + ', u',':u', ', 
      u'-':u' − ', u'/':u' ⁄ ', u'<':u' &lt; ', u'=':u' = ', u'>':u' &gt; ', 
      }

  onefunctions = {
      u'\\bar':u'span class="bar"', u'\\begin{array}':u'span class="arraydef"', 
      u'\\bigl':u'span class="bigsymbol"', u'\\bigr':u'span class="bigsymbol"', 
      u'\\hphantom':u'span class="phantom"', u'\\left':u'span class="symbol"', 
      u'\\overline':u'span class="overline"', 
      u'\\phantom':u'span class="phantom"', u'\\right':u'span class="symbol"', 
      u'\\underline':u'u', u'\\vphantom':u'span class="phantom"', 
      }

  starts = {
      u'beginafter':u'}', u'beginbefore':u'\\begin{', u'bracket':u'{', 
      u'command':u'\\', u'complex':u'\\[', u'simple':u'$', 
      u'squarebracket':u'[', 
      }

  symbolfunctions = {
      u'^':u'sup', u'_':u'sub', 
      }

  unmodified = {
      
      u'characters':[u'.',u'*',u'€',u'(',u')',u'[',u']',u':',u'·',u'!',u';',u'|',], 
      }

class GeneralConfig(object):
  "Configuration class from config file"

  version = {
      u'date':u'2009-09-18', u'number':u'0.31', 
      }

class NumberingConfig(object):
  "Configuration class from config file"

  layouts = {
      
      u'ordered':[u'Chapter',u'Section',u'Subsection',u'Subsubsection',u'Paragraph',], 
      u'unique':[u'Part',u'Book',], 
      }

class StyleConfig(object):
  "Configuration class from config file"

  quotes = {
      u'ald':u'»', u'als':u'›', u'ard':u'«', u'ars':u'‹', u'eld':u'“', 
      u'els':u'‘', u'erd':u'”', u'ers':u'’', u'fld':u'«', u'fls':u'‹', 
      u'frd':u'»', u'frs':u'›', u'gld':u'„', u'gls':u'‚', u'grd':u'“', 
      u'grs':u'‘', u'pld':u'„', u'pls':u'‚', u'prd':u'”', u'prs':u'’', 
      u'sld':u'”', u'srd':u'”', 
      }

  spaces = {
      u'\\enskip{}':u' ', u'\\hfill{}':u' ', u'\\hspace*{\\fill}':u' ', 
      u'\\hspace*{}':u'', u'\\hspace{}':u' ', u'\\negthinspace{}':u'', 
      u'\\qquad{}':u'  ', u'\\quad{}':u' ', u'\\space{}':u'&nbsp;', 
      u'\\thinspace{}':u' ', u'~':u'&nbsp;', 
      }

class TagConfig(object):
  "Configuration class from config file"

  barred = {
      u'under':u'u', 
      }

  boxes = {
      u'Framed':u'div class="framed"', u'Frameless':u'div class="frameless"', 
      }

  family = {
      u'sans':u'span class="sans"', u'typewriter':u'tt', 
      }

  layouts = {
      u'Center':u'div', u'Chapter':u'h1', u'Date':u'h2', u'LyX-Code':u'pre', 
      u'Paragraph':u'div', u'Part':u'h1', u'Quotation':u'blockquote', 
      u'Quote':u'blockquote', u'Section':u'h2', u'Subsection':u'h3', 
      u'Subsubsection':u'h4', 
      }

  listitems = {
      u'Enumerate':u'ol', u'Itemize':u'ul', 
      }

  notes = {
      u'Comment':u'', u'Greyedout':u'span class="greyedout"', u'Note':u'', 
      }

  shaped = {
      u'italic':u'i', u'slanted':u'i', u'smallcaps':u'span class="versalitas"', 
      }

class TranslationConfig(object):
  "Configuration class from config file"

  constants = {
      u'abstract':u'Abstract', u'bibliography':u'Bibliography', 
      u'index':u'Index', u'nomenclature':u'Nomenclature', 
      u'toc':u'Table of Contents', 
      }

  floats = {
      u'algorithm':u'Listing ', u'figure':u'Figure ', u'listing':u'Listing ', 
      u'table':u'Table ', 
      }

  lists = {
      u'algorithm':u'List of Listings', u'figure':u'List of Figures', 
      u'table':u'List of Tables', 
      }



class CommandLineParser(object):
  "A parser for runtime options"

  def __init__(self, options):
    self.options = options

  def parseoptions(self, args):
    "Parse command line options"
    if len(args) == 0:
      return None
    while len(args) > 0 and args[0].startswith('--'):
      key, value = self.readoption(args)
      if not key:
        return 'Option ' + value + ' not recognized'
      if not value:
        return 'Option ' + key + ' needs a value'
      setattr(self.options, key, value)
    return None

  def readoption(self, args):
    "Read the key and value for an option"
    arg = args[0][2:]
    del args[0]
    if '=' in arg:
      return self.readequals(arg, args)
    key = arg
    if not hasattr(self.options, key):
      return None, key
    current = getattr(self.options, key)
    if current.__class__ == bool:
      return key, True
    # read value
    if len(args) == 0:
      return key, None
    if args[0].startswith('"'):
      initial = args[0]
      del args[0]
      return key, self.readquoted(args, initial)
    value = args[0]
    del args[0]
    return key, value

  def readquoted(self, args, initial):
    "Read a value between quotes"
    value = initial[1:]
    while len(args) > 0 and not args[0].endswith('"') and not args[0].startswith('--'):
      value += ' ' + args[0]
      del args[0]
    if len(args) == 0 or args[0].startswith('--'):
      return None
    value += ' ' + args[0:-1]
    return value

  def readequals(self, arg, args):
    "Read a value with equals"
    split = arg.split('=', 1)
    key = split[0]
    value = split[1]
    if not value.startswith('"'):
      return key, value
    return key, self.readquoted(args, value)



class Options(object):
  "A set of runtime options"

  instance = None

  nocopy = False
  debug = False
  quiet = False
  version = False
  hardversion = False
  versiondate = False
  html = False
  help = False
  showlines = True
  unicode = False
  css = 'http://www.nongnu.org/elyxer/lyx.css'
  title = None
  directory = None
  destdirectory = None
  toc = False
  forceformat = None
  branches = dict()

  def parseoptions(self, args):
    "Parse command line options"
    parser = CommandLineParser(Options)
    result = parser.parseoptions(args)
    if result:
      Trace.error(result)
      self.usage()
    if Options.help:
      self.usage()
    if Options.version:
      self.showversion()
    if Options.hardversion:
      self.showhardversion()
    if Options.versiondate:
      self.showversiondate()
    # set in Trace if necessary
    for param in dir(Options):
      if hasattr(Trace, param + 'mode'):
        setattr(Trace, param + 'mode', getattr(self, param))

  def usage(self):
    "Show correct usage"
    Trace.error('Usage: elyxer.py [filein] [fileout].')
    Trace.error('  Options:')
    Trace.error('    --nocopy: disables the copyright notice at the bottom')
    Trace.error('    --quiet: disables all runtime messages')
    Trace.error('    --debug: enable debugging messages (for developers)')
    Trace.error('    --title "title": set the generated page title')
    Trace.error('    --directory "images_dir": look for images in the specified directory')
    Trace.error('    --destdirectory "dest_dir": put converted images into this directory')
    Trace.error('    --css "file.css": use a custom CSS file')
    Trace.error('    --version: show version number and release date')
    Trace.error('    --html: output HTML 4.0 instead of the default XHTML')
    Trace.error('    --unicode: full Unicode output')
    Trace.error('    --forceformat ".extension": force image output format')
    exit()

  def showversion(self):
    "Return the current eLyXer version string"
    string = 'eLyXer version ' + GeneralConfig.version['number']
    string += ' (' + GeneralConfig.version['date'] + ')'
    Trace.error(string)
    exit()

  def showhardversion(self):
    "Return just the version string"
    Trace.message(GeneralConfig.version['number'])
    exit()

  def showversiondate(self):
    "Return just the version dte"
    Trace.message(GeneralConfig.version['date'])
    exit()

class BranchOptions(object):
  "A set of options for a branch"

  def __init__(self, name):
    self.name = name
    self.options = {'color':'#ffffff'}

  def set(self, key, value):
    "Set a branch option"
    if not key.startswith(ContainerConfig.string['startcommand']):
      Trace.error('Invalid branch option ' + key)
      return
    key = key.replace(ContainerConfig.string['startcommand'], '')
    self.options[key] = value

  def isselected(self):
    "Return if the branch is selected"
    if not 'selected' in self.options:
      return False
    return self.options['selected'] == '1'

  def __unicode__(self):
    "String representation"
    return 'options for ' + self.name + ': ' + unicode(self.options)










import codecs


class Parser(object):
  "A generic parser"

  def __init__(self):
    self.begin = 0
    self.parameters = dict()

  def parseheader(self, reader):
    "Parse the header"
    header = reader.currentline().split()
    reader.nextline()
    self.begin = reader.linenumber
    return header

  def parseparameter(self, reader):
    "Parse a parameter"
    if reader.currentline().strip().startswith('<'):
      key, value = self.parsexml(reader)
      self.parameters[key] = value
      return
    split = reader.currentline().strip().split(' ', 1)
    reader.nextline()
    if len(split) == 0:
      return
    key = split[0]
    if len(split) == 1:
      self.parameters[key] = True
      return
    if not '"' in split[1]:
      self.parameters[key] = split[1].strip()
      return
    doublesplit = split[1].split('"')
    self.parameters[key] = doublesplit[1]

  def parsexml(self, reader):
    "Parse a parameter in xml form: <param attr1=value...>"
    strip = reader.currentline().strip()
    reader.nextline()
    if not strip.endswith('>'):
      Trace.error('XML parameter ' + strip + ' should be <...>')
    split = strip[1:-1].split()
    if len(split) == 0:
      Trace.error('Empty XML parameter <>')
      return None, None
    key = split[0]
    del split[0]
    if len(split) == 0:
      return key, dict()
    attrs = dict()
    for attr in split:
      if not '=' in attr:
        Trace.error('Erroneous attribute ' + attr)
        attr += '="0"'
      parts = attr.split('=')
      attrkey = parts[0]
      value = parts[1].split('"')[1]
      attrs[attrkey] = value
    return key, attrs

  def parseending(self, reader, process):
    "Parse until the current ending is found"
    while not reader.currentline().startswith(self.ending):
      process()

  def __unicode__(self):
    "Return a description"
    return self.__class__.__name__ + ' (' + unicode(self.begin) + ')'

class LoneCommand(Parser):
  "A parser for just one command line"

  def parse(self,reader):
    "Read nothing"
    return []

class TextParser(Parser):
  "A parser for a command and a bit of text"

  stack = []

  def __init__(self, ending):
    Parser.__init__(self)
    self.ending = ending
    self.endings = []

  def parse(self, reader):
    "Parse lines as long as they are text"
    TextParser.stack.append(self.ending)
    self.endings = TextParser.stack + [ContainerConfig.endings['Layout'],
        ContainerConfig.endings['Inset'], self.ending]
    contents = []
    while not self.isending(reader):
      containers = self.factory.createsome(reader)
      contents += containers
    return contents

  def isending(self, reader):
    "Check if text is ending"
    current = reader.currentline().split()
    if len(current) == 0:
      return False
    if current[0] in self.endings:
      if current[0] in TextParser.stack:
        TextParser.stack.remove(current[0])
      else:
        TextParser.stack = []
      return True
    return False

class ExcludingParser(Parser):
  "A parser that excludes the final line"

  def parse(self, reader):
    "Parse everything up to (and excluding) the final line"
    contents = []
    self.parseending(reader, lambda: self.parsecontainers(reader, contents))
    return contents

  def parsecontainers(self, reader, contents):
    containers = self.factory.createsome(reader)
    contents += containers

class BoundedParser(ExcludingParser):
  "A parser bound by a final line"

  def parse(self, reader):
    "Parse everything, including the final line"
    contents = ExcludingParser.parse(self, reader)
    # skip last line
    reader.nextline()
    return contents

class BoundedDummy(Parser):
  "A bound parser that ignores everything"

  def parse(self, reader):
    "Parse the contents of the container"
    self.parseending(reader, lambda: reader.nextline())
    # skip last line
    reader.nextline()
    return []

class StringParser(Parser):
  "Parses just a string"

  def parseheader(self, reader):
    "Do nothing, just take note"
    self.begin = reader.linenumber + 1
    return []

  def parse(self, reader):
    "Parse a single line"
    contents = [reader.currentline()]
    reader.nextline()
    return contents

class InsetParser(BoundedParser):
  "Parses a LyX inset"

  def parse(self, reader):
    "Parse inset parameters into a dictionary"
    startcommand = ContainerConfig.string['startcommand']
    while reader.currentline() != '' and not reader.currentline().startswith(startcommand):
      self.parseparameter(reader)
    return BoundedParser.parse(self, reader)

class HeaderParser(Parser):
  "Parses the LyX header"

  def parse(self, reader):
    "Parse header parameters into a dictionary"
    self.parseending(reader, lambda: self.parseline(reader))
    # skip last line
    reader.nextline()
    return []

  def parseline(self, reader):
    "Parse a single line as a parameter or as a start"
    line = reader.currentline()
    if line.startswith(ContainerConfig.header['branch']):
      self.parsebranch(reader)
      return
    # no match
    self.parseparameter(reader)

  def parsebranch(self, reader):
    branch = reader.currentline().split()[1]
    reader.nextline()
    subparser = HeaderParser().complete(ContainerConfig.header['endbranch'])
    subparser.parse(reader)
    options = BranchOptions(branch)
    for key in subparser.parameters:
      options.set(key, subparser.parameters[key])
    Options.branches[branch] = options

  def complete(self, ending):
    self.ending = ending
    return self




import codecs
import datetime


class EmptyOutput(object):
  "The output for some container"

  def gethtml(self, container):
    "Return empty HTML code"
    return []

class FixedOutput(object):
  "Fixed output"

  def gethtml(self, container):
    "Return constant HTML code"
    return container.html

class ContentsOutput(object):
  "Outputs the contents converted to HTML"

  def gethtml(self, container):
    "Return the HTML code"
    html = []
    if container.contents == None:
      return html
    for element in container.contents:
      if not hasattr(element, 'gethtml'):
        Trace.error('No html in ' + element.__class__.__name__ + ': ' + unicode(element))
        return html
      html += element.gethtml()
    return html

class TaggedOutput(ContentsOutput):
  "Outputs an HTML tag surrounding the contents"

  def __init__(self):
    self.breaklines = False

  def settag(self, tag, breaklines=False):
    "Set the value for the tag"
    self.tag = tag
    self.breaklines = breaklines
    return self

  def setbreaklines(self, breaklines):
    "Set the value for breaklines"
    self.breaklines = breaklines
    return self

  def gethtml(self, container):
    "Return the HTML code"
    html = [self.getopen(container)]
    html += ContentsOutput.gethtml(self, container)
    html.append(self.getclose(container))
    return html

  def getopen(self, container):
    "Get opening line"
    if self.tag == '':
      return ''
    open = '<' + self.tag + '>'
    if self.breaklines:
      return open + '\n'
    return open

  def getclose(self, container):
    "Get closing line"
    if self.tag == '':
      return ''
    close = '</' + self.tag.split()[0] + '>'
    if self.breaklines:
      return '\n' + close + '\n'
    return close

class MirrorOutput(object):
  "Returns as output whatever comes along"

  def gethtml(self, container):
    "Return what is put in"
    return container.contents

class HeaderOutput(object):
  "Returns the HTML headers"

  def gethtml(self, container):
    "Return a constant header"
    if not Options.html:
      html = [u'<?xml version="1.0" encoding="UTF-8"?>\n']
      html.append(u'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n')
      html.append(u'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n')
    else:
      html = [u'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">\n']
      html.append(u'<html lang="en">\n')
    html.append(u'<head>\n')
    html.append(u'<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
    html.append(u'<meta name="generator" content="http://www.nongnu.org/elyxer/"/>\n')
    html.append(u'<meta name="create-date" content="' + datetime.date.today().isoformat() + '"/>\n')
    html.append(u'<link rel="stylesheet" href="' + Options.css + '" type="text/css" media="screen"/>\n')
    html += TitleOutput().gethtml(container)
    html.append('</head>\n')
    html.append('<body>\n')
    html.append('<div id="globalWrapper">\n')
    return html

class TitleOutput(object):
  "Return the HTML title tag"

  pdftitle = None

  def gethtml(self, container):
    "Return the title tag"
    return ['<title>' + self.gettitle() + '</title>\n']

  def gettitle(self):
    "Return the correct title from the option or the PDF title"
    if Options.title:
      return Options.title
    if TitleOutput.pdftitle:
      return TitleOutput.pdftitle
    return 'Converted document'

class FooterOutput(object):
  "Return the HTML code for the footer"

  author = None

  def gethtml(self, container):
    "Footer HTML"
    html = []
    if FooterOutput.author and not Options.nocopy:
      html.append('<hr/>\n')
      year = datetime.date.today().year
      html.append('<p>Copyright (C) ' + unicode(year) + ' ' + FooterOutput.author
          + '</p>\n')
    html.append('</div>\n')
    html.append('</body>\n')
    html.append('</html>\n')
    return html



class Container(object):
  "A container for text and objects in a lyx file"

  def __init__(self):
    self.contents = list()

  def process(self):
    "Process contents"
    pass

  def gethtml(self):
    "Get the resulting HTML"
    html = self.output.gethtml(self)
    if isinstance(html, basestring):
      Trace.error('Raw string ' + html)
      html = [html]
    if Options.html:
      self.escapeall(html, EscapeConfig.html)
    if not Options.unicode:
      self.escapeall(html, EscapeConfig.nonunicode)
    return html

  def escapeall(self, lines, replacements):
    "Escape all lines in an array with the replacements"
    for index, line in enumerate(lines):
      lines[index] = self.escape(line, replacements)

  def escape(self, line, replacements = EscapeConfig.entities):
    "Escape a line with replacements from a map"
    pieces = replacements.keys()
    # do them in order
    pieces.sort()
    for piece in pieces:
      if piece in line:
        line = line.replace(piece, replacements[piece])
    return line

  def searchall(self, type):
    "Search for all embedded containers of a given type"
    list = []
    self.searchprocess(type,
        lambda contents, index: list.append(contents[index]))
    return list

  def searchremove(self, type):
    "Search for all containers of a type and remove them"
    list = []
    self.searchprocess(type,
        lambda contents, index: self.appendremove(list, contents, index))
    return list

  def appendremove(self, list, contents, index):
    "Append to a list and remove from contents"
    list.append(contents[index])
    del contents[index]

  def searchprocess(self, type, process):
    "Search for all embedded containers and process them"
    for index, element in enumerate(self.contents):
      if isinstance(element, Container):
        element.searchprocess(type, process)
      if isinstance(element, type):
        process(self.contents, index)

  def extracttext(self):
    "Search for all the strings and extract the text they contain"
    text = ''
    strings = self.searchall(StringContainer)
    for string in strings:
      text += string.contents[0]
    return text

  def restyle(self, type, restyler):
    "Restyle contents with a restyler function"
    for index, element in enumerate(self.contents):
      if isinstance(element, type):
        restyler(self, index)
      if isinstance(element, Container):
        element.restyle(type, restyler)

  def group(self, index, group, isingroup):
    "Group some adjoining elements into a group"
    if index >= len(self.contents):
      return
    if hasattr(self.contents[index], 'grouped'):
      return
    while index < len(self.contents) and isingroup(self.contents[index]):
      self.contents[index].grouped = True
      group.contents.append(self.contents[index])
      self.contents.pop(index)
    self.contents.insert(index, group)

  def remove(self, index):
    "Remove a container but leave its contents"
    container = self.contents[index]
    self.contents.pop(index)
    while len(container.contents) > 0:
      self.contents.insert(index, container.contents.pop())

  def debug(self, level = 0):
    "Show the contents in debug mode"
    if not Trace.debugmode:
      return
    Trace.debug('  ' * level + unicode(self))
    for element in self.contents:
      if isinstance(element, Container):
        element.debug(level + 1)

  def __unicode__(self):
    "Get a description"
    if not hasattr(self, 'begin'):
      return self.__class__.__name__
    return self.__class__.__name__ + '@' + unicode(self.begin)

class BlackBox(Container):
  "A container that does not output anything"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()
    self.contents = []

class LyXFormat(BlackBox):
  "Read the lyxformat command"

  def process(self):
    "Show warning if version < 276"
    version = int(self.header[1])
    if version < 276:
      Trace.error('Warning: unsupported format version ' + str(version))

class StringContainer(Container):
  "A container for a single string"

  def __init__(self):
    self.parser = StringParser()
    self.output = MirrorOutput()

  def process(self):
    "Replace special chars"
    line = self.contents[0]
    replaced = self.escape(line, EscapeConfig.entities)
    replaced = self.changeline(replaced)
    self.contents = [replaced]
    if ContainerConfig.string['startcommand'] in replaced and len(replaced) > 1:
      # unprocessed commands
      Trace.error('Unknown command at ' + unicode(self.parser.begin) + ': '
          + replaced.strip())

  def changeline(self, line):
    line = self.escape(line, EscapeConfig.chars)
    if not ContainerConfig.string['startcommand'] in line:
      return line
    line = self.escape(line, EscapeConfig.commands)
    return line
  
  def __unicode__(self):
    length = ''
    descr = ''
    if len(self.contents) > 0:
      length = unicode(len(self.contents[0]))
      descr = self.contents[0].strip()
    return 'StringContainer@' + unicode(self.begin) + '(' + unicode(length) + ')'

class Constant(StringContainer):
  "A constant string"

  def __init__(self, text):
    self.contents = [text]
    self.output = MirrorOutput()

  def __unicode__(self):
    return 'Constant: ' + self.contents[0]

class TaggedText(Container):
  "Text inside a tag"

  def __init__(self):
    ending = None
    if self.__class__.__name__ in ContainerConfig.endings:
      ending = ContainerConfig.endings[self.__class__.__name__]
    self.parser = TextParser(ending)
    self.output = TaggedOutput()

  def complete(self, contents, tag, breaklines=False):
    "Complete the tagged text and return it"
    self.contents = contents
    self.output.tag = tag
    self.output.breaklines = breaklines
    return self

  def constant(self, text, tag, breaklines=False):
    "Complete the tagged text with a constant"
    constant = Constant(text)
    return self.complete([constant], tag, breaklines)

  def __unicode__(self):
    return 'Tagged <' + self.output.tag + '>'









class NumberGenerator(object):
  "A number generator for unique sequences and hierarchical structures"

  letters = '-ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  instance = None

  def __init__(self):
    self.startinglevel = 0
    self.number = []
    self.uniques = dict()
    self.chaptered = dict()

  def generateunique(self, type):
    "Generate a number to place in the title but not to append to others"
    if not type in self.uniques:
      self.uniques[type] = 0
    self.uniques[type] = self.increase(self.uniques[type])
    return type + ' ' + unicode(self.uniques[type]) + '.'

  def generate(self, level):
    "Generate a number in the given level"
    if self.number == [] and level == 1:
      self.startinglevel = 1
    level -= self.startinglevel
    if len(self.number) > level:
      self.number = self.number[:level + 1]
    else:
      while len(self.number) <= level:
        self.number.append(0)
    self.number[level] = self.increase(self.number[level])
    return self.dotseparated(self.number)

  def generatechaptered(self, type):
    "Generate a number which goes with first-level numbers"
    if len(self.number) == 0:
      chapter = 0
    else:
      chapter = self.number[0]
    if not type in self.chaptered or self.chaptered[type][0] != chapter:
      self.chaptered[type] = [chapter, 0]
    chaptered = self.chaptered[type]
    chaptered[1] = self.increase(chaptered[1])
    self.chaptered[type] = chaptered
    return self.dotseparated(chaptered)

  def increase(self, number):
    "Increase the number (or letter)"
    if not isinstance(number, str):
      return number + 1
    if not number in NumberGenerator.letters:
      Trace.error('Unknown letter numeration ' + number)
      return 0
    index = NumberGenerator.letters.index(number) + 1
    return NumberGenerator.letters[index % len(NumberGenerator.letters)]

  def dotseparated(self, number):
    "Get the number separated by dots: 1.1.3"
    dotsep = ''
    if len(number) == 0:
      Trace.error('Empty number')
      return '.'
    for piece in number:
      dotsep += '.' + unicode(piece)
    return dotsep[1:]

NumberGenerator.instance = NumberGenerator()



class LyxHeader(Container):
  "Reads the header, outputs the HTML header"

  def __init__(self):
    self.parser = HeaderParser()
    self.output = HeaderOutput()

  def process(self):
    "Find pdf title"
    key = ContainerConfig.header['pdftitle']
    if key in self.parameters:
      TitleOutput.pdftitle = self.parameters[key]

class LyxFooter(Container):
  "Reads the footer, outputs the HTML footer"

  def __init__(self):
    self.parser = BoundedDummy()
    self.output = FooterOutput()

class Align(Container):
  "Bit of aligned text"

  def __init__(self):
    self.parser = ExcludingParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.output.tag = 'div class="' + self.header[1] + '"'

class Newline(Container):
  "A newline"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.html = ['<br/>\n']

class NewPage(Newline):
  "A new page"

  def process(self):
    "Process contents"
    self.html = ['<p><br/>\n</p>\n']

class Appendix(Container):
  "An appendix to the main document"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class ListItem(Container):
  "An element in a list"

  def __init__(self):
    "Output should be empty until the postprocessor can group items"
    self.contents = list()
    self.parser = BoundedParser()
    self.output = EmptyOutput()

  def process(self):
    "Set the correct type and contents."
    self.type = self.header[1]
    tag = TaggedText().complete(self.contents, 'li', True)
    self.contents = [tag]

  def __unicode__(self):
    return self.type + ' item @ ' + unicode(self.begin)

class DeeperList(Container):
  "A nested list"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

  def process(self):
    "Create the deeper list"
    if len(self.contents) == 0:
      Trace.error('Empty deeper list')
      return

  def __unicode__(self):
    result = 'deeper list @ ' + unicode(self.begin) + ': ['
    for element in self.contents:
      result += unicode(element) + ', '
    return result[:-2] + ']'

class ERT(Container):
  "Evil Red Text"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()









class QuoteContainer(Container):
  "A container for a pretty quote"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = FixedOutput()

  def process(self):
    "Process contents"
    self.type = self.header[2]
    if not self.type in StyleConfig.quotes:
      Trace.error('Quote type ' + self.type + ' not found')
      self.html = ['"']
      return
    self.html = [StyleConfig.quotes[self.type]]

class LyxLine(Container):
  "A Lyx line"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = FixedOutput()

  def process(self):
    self.html = ['<hr class="line" />']

class EmphaticText(TaggedText):
  "Text with emphatic mode"

  def process(self):
    self.output.tag = 'i'

class ShapedText(TaggedText):
  "Text shaped (italic, slanted)"

  def process(self):
    self.type = self.header[1]
    if not self.type in TagConfig.shaped:
      Trace.error('Unrecognized shape ' + self.header[1])
      self.output.tag = 'span'
      return
    self.output.tag = TagConfig.shaped[self.type]

class VersalitasText(TaggedText):
  "Text in versalitas"

  def process(self):
    self.output.tag = 'span class="versalitas"'

class ColorText(TaggedText):
  "Colored text"

  def process(self):
    self.color = self.header[1]
    self.output.tag = 'span class="' + self.color + '"'

class SizeText(TaggedText):
  "Sized text"

  def process(self):
    self.size = self.header[1]
    self.output.tag = 'span class="' + self.size + '"'

class BoldText(TaggedText):
  "Bold text"

  def process(self):
    self.output.tag = 'b'

class TextFamily(TaggedText):
  "A bit of text from a different family"

  def process(self):
    "Parse the type of family"
    self.type = self.header[1]
    if not self.type in TagConfig.family:
      Trace.error('Unrecognized family ' + type)
      self.output.tag = 'span'
      return
    self.output.tag = TagConfig.family[self.type]

class Hfill(TaggedText):
  "Horizontall fill"

  def process(self):
    self.output.tag = 'span class="right"'

class BarredText(TaggedText):
  "Text with a bar somewhere"

  def process(self):
    "Parse the type of bar"
    self.type = self.header[1]
    if not self.type in TagConfig.barred:
      Trace.error('Unknown bar type ' + self.type)
      self.output.tag = 'span'
      return
    self.output.tag = TagConfig.barred[self.type]

class LangLine(Container):
  "A line with language information"

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

  def process(self):
    self.lang = self.header[1]

class Space(Container):
  "A space of several types"

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()
  
  def process(self):
    self.type = self.header[2]
    if self.type not in StyleConfig.spaces:
      Trace.error('Unknown space type ' + self.type)
      self.html = [' ']
      return
    self.html = [StyleConfig.spaces[self.type]]







class Link(Container):
  "A link to another part of the document"

  def __init__(self):
    self.contents = list()
    self.output = LinkOutput()

  def complete(self, text, anchor, url, type = None):
    self.contents = [Constant(text)]
    if anchor:
      self.anchor = anchor
    if url:
      self.url = url
    if type:
      self.type = type
    return self

class ListOf(Container):
  "A list of entities (figures, tables, algorithms)"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('div class="list"', True)

  def process(self):
    "Parse the header and get the type"
    self.type = self.header[2]
    self.contents = [Constant(TranslationConfig.lists[self.type])]

class TableOfContents(Container):
  "Table of contents"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('div class="toc"', True)

  def process(self):
    "Parse the header and get the type"
    self.contents = [Constant(TranslationConfig.constants['toc'])]

class IndexEntry(Link):
  "An entry in the alphabetical index"

  entries = dict()

  namescapes = {'!':'', '|':', ', '  ':' '}
  keyescapes = {' ':'-', '--':'-', ',':''}

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Put entry in index"
    if 'name' in self.parameters:
      name = self.parameters['name'].strip()
    else:
      name = self.extracttext()
    self.name = self.escape(name, IndexEntry.namescapes)
    self.key = self.escape(self.name, IndexEntry.keyescapes)
    if not self.key in IndexEntry.entries:
      # no entry; create
      IndexEntry.entries[self.key] = list()
    self.index = len(IndexEntry.entries[self.key])
    IndexEntry.entries[self.key].append(self)
    self.anchor = 'entry-' + self.key + '-' + unicode(self.index)
    self.url = '#index-' + self.key
    self.contents = [Constant(u'↓')]

class PrintIndex(Container):
  "Command to print an index"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

  def process(self):
    "Create the alphabetic index"
    index = TranslationConfig.constants['index']
    self.contents = [TaggedText().constant(index, 'h1 class="index"'),
        Constant('\n')]
    for key in self.sortentries():
      name = IndexEntry.entries[key][0].name
      entry = [Link().complete(name, 'index-' + key, None, 'printindex'),
          Constant(': ')]
      contents = [TaggedText().complete(entry, 'i')]
      contents += self.createarrows(key, IndexEntry.entries[key])
      self.contents.append(TaggedText().complete(contents, 'p class="printindex"',
          True))

  def sortentries(self):
    "Sort all entries in the index"
    keys = IndexEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

  def createarrows(self, key, entries):
    "Create an entry in the index"
    arrows = []
    for entry in entries:
      link = Link().complete(u'↑', 'index-' + entry.key,
          '#entry-' + entry.key + '-' + unicode(entry.index))
      arrows += [link, Constant(u', \n')]
    return arrows[:-1]

class NomenclatureEntry(Link):
  "An entry of LyX nomenclature"

  entries = {}

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Put entry in index"
    self.symbol = self.parser.parameters['symbol']
    self.description = self.parser.parameters['description']
    self.key = self.symbol.replace(' ', '-').lower()
    NomenclatureEntry.entries[self.key] = self
    self.anchor = 'noment-' + self.key
    self.url = '#nom-' + self.key
    self.contents = [Constant(u'↓')]

class NomenclaturePrint(Container):
  "Print all nomenclature entries"

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    self.keys = self.sortentries()
    nomenclature = TranslationConfig.constants['nomenclature']
    self.contents = [TaggedText().constant(nomenclature, 'h1 class="nomenclature"')]
    for key in self.keys:
      entry = NomenclatureEntry.entries[key]
      contents = [Link().complete(u'↑', 'nom-' + key, '#noment-' + key)]
      contents.append(Constant(entry.symbol + u' '))
      contents.append(Constant(entry.description))
      text = TaggedText().complete(contents, 'div class="Nomenclated"', True)
      self.contents.append(text)

  def sortentries(self):
    "Sort all entries in the index"
    keys = NomenclatureEntry.entries.keys()
    # sort by name
    keys.sort()
    return keys

class URL(Link):
  "A clickable URL"

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    "Read URL from parameters"
    name = self.escape(self.parser.parameters['target'])
    if 'type' in self.parser.parameters:
      self.url = self.escape(self.parser.parameters['type']) + name
    else:
      self.url = name
    if 'name' in self.parser.parameters:
      name = self.parser.parameters['name']
    self.contents = [Constant(name)]

class FlexURL(URL):
  "A flexible URL"

  def process(self):
    "Read URL from contents"
    self.url = self.extracttext()

class LinkOutput(object):
  "A link pointing to some destination"
  "Or an anchor (destination)"

  def gethtml(self, container):
    "Get the HTML code for the link"
    type = container.__class__.__name__
    if hasattr(container, 'type'):
      type = container.type
    tag = 'a class="' + type + '"'
    if hasattr(container, 'anchor'):
      tag += ' name="' + container.anchor + '"'
    if hasattr(container, 'url'):
      tag += ' href="' + container.url + '"'
    text = TaggedText().complete(container.contents, tag)
    return text.gethtml()



class Label(Container):
  "A label to be referenced"

  names = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()

  def process(self):
    self.anchor = self.parser.parameters['name']
    Label.names[self.anchor] = self
    self.contents = [Constant(' ')]

class Reference(Link):
  "A reference to a label"

  def __init__(self):
    self.parser = InsetParser()
    self.output = LinkOutput()
    self.direction = u'↓'

  def process(self):
    key = self.parser.parameters['reference']
    self.url = '#' + key
    if key in Label.names:
      # already seen
      self.direction = u'↑'
    self.contents = [Constant(self.direction)]






class Layout(Container):
  "A layout (block of text) inside a lyx file"

  def __init__(self):
    self.contents = list()
    self.parser = BoundedParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    if self.type in TagConfig.layouts:
      self.output.tag = TagConfig.layouts[self.type] + ' class="' + self.type + '"'
    elif self.type.replace('*', '') in TagConfig.layouts:
      self.output.tag = TagConfig.layouts[self.type.replace('*', '')] + ' class="' +  self.type.replace('*', '-') + '"'
    else:
      self.output.tag = 'div class="' + self.type + '"'

  def __unicode__(self):
    return 'Layout of type ' + self.type

class StandardLayout(Layout):
  "A standard layout -- can be a true div or nothing at all"

  def process(self):
    self.type = 'standard'
    self.output = ContentsOutput()

class Title(Layout):
  "The title of the whole document"

  def process(self):
    self.type = 'title'
    self.output.tag = 'h1 class="title"'
    self.title = self.extracttext()
    Trace.message('Title: ' + self.title)

class Author(Layout):
  "The document author"

  def process(self):
    self.type = 'author'
    self.output.tag = 'h2 class="author"'
    strings = self.searchall(StringContainer)
    if len(strings) > 0:
      FooterOutput.author = strings[0].contents[0]
      Trace.debug('Author: ' + FooterOutput.author)

class Abstract(Layout):
  "A paper abstract"

  def process(self):
    self.type = 'abstract'
    self.output.tag = 'div class="abstract"'
    message = TranslationConfig.constants['abstract']
    tagged = TaggedText().constant(message, 'p class="abstract-message"', True)
    self.contents.insert(0, tagged)

class FirstWorder(Layout):
  "A layout where the first word is extracted"

  def extractfirstword(self, contents):
    "Extract the first word as a list"
    first, found = self.extractfirsttuple(contents)
    return first

  def extractfirsttuple(self, contents):
    "Extract the first word as a tuple"
    firstcontents = []
    index = 0
    while index < len(contents):
      first, found = self.extractfirstcontainer(contents[index])
      if first:
        firstcontents += first
      if found:
        return firstcontents, True
      else:
        del contents[index]
    return firstcontents, False

  def extractfirstcontainer(self, container):
    "Extract the first word from a string container"
    if len(container.contents) == 0:
      # empty container
      return [container], False
    if isinstance(container, StringContainer):
      return self.extractfirststring(container)
    elif isinstance(container, ERT):
      return [container], False
    if len(container.contents) == 0:
      # empty container
      return None, False
    first, found = self.extractfirsttuple(container.contents)
    if isinstance(container, TaggedText) and hasattr(container, 'tag'):
      newtag = TaggedText().complete(first, container.tag)
      return [newtag], found
    return first, found

  def extractfirststring(self, container):
    "Extract the first word from a string container"
    string = container.contents[0]
    if not ' ' in string:
      return [container], False
    split = string.split(' ', 1)
    container.contents[0] = split[1]
    return [Constant(split[0])], True

class Description(FirstWorder):
  "A description layout"

  def process(self):
    "Set the first word to bold"
    self.type = 'Description'
    self.output.tag = 'div class="Description"'
    firstword = self.extractfirstword(self.contents)
    if not firstword:
      return
    firstword.append(Constant(u' '))
    tag = 'span class="Description-entry"'
    self.contents.insert(0, TaggedText().complete(firstword, tag))

class List(FirstWorder):
  "A list layout"

  def process(self):
    "Set the first word to bold"
    self.type = 'List'
    self.output.tag = 'div class="List"'
    firstword = self.extractfirstword(self.contents)
    if not firstword:
      return
    tag = 'span class="List-entry"'
    self.contents.insert(0, TaggedText().complete(firstword, tag))

class PlainLayout(Layout):
  "A plain layout"

  def process(self):
    "Do nothing"
    self.type = 'Plain'






class InsetText(Container):
  "An inset of text in a lyx file"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()

class Inset(Container):
  "A generic inset in a LyX document"

  def __init__(self):
    self.contents = list()
    self.parser = InsetParser()
    self.output = TaggedOutput().setbreaklines(True)

  def process(self):
    self.type = self.header[1]
    self.output.tag = 'span class="' + self.type + '"'

  def __unicode__(self):
    return 'Inset of type ' + self.type

class NewlineInset(Newline):
  "A newline or line break in an inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = FixedOutput()

class Branch(Container):
  "A branch within a LyX document"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="branch"', True)

  def process(self):
    "Disable inactive branches"
    self.branch = self.header[2]
    if not self.isactive():
      Trace.debug('Branch ' + self.branch + ' not active')
      self.output = EmptyOutput()

  def isactive(self):
    "Check if the branch is active"
    if not self.branch in Options.branches:
      Trace.error('Invalid branch ' + self.branch)
      return True
    branch = Options.branches[self.branch]
    return branch.isselected()

class ShortTitle(Container):
  "A short title to display (always hidden)"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

class Footnote(Container):
  "A footnote to the main text"

  order = 0
  list = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Add a letter for the order, rotating"
    letter = Footnote.list[Footnote.order % len(Footnote.list)]
    span = 'span class="FootMarker"'
    pre = FootnoteConfig.constants['prefrom']
    post = FootnoteConfig.constants['postfrom']
    fromfoot = TaggedText().constant(pre + letter + post, span)
    self.contents.insert(0, fromfoot)
    tag = TaggedText().complete(self.contents, 'span class="Foot"', True)
    pre = FootnoteConfig.constants['preto']
    post = FootnoteConfig.constants['postto']
    tofoot = TaggedText().constant(pre + letter + post, span)
    self.contents = [tofoot, tag]
    Footnote.order += 1

class Note(Container):
  "A LyX note of several types"

  def __init__(self):
    self.parser = InsetParser()
    self.output = EmptyOutput()

  def process(self):
    "Hide note and comment, dim greyed out"
    self.type = self.header[2]
    if TagConfig.notes[self.type] == '':
      return
    self.output = TaggedOutput().settag(TagConfig.notes[self.type], True)

class FlexCode(Container):
  "A bit of inset code"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="code"', True)

class InfoInset(Container):
  "A LyX Info inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="Info"', False)

  def process(self):
    "Set the shortcut as text"
    self.type = self.parser.parameters['type']
    self.contents = [Constant(self.parser.parameters['arg'])]

class BoxInset(Container):
  "A box inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div', True)

  def process(self):
    "Set the correct tag"
    self.type = self.header[2]
    if not self.type in TagConfig.boxes:
      Trace.error('Uknown box type ' + self.type)
      return
    self.output.settag(TagConfig.boxes[self.type], True)




class Group(Container):
  "A silly group of containers"

  def __init__(self):
    self.output = ContentsOutput()

  def contents(self, contents):
    self.contents = contents
    return self

  def __unicode__(self):
    return 'Group: ' + unicode(self.contents)

class PostLayout(object):
  "Numerate an indexed layout"

  processedclass = Layout
  unique = NumberingConfig.layouts['unique']
  ordered = NumberingConfig.layouts['ordered']

  def __init__(self):
    self.generator = NumberGenerator.instance

  def postprocess(self, layout, last):
    "Generate a number and place it before the text"
    if self.containsappendix(layout):
      self.activateappendix()
    if layout.type in PostLayout.unique:
      number = self.generator.generateunique(layout.type)
    elif layout.type in PostLayout.ordered:
      level = PostLayout.ordered.index(layout.type)
      number = self.generator.generate(level)
    else:
      return layout
    layout.number = number
    layout.contents.insert(0, Constant(number + u' '))
    return layout

  def containsappendix(self, layout):
    "Find out if there is an appendix somewhere in the layout"
    for element in layout.contents:
      if isinstance(element, Appendix):
        return True
    return False

  def activateappendix(self):
    "Change first number to letter, and chapter to appendix"
    self.generator.number = ['-']

class PostStandard(object):
  "Convert any standard spans in root to divs"

  processedclass = StandardLayout

  def postprocess(self, standard, last):
    "Switch to div"
    standard.output = TaggedOutput().settag('div class="Standard"', True)
    return standard

class Postprocessor(object):
  "Postprocess a container keeping some context"

  stages = [PostLayout, PostStandard]
  unconditional = []
  contents = []

  def __init__(self):
    self.stages = self.instantiate(Postprocessor.stages)
    self.stagedict = dict([(x.processedclass, x) for x in self.stages])
    self.unconditional = self.instantiate(Postprocessor.unconditional)
    self.contents = self.instantiate(Postprocessor.contents)
    self.contentsdict = dict([(x.processedclass, x) for x in self.contents])
    self.last = None

  def postprocess(self, container):
    "Postprocess the root container and its contents"
    container = self.postprocessroot(container)
    self.postprocesscontents(container.contents)
    return container

  def postprocessroot(self, original):
    "Postprocess an element taking into account the last one"
    element = original
    if element.__class__ in self.stagedict:
      stage = self.stagedict[element.__class__]
      element = stage.postprocess(element, self.last)
    for stage in self.unconditional:
      element = stage.postprocess(element, self.last)
    self.last = original
    return element

  def postprocesscontents(self, contents):
    "Postprocess the container contents"
    last = None
    for index, element in enumerate(contents):
      if isinstance(element, Container):
        self.postprocesscontents(element.contents)
      if element.__class__ in self.contentsdict:
        stage = self.contentsdict[element.__class__]
        contents[index] = stage.postprocess(element, last)
      last = contents[index]

  def instantiate(self, classes):
    "Instantiate an element from each class"
    list = [x.__new__(x) for x in classes]
    for element in list:
      element.__init__()
    return list












class TableParser(BoundedParser):
  "Parse the whole table"

  headers = ContainerConfig.table['headers']

  def __init__(self):
    BoundedParser.__init__(self)
    self.columns = list()

  def parseheader(self, reader):
    "Parse table headers"
    reader.nextline()
    while self.startswithheader(reader):
      self.parseparameter(reader)
    return []

  def startswithheader(self, reader):
    "Check if the current line starts with a header line"
    for start in TableParser.headers:
      if reader.currentline().strip().startswith(start):
        return True
    return False

class TablePartParser(BoundedParser):
  "Parse a table part (row or cell)"

  def parseheader(self, reader):
    "Parse the header"
    tablekey, parameters = self.parsexml(reader)
    self.parameters = parameters
    return list()

class ColumnParser(LoneCommand):
  "Parse column properties"

  def parseheader(self, reader):
    "Parse the column definition"
    key, parameters = self.parsexml(reader)
    self.parameters = parameters
    return []



class Table(Container):
  "A lyx table"

  def __init__(self):
    self.parser = TableParser()
    self.output = TaggedOutput().settag('table', True)
    self.columns = []

  def process(self):
    "Set the columns on every row"
    index = 0
    while index < len(self.contents):
      element = self.contents[index]
      if isinstance(element, Column):
        self.columns.append(element)
        del self.contents[index]
      elif isinstance(element, BlackBox):
        del self.contents[index]
      elif isinstance(element, Row):
        element.setcolumns(self.columns)
        index += 1
      else:
        Trace.error('Unknown element type ' + element.__class__.__name__ +
            ' in table: ' + unicode(element.contents[0]))
        index += 1

class Row(Container):
  "A row in a table"

  def __init__(self):
    self.parser = TablePartParser()
    self.output = TaggedOutput().settag('tr', True)
    self.columns = list()

  def setcolumns(self, columns):
    "Process alignments for every column"
    if len(columns) != len(self.contents):
      Trace.error('Columns: ' + unicode(len(columns)) + ', cells: ' + unicode(len(self.contents)))
      return
    for index, cell in enumerate(self.contents):
      columns[index].set(cell)

class Column(Container):
  "A column definition in a table"

  def __init__(self):
    self.parser = ColumnParser()
    self.output = EmptyOutput()

  def set(self, cell):
    "Set alignments in the corresponding cell"
    alignment = self.parameters['alignment']
    if alignment == 'block':
      alignment = 'justify'
    cell.setattribute('align', alignment)
    valignment = self.parameters['valignment']
    cell.setattribute('valign', valignment)

class Cell(Container):
  "A cell in a table"

  def __init__(self):
    self.parser = TablePartParser()
    self.output = TaggedOutput().settag('td', True)

  def setmulticolumn(self, span):
    "Set the cell as multicolumn"
    self.setattribute('colspan', span)

  def setattribute(self, attribute, value):
    "Set a cell attribute in the tag"
    self.output.tag += ' ' + attribute + '="' + unicode(value) + '"'



class PostTable(object):
  "Postprocess a table"

  processedclass = Table

  def postprocess(self, table, last):
    "Postprocess a table: long table, multicolumn rows"
    self.longtable(table)
    for row in table.contents:
      index = 0
      while index < len(row.contents):
        self.checkmulticolumn(row, index)
        index += 1
    return table

  def longtable(self, table):
    "Postprocess a long table, removing unwanted rows"
    if not 'features' in table.parameters:
      return
    features = table.parameters['features']
    if not 'islongtable' in features:
      return
    if features['islongtable'] != 'true':
      return
    if self.hasrow(table, 'endfirsthead'):
      self.removerows(table, 'endhead')
    if self.hasrow(table, 'endlastfoot'):
      self.removerows(table, 'endfoot')

  def hasrow(self, table, attrname):
    "Find out if the table has a row of first heads"
    for row in table.contents:
      if attrname in row.parameters:
        return True
    return False

  def removerows(self, table, attrname):
    "Remove the head rows, since the table has first head rows."
    for row in table.contents:
      if attrname in row.parameters:
        row.output = EmptyOutput()

  def checkmulticolumn(self, row, index):
    "Process a multicolumn attribute"
    cell = row.contents[index]
    if not 'multicolumn' in cell.parameters:
      return
    mc = cell.parameters['multicolumn']
    if mc != '1':
      Trace.error('Unprocessed multicolumn=' + unicode(multicolumn) + ' cell ' + unicode(cell))
      return
    total = 1
    index += 1
    while self.checkbounds(row, index):
      del row.contents[index]
      total += 1
    cell.setmulticolumn(total)

  def checkbounds(self, row, index):
    "Check if the index is within bounds for the row"
    if index >= len(row.contents):
      return False
    if not 'multicolumn' in row.contents[index].parameters:
      return False
    if row.contents[index].parameters['multicolumn'] != '2':
      return False
    return True

Postprocessor.contents.append(PostTable)







import sys



import sys



import sys



import sys


class Position(object):
  "A position in a text to parse"

  def __init__(self, text):
    self.text = text
    self.pos = 0
    self.endinglist = EndingList()

  def skip(self, string):
    "Skip a string"
    self.pos += len(string)

  def remaining(self):
    "Return the text remaining for parsing"
    return self.text[self.pos:]

  def finished(self):
    "Find out if the current formula has finished"
    if self.isout():
      self.endinglist.checkpending()
      return True
    return self.endinglist.checkin(self)

  def isout(self):
    "Find out if we are out of the formula yet"
    return self.pos >= len(self.text)

  def current(self):
    "Return the current character"
    if self.isout():
      Trace.error('Out of the formula')
      return ''
    return self.text[self.pos]

  def checkfor(self, string):
    "Check for a string at the given position"
    if self.pos + len(string) > len(self.text):
      return False
    return self.text[self.pos : self.pos + len(string)] == string

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

  def skipspace(self):
    "Skip all whitespace at current position"
    return self.glob(lambda current: current.isspace())

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
      Trace.error('Pending endings ' + unicode(self.endings) + ' left open')

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



class FormulaParser(Parser):
  "Parses a formula"

  def parseheader(self, reader):
    "See if the formula is inlined"
    self.begin = reader.linenumber + 1
    if reader.currentline().find(FormulaConfig.starts['simple']) > 0:
      return ['inline']
    else:
      return ['block']
  
  def parse(self, reader):
    "Parse the formula until the end"
    formula = self.parseformula(reader)
    while not reader.currentline().startswith(self.ending):
      stripped = reader.currentline().strip()
      if len(stripped) > 0:
        Trace.error('Unparsed formula line ' + stripped)
      reader.nextline()
    reader.nextline()
    return [formula]

  def parseformula(self, reader):
    "Parse the formula contents"
    simple = FormulaConfig.starts['simple']
    if simple in reader.currentline():
      rest = reader.currentline().split(simple, 1)[1]
      if simple in rest:
        # formula is $...$
        return self.parsesingleliner(reader, simple, simple)
      # formula is multiline $...$
      return self.parsemultiliner(reader, simple, simple)
    if FormulaConfig.starts['complex'] in reader.currentline():
      # formula of the form \[...\]
      return self.parsemultiliner(reader, FormulaConfig.starts['complex'],
          FormulaConfig.endings['complex'])
    beginbefore = FormulaConfig.starts['beginbefore']
    beginafter = FormulaConfig.starts['beginafter']
    if beginbefore in reader.currentline():
      if reader.currentline().strip().endswith(beginafter):
        current = reader.currentline().strip()
        endsplit = current.split(beginbefore)[1].split(beginafter)
        startpiece = beginbefore + endsplit[0] + beginafter
        endbefore = FormulaConfig.endings['endbefore']
        endafter = FormulaConfig.endings['endafter']
        endpiece = endbefore + endsplit[0] + endafter
        return self.parsemultiliner(reader, startpiece, endpiece)
      Trace.error('Missing ' + beginafter + ' in ' + reader.currentline())
      return ''
    begincommand = FormulaConfig.starts['command']
    beginbracket = FormulaConfig.starts['bracket']
    if begincommand in reader.currentline() and beginbracket in reader.currentline():
      endbracket = FormulaConfig.endings['bracket']
      return self.parsemultiliner(reader, beginbracket, endbracket)
    Trace.error('Formula beginning ' + reader.currentline() + ' is unknown')
    return ''

  def parsesingleliner(self, reader, start, ending):
    "Parse a formula in one line"
    line = reader.currentline().strip()
    if not start in line:
      Trace.error('Line ' + line + ' does not contain formula start ' + start)
      return ''
    if not line.endswith(ending):
      Trace.error('Formula ' + line + ' does not end with ' + ending)
      return ''
    index = line.index(start)
    rest = line[index + len(start):-len(ending)]
    reader.nextline()
    return rest

  def parsemultiliner(self, reader, start, ending):
    "Parse a formula in multiple lines"
    formula = ''
    line = reader.currentline()
    if not start in line:
      Trace.error('Line ' + line.strip() + ' does not contain formula start ' + start)
      return ''
    index = line.index(start)
    formula = line[index + len(start):].strip()
    reader.nextline()
    while not reader.currentline().endswith(ending):
      formula += reader.currentline()
      reader.nextline()
    formula += reader.currentline()[:-len(ending)]
    reader.nextline()
    return formula



class Formula(Container):
  "A LaTeX formula"

  def __init__(self):
    self.parser = FormulaParser()
    self.output = TaggedOutput().settag('span class="formula"')

  def process(self):
    "Convert the formula to tags"
    pos = Position(self.contents[0])
    whole = WholeFormula()
    if not whole.detect(pos):
      Trace.error('Unknown formula at: ' + pos.remaining())
      constant = TaggedBit().constant(pos.remaining(), 'span class="unknown"')
      self.contents = [constant]
      return
    whole.parsebit(pos)
    whole.process()
    self.contents = [whole]
    if self.header[0] != 'inline':
      self.output.settag('div class="formula"', True)

class FormulaBit(Container):
  "A bit of a formula"

  def __init__(self):
    # type can be 'alpha', 'number', 'font'
    self.type = None
    self.original = ''
    self.contents = []
    self.output = ContentsOutput()

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

  def add(self, bit):
    "Add any kind of formula bit already processed"
    self.contents.append(bit)
    self.original += bit.original

  def skiporiginal(self, string, pos):
    "Skip a string and add it to the original formula"
    self.original += string
    if not pos.checkfor(string):
      Trace.error('String ' + string + ' not at ' + pos.remaining())
    pos.skip(string)

  def __unicode__(self):
    "Get a string representation"
    return self.__class__.__name__ + ' read in ' + self.original

class TaggedBit(FormulaBit):
  "A tagged string in a formula"

  def constant(self, constant, tag):
    "Set the constant and the tag"
    self.output = TaggedOutput().settag(tag)
    self.add(FormulaConstant(constant))
    return self

  def complete(self, contents, tag):
    "Set the constant and the tag"
    self.contents = contents
    self.output = TaggedOutput().settag(tag)
    return self

class FormulaConstant(FormulaBit):
  "A constant string in a formula"

  def __init__(self, string):
    "Set the constant string"
    FormulaBit.__init__(self)
    self.original = string
    self.output = FixedOutput()
    self.html = [string]

class WholeFormula(FormulaBit):
  "Parse a whole formula"

  def __init__(self):
    FormulaBit.__init__(self)
    self.factory = FormulaFactory()

  def detect(self, pos):
    "Check in the factory"
    return self.factory.detectbit(pos)

  def parsebit(self, pos):
    "Parse with any formula bit"
    while self.factory.detectbit(pos):
      bit = self.factory.parsebit(pos)
      #Trace.debug(bit.original + ' -> ' + unicode(bit.gethtml()))
      self.add(bit)

  def process(self):
    "Process the whole formula"
    for index, bit in enumerate(self.contents):
      bit.process()
      if bit.type == 'alpha':
        # make variable
        self.contents[index] = TaggedBit().complete([bit], 'i')
      elif bit.type == 'font' and index > 0:
        last = self.contents[index - 1]
        if last.type == 'number':
          #separate
          last.contents.append(FormulaConstant(u' '))

class FormulaFactory(object):
  "Construct bits of formula"

  # bits will be appended later
  bits = []

  def detectbit(self, pos):
    "Detect if there is a next bit"
    if pos.finished():
      return False
    for bit in FormulaFactory.bits:
      if bit.detect(pos):
        return True
    return False

  def parsebit(self, pos):
    "Parse just one formula bit."
    for bit in FormulaFactory.bits:
      if bit.detect(pos):
        # get a fresh bit and parse it
        newbit = bit.clone()
        newbit.factory = self
        returnedbit = newbit.parsebit(pos)
        if returnedbit:
          return returnedbit
        return newbit
    Trace.error('Unrecognized formula at ' + pos.remaining())
    constant = FormulaConstant(pos.current())
    pos.skip(pos.current())
    return constant




import sys


class RawText(FormulaBit):
  "A bit of text inside a formula"

  def detect(self, pos):
    "Detect a bit of raw text"
    return pos.current().isalpha()

  def parsebit(self, pos):
    "Parse alphabetic text"
    alpha = pos.globalpha()
    self.add(FormulaConstant(alpha))
    self.type = 'alpha'

class FormulaSymbol(FormulaBit):
  "A symbol inside a formula"

  modified = FormulaConfig.modified
  unmodified = FormulaConfig.unmodified['characters']

  def detect(self, pos):
    "Detect a symbol"
    if pos.current() in FormulaSymbol.unmodified:
      return True
    if pos.current() in FormulaSymbol.modified:
      return True
    return False

  def parsebit(self, pos):
    "Parse the symbol"
    if pos.current() in FormulaSymbol.unmodified:
      self.addsymbol(pos.current(), pos)
      return
    if pos.current() in FormulaSymbol.modified:
      self.addsymbol(FormulaSymbol.modified[pos.current()], pos)
      return
    Trace.error('Symbol ' + pos.current() + ' not found')

  def addsymbol(self, symbol, pos):
    "Add a symbol"
    self.skiporiginal(pos.current(), pos)
    self.contents.append(FormulaConstant(symbol))

class Number(FormulaBit):
  "A string of digits in a formula"

  def detect(self, pos):
    "Detect a digit"
    return pos.current().isdigit()

  def parsebit(self, pos):
    "Parse a bunch of digits"
    digits = pos.glob(lambda current: current.isdigit())
    self.add(FormulaConstant(digits))
    self.type = 'number'

class Bracket(FormulaBit):
  "A {} bracket inside a formula"

  start = FormulaConfig.starts['bracket']
  ending = FormulaConfig.endings['bracket']

  def __init__(self):
    "Create a (possibly literal) new bracket"
    FormulaBit.__init__(self)
    self.inner = None

  def detect(self, pos):
    "Detect the start of a bracket"
    return pos.checkfor(self.start)

  def parsebit(self, pos):
    "Parse the bracket"
    self.parsecomplete(pos, self.innerformula)
    return self

  def parseliteral(self, pos):
    "Parse a literal bracket"
    self.parsecomplete(pos, self.innerliteral)
    return self

  def parsecomplete(self, pos, innerparser):
    "Parse the start and end marks"
    if not pos.checkfor(self.start):
      Trace.error('Bracket should start with ' + self.start + ' at ' + pos.remaining())
      return
    self.skiporiginal(self.start, pos)
    pos.pushending(self.ending)
    innerparser(pos)
    self.original += pos.popending(self.ending)

  def innerformula(self, pos):
    "Parse a whole formula inside the bracket"
    self.inner = WholeFormula()
    if self.inner.detect(pos):
      self.inner.parsebit(pos)
      self.add(self.inner)
      return
    if pos.finished():
      Trace.error('Unexpected end of bracket')
      return
    if pos.current() != self.ending:
      Trace.error('No formula in bracket at ' + pos.remaining())
    return

  def innerliteral(self, pos):
    "Parse a literal inside the bracket, which cannot generate html"
    self.literal = pos.glob(lambda current: current != self.ending)
    self.original += self.literal

  def process(self):
    "Process the bracket"
    if self.inner:
      self.inner.process()

class SquareBracket(Bracket):
  "A [] bracket inside a formula"

  start = FormulaConfig.starts['squarebracket']
  ending = FormulaConfig.endings['squarebracket']

FormulaFactory.bits += [ FormulaSymbol(), RawText(), Number(), Bracket() ]



class FormulaCommand(FormulaBit):
  "A LaTeX command inside a formula"

  commandbits = []

  def detect(self, pos):
    "Find the current command"
    return pos.checkfor(FormulaConfig.starts['command'])

  def parsebit(self, pos):
    "Parse the command"
    command = self.extractcommand(pos)
    for bit in FormulaCommand.commandbits:
      if bit.recognize(command):
        newbit = bit.clone()
        newbit.factory = self.factory
        newbit.setcommand(command)
        newbit.parsebit(pos)
        self.add(newbit)
        return newbit
    Trace.error('Unknown command ' + command)
    self.output = TaggedOutput().settag('span class="unknown"')
    self.add(FormulaConstant(command))

  def extractcommand(self, pos):
    "Extract the command from the current position"
    start = FormulaConfig.starts['command']
    if not pos.checkfor(start):
      Trace.error('Missing command start ' + start)
      return
    pos.skip(start)
    if pos.current().isalpha():
      # alpha command
      return start + pos.globalpha()
    # symbol command
    command = start + pos.current()
    pos.skip(pos.current())
    return command

  def process(self):
    "Process the internals"
    for bit in self.contents:
      bit.process()

class CommandBit(FormulaCommand):
  "A formula bit that includes a command"

  def recognize(self, command):
    "Recognize the command as own"
    return command in self.commandmap

  def setcommand(self, command):
    "Set the command in the bit"
    self.command = command
    self.original += command
    self.translated = self.commandmap[self.command]
 
  def parseparameter(self, pos):
    "Parse a parameter at the current position"
    if not self.factory.detectbit(pos):
      Trace.error('No parameter found at: ' + pos.remaining())
      return
    parameter = self.factory.parsebit(pos)
    self.add(parameter)
    return parameter

class EmptyCommand(CommandBit):
  "An empty command (without parameters)"

  commandmap = FormulaConfig.commands

  def parsebit(self, pos):
    "Parse a command without parameters"
    self.contents = [FormulaConstant(self.translated)]

class AlphaCommand(CommandBit):
  "A command without paramters whose result is alphabetical"

  commandmap = FormulaConfig.alphacommands

  def parsebit(self, pos):
    "Parse the command and set type to alpha"
    EmptyCommand.parsebit(self, pos)
    self.type = 'alpha'

class OneParamFunction(CommandBit):
  "A function of one parameter"

  commandmap = FormulaConfig.onefunctions

  def parsebit(self, pos):
    "Parse a function with one parameter"
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)

class SymbolFunction(CommandBit):
  "Find a function which is represented by a symbol (like _ or ^)"

  commandmap = FormulaConfig.symbolfunctions

  def detect(self, pos):
    "Find the symbol"
    return pos.current() in SymbolFunction.commandmap

  def parsebit(self, pos):
    "Parse the symbol"
    self.setcommand(pos.current())
    pos.skip(self.command)
    self.output = TaggedOutput().settag(self.translated)
    self.parseparameter(pos)

class LiteralFunction(CommandBit):
  "A function where parameters are read literally"

  commandmap = FormulaConfig.literalfunctions

  def parsebit(self, pos):
    "Parse a literal parameter"
    self.output = TaggedOutput().settag(self.translated)
    bracket = Bracket().parseliteral(pos)
    self.add(bracket)
    self.contents.append(FormulaConstant(bracket.literal))

  def process(self):
    "Set the type to font"
    self.type = 'font'

class LabelFunction(LiteralFunction):
  "A function that acts as a label"

  commandmap = FormulaConfig.labelfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class FontFunction(OneParamFunction):
  "A function of one parameter that changes the font"

  commandmap = FormulaConfig.fontfunctions

  def process(self):
    "Do not process the inside"
    self.type = 'font'

class DecoratingFunction(OneParamFunction):
  "A function that decorates some bit of text"

  commandmap = FormulaConfig.decoratingfunctions

  def parsebit(self, pos):
    "Parse a decorating function"
    self.output = TaggedOutput().settag('span class="withsymbol"')
    self.type = 'alpha'
    symbol = self.translated
    tagged = TaggedBit().constant(symbol, 'span class="symbolover"')
    self.contents.append(tagged)
    parameter = self.parseparameter(pos)
    parameter.output = TaggedOutput().settag('span class="undersymbol"')
    # simplify if possible
    if self.original in FormulaConfig.alphacommands:
      self.output = FixedOutput()
      self.html = [FormulaConfig.alphacommands[self.original]]

class HybridFunction(CommandBit):
  "Read a function with two parameters: [] and {}"

  commandmap = FormulaConfig.hybridfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters"
    self.parsesquare(pos)
    parameter = self.parseparameter(pos)
    parameter.type = self.translated[0]
    parameter.output = TaggedOutput().settag(self.translated[1])

  def parsesquare(self, pos):
    "Parse a square bracket"
    bracket = SquareBracket()
    if not bracket.detect(pos):
      return
    bracket.parsebit(pos)
    bracket.output = TaggedOutput().settag(self.translated[2])
    self.add(bracket)

class FractionFunction(CommandBit):
  "A fraction with two parameters"

  commandmap = FormulaConfig.fractionfunctions

  def parsebit(self, pos):
    "Parse a fraction function with two parameters"
    tags = self.translated
    self.output = TaggedOutput().settag(self.translated[0])
    parameter1 = self.parseparameter(pos)
    if not parameter1:
      return
    parameter1.output = TaggedOutput().settag(self.translated[1])
    self.contents.append(FormulaConstant(self.translated[2]))
    parameter2 = self.parseparameter(pos)
    if not parameter2:
      return
    parameter2.output = TaggedOutput().settag(self.translated[3])

FormulaFactory.bits += [FormulaCommand(), SymbolFunction()]
FormulaCommand.commandbits = [
    EmptyCommand(), OneParamFunction(), DecoratingFunction(),
    FractionFunction(), FontFunction(), LabelFunction(), LiteralFunction(),
    HybridFunction(),
    ]



class PostFormula(object):
  "Postprocess a formula"

  processedclass = Formula

  def __init__(self):
    self.generator = NumberGenerator()

  def postprocess(self, formula, last):
    "Postprocess any formulae"
    self.postcontents(formula.contents)
    return formula

  def postcontents(self, contents):
    "Search for sum or integral"
    for index, bit in enumerate(contents):
      self.checklimited(contents, index)
      self.checkroot(contents, index)
      self.checknumber(contents, index)
      if isinstance(bit, FormulaBit):
        self.postcontents(bit.contents)

  def checklimited(self, contents, index):
    "Check for a command with limits"
    bit = contents[index]
    if not isinstance(bit, EmptyCommand):
      return
    if not bit.command in FormulaConfig.limits['commands']:
      return
    limits = self.findlimits(contents, index + 1)
    limits.reverse()
    if len(limits) == 0:
      return
    tagged = TaggedText().complete(limits, 'span class="limits"')
    contents.insert(index + 1, tagged)

  def findlimits(self, contents, index):
    "Find the limits for the command"
    limits = []
    while index < len(contents):
      if not self.checklimits(contents, index):
        return limits
      limits.append(contents[index])
      del contents[index]
    return limits

  def checklimits(self, contents, index):
    "Check for a command making the limits"
    bit = contents[index]
    if not isinstance(bit, SymbolFunction):
      return False
    if not bit.command in FormulaConfig.limits['operands']:
      return False
    bit.output.tag += ' class="bigsymbol"'
    return True

  def checkroot(self, contents, index):
    "Check for a root, insert the radical in front"
    bit = contents[index]
    if not hasattr(bit, 'type'):
      return
    if bit.type != 'sqrt':
      return
    radical = TaggedText().constant(u'√', 'span class="radical"')
    root = TaggedText().complete(bit.contents, 'span class="root"')
    bit.contents = [radical, root]

  def checknumber(self, contents, index):
    "Check for equation numbering"
    label = contents[index]
    if not isinstance(label, LabelFunction):
      return
    if len(label.contents) < 1 or not isinstance(label.contents[0], Bracket):
      Trace.error('Wrong contents for label ' + unicode(label))
      return
    bracket = label.contents[0]
    labelname = bracket.literal
    number = '(' + self.generator.generate(1) + ') '
    Label.names[labelname] = label
    tag = label.output.tag.replace('#', labelname)
    label.output.settag(tag)
    label.contents = [FormulaConstant(number)]
    # place number at the beginning
    del contents[index]
    contents.insert(0, label)

Postprocessor.contents.append(PostFormula)






class PostNestedList(object):
  "Postprocess a nested list"

  processedclass = DeeperList

  def postprocess(self, deeper, last):
    "Run the postprocessor on the nested list"
    postproc = Postprocessor()
    for index, part in enumerate(deeper.contents):
      result = postproc.postprocessroot(part)
      deeper.contents[index] = result
    # one additional item to flush the list
    deeper.contents.append(postproc.postprocessroot(BlackBox()))
    return deeper

class PendingList(object):
  "A pending list"

  def __init__(self):
    self.contents = []
    self.type = None

  def additem(self, item):
    "Add a list item"
    self.contents += item.contents
    self.type = item.type

  def addnested(self, nested):
    "Add a nested list item"
    if self.empty():
      self.insertfake()
    item = self.contents[-1]
    self.contents[-1].contents.append(nested)

  def generatelist(self):
    "Get the resulting list"
    if not self.type:
      return Group().contents(self.contents)
    tag = TagConfig.listitems[self.type]
    return TaggedText().complete(self.contents, tag, True)

  def empty(self):
    return len(self.contents) == 0

  def insertfake(self):
    "Insert a fake item"
    item = TaggedText().constant('', 'li class="nested"', True)
    self.contents = [item]
    self.type = 'Itemize'

  def __unicode__(self):
    result = 'pending ' + unicode(self.type) + ': ['
    for element in self.contents:
      result += unicode(element) + ', '
    if len(self.contents) > 0:
      result = result[:-2]
    return result + ']'

class PostListPending(object):
  "Check if there is a pending list"

  def __init__(self):
    self.pending = PendingList()

  def postprocess(self, element, last):
    "If a list element do not return anything;"
    "otherwise return the whole pending list"
    list = None
    if self.generatepending(element):
      list = self.pending.generatelist()
      self.pending.__init__()
    if isinstance(element, ListItem):
      element = self.processitem(element)
    elif isinstance(element, DeeperList):
      element = self.processnested(element)
    if not list:
      return element
    return Group().contents([list, element])

  def processitem(self, item):
    "Process a list item"
    self.pending.additem(item)
    return BlackBox()

  def processnested(self, nested):
    "Process a nested list"
    self.pending.addnested(nested)
    return BlackBox()

  def generatepending(self, element):
    "Decide whether to generate the pending list"
    if self.pending.empty():
      return False
    if isinstance(element, ListItem):
      if not self.pending.type:
        return False
      if self.pending.type != element.type:
        return True
      return False
    if isinstance(element, DeeperList):
      return False
    return True

Postprocessor.stages += [PostNestedList]
Postprocessor.unconditional += [PostListPending]









class BiblioCite(Container):
  "Cite of a bibliography entry"

  index = 0
  entries = dict()

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('sup')

  def process(self):
    "Add a cite to every entry"
    self.contents = list()
    keys = self.parser.parameters['key'].split(',')
    for key in keys:
      BiblioCite.index += 1
      number = unicode(BiblioCite.index)
      link = Link().complete(number, 'cite-' + number, '#' + number)
      self.contents.append(link)
      self.contents.append(Constant(','))
      if not key in BiblioCite.entries:
        BiblioCite.entries[key] = []
      BiblioCite.entries[key].append(number)
    if len(keys) > 0:
      # remove trailing ,
      self.contents.pop()

class Bibliography(Container):
  "A bibliography layout containing an entry"

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TaggedOutput().settag('p class="biblio"', True)

class BiblioEntry(Container):
  "A bibliography entry"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('span class="entry"')

  def process(self):
    "Process the cites for the entry's key"
    self.processcites(self.parser.parameters['key'])

  def processcites(self, key):
    "Get all the cites of the entry"
    cites = list()
    if key in BiblioCite.entries:
      cites = BiblioCite.entries[key]
    self.contents = [Constant('[')]
    for cite in cites:
      link = Link().complete(cite, cite, '#cite-' + cite)
      self.contents.append(link)
      self.contents.append(Constant(','))
    if len(cites) > 0:
      self.contents.pop(-1)
    self.contents.append(Constant('] '))

class PostBiblio(object):
  "Insert a Bibliography legend before the first item"

  processedclass = Bibliography

  def postprocess(self, element, last):
    "If we have the first bibliography insert a tag"
    if isinstance(last, Bibliography):
      return element
    bibliography = TranslationConfig.constants['bibliography']
    tag = TaggedText().constant(bibliography, 'h1 class="biblio"')
    return Group().contents([tag, element])

Postprocessor.stages.append(PostBiblio)




import os
import struct



import os
import os.path
import codecs


class Path(object):
  "Represents a generic path"

  def exists(self):
    "Check if the file exists"
    return os.path.exists(self.path)

  def open(self):
    "Open the file as readonly binary"
    return codecs.open(self.path, 'rb')

  def getmtime(self):
    "Return last modification time"
    return os.path.getmtime(self.path)

  def hasext(self, ext):
    "Check if the file has the given extension"
    base, oldext = os.path.splitext(self.path)
    return oldext == ext

  def __unicode__(self):
    "Return a unicode string representation"
    return self.path

  def __eq__(self, path):
    "Compare to another path"
    if not hasattr(path, 'path'):
      return False
    return self.path == path.path

class InputPath(Path):
  "Represents an input file"

  def __init__(self, url):
    "Create the input path based on url"
    self.url = url
    self.path = url
    if not os.path.isabs(url):
      self.path = Options.directory + os.path.sep + url

class OutputPath(Path):
  "Represents an output file"

  def __init__(self, inputpath):
    "Create the output path based on an input path"
    self.url = inputpath.url
    if os.path.isabs(self.url):
      self.url = os.path.basename(self.url)
    self.path = Options.destdirectory + os.path.sep + self.url
  
  def changeext(self, ext):
    "Change extension to the given one"
    base, oldext = os.path.splitext(self.path)
    self.path = base + ext
    base, oldext = os.path.splitext(self.url)
    self.url = base + ext

  def exists(self):
    "Check if the file exists"
    return os.path.exists(self.path)

  def createdirs(self):
    "Create any intermediate directories that don't exist"
    dir = os.path.dirname(self.path)
    if len(dir) > 0 and not os.path.exists(dir):
      os.makedirs(dir)



class Image(Container):
  "An embedded image"

  converter = True

  def __init__(self):
    self.parser = InsetParser()
    self.output = ImageOutput()

  def process(self):
    "Place the url, convert the image if necessary."
    self.origin = InputPath(self.parser.parameters['filename'])
    if not self.origin.exists():
      Trace.error('Image ' + unicode(self.origin) + ' not found')
      return
    self.destination = self.checkext(OutputPath(self.origin))
    self.convert(self.getparams())
    imagefile = ImageFile(self.destination)
    self.width, self.height = imagefile.getdimensions()

  def checkext(self, destination):
    "Convert extension of destination to output image format"
    forceformat = '.jpg'
    forcedest = '.png'
    if Options.forceformat:
      forceformat = Options.forceformat
      forcedest = Options.forceformat
    if not destination.hasext(forceformat):
      destination.changeext(forcedest)
    return destination

  def convert(self, params):
    "Convert an image to PNG"
    if not Image.converter:
      return
    if self.origin == self.destination:
      return
    if self.destination.exists():
      if self.origin.getmtime() <= self.destination.getmtime():
        # file has not changed; do not convert
        return
    self.destination.createdirs()
    command = 'convert '
    for param in params:
      command += '-' + param + ' ' + unicode(params[param]) + ' '
    command += '"' + unicode(self.origin) + '" "'
    command += unicode(self.destination) + '"'
    try:
      result = os.system(command)
      Trace.debug('ImageMagick Command: "' + command + '"')
      if result != 0:
        Trace.error('ImageMagick not installed; images will not be processed')
        Image.converter = False
        return
      Trace.message('Converted ' + unicode(self.origin) + ' to ' +
          unicode(self.destination))
    except OSError:
      Trace.error('Error while converting image ' + self.origin)

  def getparams(self):
    "Get the parameters for ImageMagick conversion"
    params = dict()
    scale = 100
    if 'scale' in self.parser.parameters:
      scale = int(self.parser.parameters['scale'])
    if self.origin.hasext('.svg'):
      params['density'] = scale
    elif self.origin.hasext('.jpg') or self.origin.hasext('.png'):
      params['resize'] = unicode(scale) + '%'
    return params

class ImageFile(object):
  "A file corresponding to an image (JPG or PNG)"

  dimensions = dict()

  def __init__(self, path):
    "Create the file based on its path"
    self.path = path

  def getdimensions(self):
    "Get the dimensions of a JPG or PNG image"
    if not self.path.exists():
      return None, None
    if unicode(self.path) in ImageFile.dimensions:
      return ImageFile.dimensions[unicode(self.path)]
    dimensions = (None, None)
    if self.path.hasext('.png'):
      dimensions = self.getpngdimensions()
    elif self.path.hasext('.jpg'):
      dimensions = self.getjpgdimensions()
    ImageFile.dimensions[unicode(self.path)] = dimensions
    return dimensions

  def getpngdimensions(self):
    "Get the dimensions of a PNG image"
    pngfile = self.path.open()
    pngfile.seek(16)
    width = self.readlong(pngfile)
    height = self.readlong(pngfile)
    pngfile.close()
    return (width, height)

  def getjpgdimensions(self):
    "Get the dimensions of a JPEG image"
    jpgfile = self.path.open()
    start = self.readword(jpgfile)
    if start != int('ffd8', 16):
      Trace.error(unicode(self.path) + ' not a JPEG file')
      return (None, None)
    self.skipheaders(jpgfile, ['ffc0', 'ffc2'])
    self.seek(jpgfile, 3)
    height = self.readword(jpgfile)
    width = self.readword(jpgfile)
    jpgfile.close()
    return (width, height)

  def skipheaders(self, file, hexvalues):
    "Skip JPEG headers until one of the parameter headers is found"
    headervalues = [int(value, 16) for value in hexvalues]
    header = self.readword(file)
    safetycounter = 0
    while header not in headervalues and safetycounter < 30:
      length = self.readword(file)
      if length == 0:
        Trace.error('End of file ' + file.name)
        return
      self.seek(file, length - 2)
      header = self.readword(file)
      safetycounter += 1

  def readlong(self, file):
    "Read a long (32-bit) value from file"
    return self.readformat(file, '>L', 4)

  def readword(self, file):
    "Read a 16-bit value from file"
    return self.readformat(file, '>H', 2)

  def readformat(self, file, format, bytes):
    "Read any format from file"
    read = file.read(bytes)
    if read == '':
      Trace.error('EOF reached')
      return 0
    tuple = struct.unpack(format, read)
    return tuple[0]

  def seek(self, file, bytes):
    "Seek forward, just by reading the given number of bytes"
    file.read(bytes)

class ImageOutput(object):
  "Returns an image in the output"

  def gethtml(self, container):
    "Get the HTML output of the image as a list"
    cssclass = 'embedded'
    html = ['<img class="' + cssclass + '"']
    if container.origin.exists():
      html.append(' src="' + container.destination.url +
          '" alt="figure ' + container.destination.url + '" width="' +
          unicode(container.width) + '" height="' + unicode(container.height) + '"')
    else:
      html.append(' src="' + container.origin.url + '"')
    html.append('/>\n')
    return html






class Float(Container):
  "A floating inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="float"', True)
    self.parent = None
    self.children = []
    self.number = None

  def process(self):
    "Get the float type"
    self.type = self.header[2]
    self.embed('div class="' + self.type + '"')
    for float in self.searchall(Float):
      float.parent = self
      self.children.append(float)

  def embed(self, tag):
    "Embed the whole contents in a div"
    tagged = TaggedText().complete(self.contents, tag, True)
    self.contents = [tagged]

class Wrap(Float):
  "A wrapped (floating) float"

  def process(self):
    "Get the wrap type"
    Float.process(self)
    placement = self.parameters['placement']
    self.output.tag = 'div class="wrap-' + placement + '"'

class Caption(Container):
  "A caption for a figure or a table"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="caption"', True)

class Listing(Float):
  "A code listing"

  def __init__(self):
    Float.__init__(self)
    self.numbered = None
    self.counter = 0

  def process(self):
    "Remove all layouts"
    self.processparams()
    self.type = 'listing'
    captions = self.searchremove(Caption)
    newcontents = []
    for container in self.contents:
      newcontents += self.extract(container)
    tagged = TaggedText().complete(newcontents, 'code class="listing"', True)
    self.contents = [TaggedText().complete(captions + [tagged],
      'div class="listing"', True)]

  def processparams(self):
    "Process listing parameteres"
    if not 'lstparams' in self.parameters:
      return
    paramlist = self.parameters['lstparams'].split(',')
    for param in paramlist:
      if not '=' in param:
        Trace.error('Invalid listing parameter ' + param)
      else:
        key, value = param.split('=', 1)
        self.parameters[key] = value
        if key == 'numbers':
          self.numbered = value

  def extract(self, container):
    "Extract the container's contents and return them"
    if isinstance(container, StringContainer):
      return self.modifystring(container)
    if isinstance(container, StandardLayout):
      return self.modifystring(container)
    Trace.error('Unexpected container ' + container.__class__.__name__ +
        ' in listing')
    return []

  def modifystring(self, string):
    "Modify a listing string"
    if len(string.contents) == 0:
      string.contents = [Constant(u'​')]
    contents = [string, Constant('\n')]
    if self.numbered:
      self.counter += 1
      tag = 'span class="number-' + self.numbered + '"'
      contents.insert(0, TaggedText().constant(unicode(self.counter), tag))
    return contents

class PostFloat(object):
  "Postprocess a float: number it and move the label"

  processedclass = Float

  def postprocess(self, float, last):
    "Move the label to the top and number the caption"
    captions = self.searchcaptions(float.contents)
    for caption in captions:
      self.postlabels(float, caption)
      self.postnumber(caption, float)
    return float

  def searchcaptions(self, contents):
    "Search for captions in the contents"
    list = []
    for element in contents:
      list += self.searchcaptionelement(element)
    return list

  def searchcaptionelement(self, element):
    "Search for captions outside floats"
    if isinstance(element, Float):
      return []
    if isinstance(element, Caption):
      return [element]
    if not isinstance(element, Container):
      return []
    return self.searchcaptions(element.contents)

  def postlabels(self, float, caption):
    "Search for labels and move them to the top"
    labels = caption.searchremove(Label)
    if len(labels) == 0:
      return
    float.contents = labels + float.contents

  def postnumber(self, caption, float):
    "Number the caption"
    self.numberfloat(float)
    prefix = TranslationConfig.floats[float.type]
    caption.contents.insert(0, Constant(prefix + float.number + u' '))

  def numberfloat(self, float):
    "Number a float if it isn't numbered"
    if float.number:
      return
    if float.parent:
      self.numberfloat(float.parent)
      index = float.parent.children.index(float)
      float.number = float.parent.number + NumberGenerator.letters[index + 1]
    else:
      float.number = NumberGenerator.instance.generatechaptered(float.type)

class PostWrap(PostFloat):
  "For a wrap: exactly like a float"

  processedclass = Wrap

class PostListing(PostFloat):
  "For a listing: exactly like a float"

  processedclass = Listing

Postprocessor.contents += [PostFloat, PostWrap, PostListing]




import sys


class FormulaCell(FormulaCommand):
  "An array cell inside a row"

  def __init__(self, alignment):
    FormulaCommand.__init__(self)
    self.alignment = alignment
    self.output = TaggedOutput().settag('td class="formula-' + alignment +'"', True)

  def parsebit(self, pos):
    formula = WholeFormula()
    if not formula.detect(pos):
      Trace.error('Unexpected end of array cell at ' + pos.remaining())
      return
    formula.parsebit(pos)
    self.add(formula)

class FormulaRow(FormulaCommand):
  "An array row inside an array"

  def __init__(self, alignments):
    FormulaCommand.__init__(self)
    self.alignments = alignments
    self.output = TaggedOutput().settag('tr', True)

  def parsebit(self, pos):
    "Parse a whole row"
    for cell in self.parsecells(pos):
      cell.parsebit(pos)
      self.add(cell)

  def parsecells(self, pos):
    "Parse all cells, finish when count ends"
    cellseparator = FormulaConfig.array['cellseparator']
    for index, alignment in enumerate(self.alignments):
      if self.anybutlast(index):
        pos.pushending(cellseparator)
      yield FormulaCell(alignment)
      if self.anybutlast(index):
        if not pos.checkfor(cellseparator):
          Trace.error('No cell separator ' + cellseparator)
        else:
          self.original += pos.popending(cellseparator)

  def anybutlast(self, index):
    "Return true for all cells but the last"
    return index < len(self.alignments) - 1

class FormulaArray(CommandBit):
  "An array within a formula"

  piece = 'array'

  def parsebit(self, pos):
    "Parse the array"
    self.output = TaggedOutput().settag('table class="formula"', True)
    self.parsealignments(pos)
    for row in self.parserows(pos):
      row.parsebit(pos)
      self.add(row)

  def parserows(self, pos):
    "Parse all rows, finish when no more row ends"
    rowseparator = FormulaConfig.array['rowseparator']
    while True:
      pos.pushending(rowseparator, True)
      yield FormulaRow(self.alignments)
      if pos.checkfor(rowseparator):
        self.original += pos.popending(rowseparator)
      else:
        return

  def parsealignments(self, pos):
    "Parse the different alignments"
    # vertical
    self.valign = 'c'
    vbracket = SquareBracket()
    if vbracket.detect(pos):
      vbracket.parseliteral(pos)
      self.valign = vbracket.literal
      self.add(vbracket)
    # horizontal
    bracket = Bracket().parseliteral(pos)
    self.add(bracket)
    self.alignments = []
    for l in bracket.literal:
      self.alignments.append(l)

class FormulaCases(FormulaArray):
  "A cases statement"

  piece = 'cases'

  def parsebit(self, pos):
    "Parse the cases"
    self.output = TaggedOutput().settag('table class="cases"', True)
    self.alignments = ['l', 'l']
    for row in self.parserows(pos):
      row.parsebit(pos)
      self.add(row)

class BeginCommand(CommandBit):
  "A \\begin command and what it entails (array or cases)"

  commandmap = {FormulaConfig.array['begin']:''}

  innerbits = [FormulaArray(), FormulaCases()]

  def parsebit(self, pos):
    "Parse the begin command"
    bracket = Bracket().parseliteral(pos)
    self.original += bracket.literal
    bit = self.findbit(bracket.literal)
    if not bit:
      return
    ending = FormulaConfig.array['end'] + '{' + bracket.literal + '}'
    pos.pushending(ending)
    bit.parsebit(pos)
    self.add(bit)
    self.original += pos.popending(ending)

  def findbit(self, piece):
    "Find the command bit corresponding to the \\begin{piece}"
    for bit in BeginCommand.innerbits:
      if bit.piece == piece:
        newbit = bit.clone()
        return newbit
    Trace.error('Unknown command \\begin{' + piece + '}')
    return None

FormulaCommand.commandbits += [BeginCommand()]







import os
import sys
import codecs


class BulkFile(object):
  "A file to treat in bulk"

  def __init__(self, filename):
    self.filename = filename
    self.temp = self.filename + '.temp'

  def readall(self):
    "Read the whole file"
    for encoding in FileConfig.parsing['encodings']:
      try:
        return self.readcodec(encoding)
      except UnicodeDecodeError:
        pass
    Trace.error('No suitable encoding for ' + self.filename)
    return []

  def readcodec(self, encoding):
    "Read the whole file with the given encoding"
    filein = codecs.open(self.filename, 'r', encoding)
    lines = filein.readlines()
    filein.close()
    return lines

  def getfiles(self):
    "Get reader and writer for a file name"
    reader = LineReader(self.filename)
    writer = LineWriter(self.temp)
    return reader, writer

  def swaptemp(self):
    "Swap the temp file for the original"
    os.chmod(self.temp, os.stat(self.filename).st_mode)
    os.rename(self.temp, self.filename)

  def __unicode__(self):
    "Get the unicode representation"
    return 'file ' + self.filename



class BibTeX(Container):
  "Show a BibTeX bibliography and all referenced entries"

  def __init__(self):
    self.parser = InsetParser()
    self.output = ContentsOutput()

  def process(self):
    "Read all bibtex files and process them"
    self.entries = []
    bibliography = TranslationConfig.constants['bibliography']
    tag = TaggedText().constant(bibliography, 'h1 class="biblio"')
    self.contents.append(tag)
    files = self.parser.parameters['bibfiles'].split(',')
    for file in files:
      bibfile = BibFile(file)
      bibfile.parse()
      self.entries += bibfile.entries
      Trace.message('Parsed ' + unicode(bibfile))
    self.entries.sort(key = unicode)
    self.applystyle()

  def applystyle(self):
    "Read the style and apply it to all entries"
    style = self.readstyle()
    for entry in self.entries:
      entry.template = style['default']
      if entry.type in style:
        entry.template = style[entry.type]
      entry.process()
      self.contents.append(entry)

  def readstyle(self):
    "Read the style from the bibliography options"
    options = self.parser.parameters['options'].split(',')
    for option in options:
      if hasattr(BibStylesConfig, option):
        return getattr(BibStylesConfig, option)
    return BibStylesConfig.default

class BibFile(object):
  "A BibTeX file"

  def __init__(self, filename):
    "Create the BibTeX file"
    self.filename = filename + '.bib'
    self.added = 0
    self.ignored = 0
    self.entries = []

  def parse(self):
    "Parse the BibTeX file"
    bibpath = InputPath(self.filename)
    bibfile = BulkFile(bibpath.path)
    parsed = list()
    for line in bibfile.readall():
      if not line.startswith('%') and not line.strip() == '':
        parsed.append(line)
    self.parseentries('\n'.join(parsed))

  def parseentries(self, text):
    "Extract all the entries in a piece of text"
    pos = Position(text)
    pos.skipspace()
    while not pos.finished():
      self.parseentry(pos)

  def parseentry(self, pos):
    "Parse a single entry"
    for entry in Entry.entries:
      if entry.detect(pos):
        newentry = entry.clone()
        newentry.parse(pos)
        if newentry.isreferenced():
          self.entries.append(newentry)
          self.added += 1
        else:
          self.ignored += 1
        return
    # Skip the whole line, and show it as an error
    pos.checkskip('\n')
    toline = pos.glob(lambda current: current != '\n')
    Trace.error('Unidentified entry: ' + toline)

  def __unicode__(self):
    "String representation"
    string = self.filename + ': ' + unicode(self.added) + ' entries added, '
    string += unicode(self.ignored) + ' entries ignored'
    return string

class Entry(Container):
  "An entry in a BibTeX file"

  entries = []
  structure = ['{', ',', '=', '"']
  quotes = ['{', '"', '#']

  def __init__(self):
    self.key = None
    self.tags = dict()
    self.output = TaggedOutput().settag('p class="biblio"')

  def parse(self, pos):
    "Parse the entry between {}"
    self.type = self.parsepiece(pos, Entry.structure)
    pos.skipspace()
    if not pos.checkskip('{'):
      self.lineerror(pos, 'Entry should start with {: ')
      return
    pos.pushending('}')
    self.parsetags(pos)
    pos.popending('}')
    pos.skipspace()

  def parsetags(self, pos):
    "Parse all tags in the entry"
    pos.skipspace()
    while not pos.finished():
      if pos.checkskip('{'):
        Trace.error('Unmatched {')
        return
      self.parsetag(pos)
  
  def parsetag(self, pos):
    piece = self.parsepiece(pos, Entry.structure)
    if pos.checkskip(','):
      self.key = piece
      return
    if pos.checkskip('='):
      piece = piece.lower().strip()
      pos.skipspace()
      value = self.parsevalue(pos)
      self.tags[piece] = value
      pos.skipspace()
      if not pos.finished() and not pos.checkskip(','):
        Trace.error('Missing , in BibTeX tag at ' + pos.current())
      return

  def parsevalue(self, pos):
    "Parse the value for a tag"
    pos.skipspace()
    if pos.checkfor(','):
      Trace.error('Unexpected ,')
      return ''
    if pos.checkfor('{'):
      return self.parsebracket(pos)
    elif pos.checkfor('"'):
      return self.parsequoted(pos)
    else:
      return self.parsepiece(pos, Entry.structure)

  def parsebracket(self, pos):
    "Parse a {} bracket"
    if not pos.checkskip('{'):
      Trace.error('Missing opening { in bracket')
      return ''
    pos.pushending('}')
    bracket = self.parserecursive(pos)
    pos.popending('}')
    return bracket

  def parsequoted(self, pos):
    "Parse a piece of quoted text"
    if not pos.checkskip('"'):
      Trace.error('Missing opening " in quote')
      return
    pos.pushending('"')
    quoted = self.parserecursive(pos)
    pos.popending('"')
    pos.skipspace()
    if pos.checkskip('#'):
      pos.skipspace()
      quoted += self.parsequoted(pos)
    return quoted

  def parserecursive(self, pos):
    "Parse brackets or quotes recursively"
    piece = ''
    while not pos.finished():
      piece += self.parsepiece(pos, Entry.quotes)
      if not pos.finished():
        if pos.checkfor('{'):
          piece += self.parsebracket(pos)
        elif pos.checkfor('"'):
          piece += self.parsequoted(pos)
        else:
          Trace.error('Missing opening { or ": ' + pos.current())
          return piece
    return piece

  def parsepiece(self, pos, undesired):
    "Parse a piece not structure"
    return pos.glob(lambda current: not current in undesired)

  def clone(self):
    "Return an exact copy of self"
    type = self.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

class SpecialEntry(Entry):
  "A special entry"

  types = ['@STRING', '@PREAMBLE', '@COMMENT']

  def detect(self, pos):
    "Detect the special entry"
    for type in SpecialEntry.types:
      if pos.checkfor(type):
        return True
    return False

  def isreferenced(self):
    "A special entry is never referenced"
    return False

  def __unicode__(self):
    "Return a string representation"
    return self.type

class PubEntry(Entry):
  "A publication entry"

  def detect(self, pos):
    "Detect a publication entry"
    return pos.checkfor('@')

  def isreferenced(self):
    "Check if the entry is referenced"
    if not self.key:
      return False
    return self.key in BiblioCite.entries

  def process(self):
    "Process the entry"
    biblio = BiblioEntry()
    biblio.processcites(self.key)
    self.contents = [biblio]
    self.contents.append(Constant(' '))
    self.contents.append(self.getcontents())

  def getcontents(self):
    "Get the contents as a constant"
    contents = self.template
    while contents.find('$') >= 0:
      tag = self.extracttag(contents)
      value = self.gettag(tag)
      contents = contents.replace('$' + tag, value)
    return Constant(contents)

  def extracttag(self, string):
    "Extract the first tag in the form $tag"
    pos = Position(string)
    pos.glob(lambda c: c != '$')
    pos.skip('$')
    return pos.globalpha()

  def __unicode__(self):
    "Return a string representation"
    string = ''
    author = self.gettag('author')
    if author:
      string += author + ': '
    title = self.gettag('title')
    if title:
      string += '"' + title + '"'
    return string

  def gettag(self, key):
    "Get a tag with the given key"
    if not key in self.tags:
      return ''
    return self.tags[key]

Entry.entries += [SpecialEntry(), PubEntry()]



class ContainerFactory(object):
  "Creates containers depending on the first line"

  def __init__(self):
    "Read table that convert start lines to containers"
    types = dict()
    for start, typename in ContainerConfig.starts.iteritems():
      types[start] = globals()[typename]
    self.tree = ParseTree(types)

  def createsome(self, reader):
    "Parse a list of containers"
    #Trace.debug('processing "' + reader.currentline().strip() + '"')
    if reader.currentline() == '':
      reader.nextline()
      return []
    type = self.tree.find(reader)
    container = type.__new__(type)
    container.__init__()
    container.start = reader.currentline().strip()
    self.parse(container, reader)
    return self.getlist(container)

  def parse(self, container, reader):
    "Parse a container"
    parser = container.parser
    parser.ending = self.getending(container)
    parser.factory = self
    container.header = parser.parseheader(reader)
    container.begin = parser.begin
    container.contents = parser.parse(reader)
    container.parameters = parser.parameters
    container.process()
    container.parser = None

  def getending(self, container):
    "Get the ending for a container"
    split = container.start.split()
    if len(split) == 0:
      return None
    start = split[0]
    if start in ContainerConfig.startendings:
      return ContainerConfig.startendings[start]
    classname = container.__class__.__name__
    if classname in ContainerConfig.endings:
      return ContainerConfig.endings[classname]
    if hasattr(container, 'ending'):
      Trace.error('Pending ending in ' + container.__class__.__name__)
      return container.ending
    return None

  def getlist(self, container):
    "Get a list of containers from one."
    "If appropriate, change the container for another(s)"
    if not isinstance(container, PlainLayout):
      return [container]
    return container.contents

class ParseTree(object):
  "A parsing tree"

  default = '~~default~~'

  def __init__(self, types):
    "Create the parse tree"
    self.root = dict()
    for start, type in types.iteritems():
      self.addstart(type, start)

  def addstart(self, type, start):
    "Add a start piece to the tree"
    tree = self.root
    for piece in start.split():
      if not piece in tree:
        tree[piece] = dict()
      tree = tree[piece]
    if ParseTree.default in tree:
      Trace.error('Start ' + start + ' duplicated')
    tree[ParseTree.default] = type

  def find(self, reader):
    "Find the current sentence in the tree"
    branches = [self.root]
    for piece in reader.currentline().split():
      current = branches[-1]
      piece = piece.rstrip('>')
      if piece in current:
        branches.append(current[piece])
    while not ParseTree.default in branches[-1]:
      Trace.error('Line ' + reader.currentline().strip() + ' not found')
      branches.pop()
    last = branches[-1]
    return last[ParseTree.default]



class eLyXerConverter(object):
  "Converter for a document in a lyx file"

  def __init__(self, filein, fileout):
    "Create the converter"
    self.reader = LineReader(filein)
    self.writer = LineWriter(fileout)

  def convert(self):
    "Perform the conversion for the document"
    try:
      if Options.toc:
        # generate TOC
        self.processcontents(lambda container: self.writetoc(container))
      else:
        # generate converted document
        self.processcontents(lambda container: self.writer.write(container.gethtml()))
    except (Exception):
      Trace.error('Conversion failed at ' + reader.currentline())
      raise

  def writetoc(self, container):
    "Write the table of contents for a container"
    if hasattr(container, 'number'):
      self.writer.write(container.type + ' ' + container.number + '\n')
    floats = container.searchall(Float)
    for float in floats:
      self.writer.write(float.type + ' ' + float.number + '\n')

  def processcontents(self, process):
    "Parse the contents and process it by containers"
    factory = ContainerFactory()
    postproc = Postprocessor()
    while not self.reader.finished():
      containers = factory.createsome(self.reader)
      for container in containers:
        container = postproc.postprocess(container)
        process(container)

