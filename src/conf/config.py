#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer configuration
# autogenerated from config file on 2009-05-28

class ContainerConfig(object):
  "Configuration class from config file"

  endings = {
      u'Align':u'\\end_layout', u'BarredText':u'\\bar', 
      u'BoldText':u'\\series', u'Cell':u'</cell', u'ColorText':u'\\color', 
      u'EmphaticText':u'\\emph', u'FormulaArray':u'\\end{array}', 
      u'FormulaCases':u'\\end{cases}', u'Hfill':u'\\hfill', 
      u'Inset':u'\\end_inset', u'Layout':u'\\end_layout', 
      u'LyxFooter':u'\\end_document', u'LyxHeader':u'\\end_header', 
      u'Row':u'</row', u'ShapedText':u'\\shape', u'SizeText':u'\\size', 
      u'TextFamily':u'\\family', u'VersalitasText':u'\\noun', 
      }

  header = {
      u'branch':u'\\branch', u'endbranch':u'\\end_branch', 
      u'pdftitle':u'\\pdf_title', 
      }

  infoinsets = [
      u'shortcut', u'shortcuts', u'package', u'textclass', 
      ]

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
      u'\\begin_inset LatexCommand cite':u'BiblioCite', 
      u'\\begin_inset LatexCommand htmlurl':u'URL', 
      u'\\begin_inset LatexCommand index':u'IndexEntry', 
      u'\\begin_inset LatexCommand label':u'Label', 
      u'\\begin_inset LatexCommand nomenclature':u'NomenclatureEntry', 
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

  tableheaders = [
      u'<lyxtabular', u'<features', 
      ]

class EscapeConfig(object):
  "Configuration class from config file"

  chars = {
      u'\n':u'', u' -- ':u' — ', u'\'':u'’', u'`':u'‘', 
      }

  commands = {
      u'\\InsetSpace \\space{}':u'&nbsp;', u'\\InsetSpace \\thinspace{}':u' ', 
      u'\\InsetSpace ~':u'&nbsp;', u'\\SpecialChar \\@.':u'.', 
      u'\\SpecialChar \\ldots{}':u'…', 
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

  commands = {
      u'\\!':u'', u'\\%':u'%', u'\\,':u' ', u'\\:':u' ', 
      u'\\Longleftarrow':u'⟸', u'\\Longrightarrow':u'⟹', u'\\Omega':u'Ω', 
      u'\\Rightarrow':u' ⇒ ', u'\\\\':u'<br/>', u'\\_':u'_', 
      u'\\approx':u' ≈ ', u'\\backslash':u'\\', u'\\bigstar':u'★', 
      u'\\blacktriangleright':u'▶', u'\\bullet':u'•', u'\\cdot':u'⋅', 
      u'\\circ':u'○', u'\\cos':u'cos', u'\\cosh':u'cosh', u'\\dagger':u'†', 
      u'\\dashrightarrow':u' ⇢ ', u'\\ddagger':u'‡', u'\\ddots':u'⋱', 
      u'\\diamond':u'◇', u'\\displaystyle':u'', u'\\downarrow':u'↓', 
      u'\\end{array}':u'', u'\\exp':u'exp', u'\\ge':u' ≥ ', u'\\geq':u' ≥ ', 
      u'\\gets':u'←', u'\\implies':u'  ⇒  ', u'\\in':u' ∈ ', u'\\infty':u'∞', 
      u'\\int':u'<span class="bigsymbol">∫</span>', 
      u'\\intop':u'<span class="bigsymbol">∫</span>', u'\\langle':u'⟨', 
      u'\\leftarrow':u' ← ', u'\\leq':u' ≤ ', u'\\lim':u'lim', u'\\ln':u'ln', 
      u'\\log':u'log', u'\\lyxlock':u'', u'\\ne':u' ≠ ', u'\\neq':u'≠', 
      u'\\nonumber':u'', u'\\not':u'¬', u'\\phi':u'φ', u'\\pm':u'±', 
      u'\\prime':u'′', u'\\propto':u' ∝ ', u'\\quad':u' ', u'\\rangle':u'⟩', 
      u'\\rightarrow':u' → ', u'\\rightsquigarrow':u' ⇝ ', 
      u'\\scriptscriptstyle':u'', u'\\scriptstyle':u'', u'\\sim':u' ~ ', 
      u'\\sin':u'sin', u'\\sinh':u'sinh', u'\\square':u'□', 
      u'\\sum':u'<span class="bigsymbol">∑</span>', u'\\tanh':u'tanh', 
      u'\\textstyle':u'', u'\\times':u' × ', u'\\to':u'→', 
      u'\\triangleright':u'▷', u'\\uparrow':u'↑', u'\\{':u'{', u'\\}':u'}', 
      }

  decoratingfunctions = {
      u'\\acute':u'´', u'\\breve':u'˘', u'\\check':u'ˇ', u'\\ddot':u'¨', 
      u'\\dot':u'˙', u'\\grave':u'`', u'\\hat':u'^', u'\\tilde':u'˜', 
      u'\\vec':u'→', 
      }

  endings = {
      u'Cell':u'&', u'Row':u'\\\\', u'common':u'\\end', u'complex':u'\\]', 
      u'endafter':u'}', u'endbefore':u'\\end{', 
      }

  fontfunctions = {
      u'\\boldsymbol':u'b', u'\\mathbb':u'span class="blackboard"', 
      u'\\mathbf':u'b', u'\\mathcal':u'span class="script"', 
      u'\\mathfrak':u'span class="fraktur"', u'\\mathit':u'i', 
      u'\\mathrm':u'span class="mathrm"', u'\\mathsf':u'span class="mathsf"', 
      u'\\mathtt':u'tt', u'\\text':u'span class="text"', 
      u'\\textipa':u'span class="textipa"', u'\\textrm':u'span class="mathrm"', 
      }

  fractionfunctions = [
      u'\\frac', u'\\nicefrac', 
      ]

  fractionspans = {
      u'first':u'span class="numerator"', 
      u'second':u'span class="denominator"', u'whole':u'span class="fraction"', 
      }

  labelfunctions = {
      u'\\label':u'a class="eqnumber" name="#"', 
      }

  limited = [
      u'\\sum', u'\\int', u'\\intop', 
      ]

  limits = [
      u'^', u'_', 
      ]

  modified = {
      u'\n':u'', u' ':u'', u'&':u'	', u'\'':u'’', u'+':u' + ', u',':u', ', 
      u'-':u' − ', u'/':u' ⁄ ', u'<':u' &lt; ', u'=':u' = ', u'>':u' &gt; ', 
      }

  onefunctions = {
      u'\\bar':u'span class="bar"', u'\\begin{array}':u'span class="arraydef"', 
      u'\\bigl':u'span class="bigsymbol"', u'\\bigr':u'span class="bigsymbol"', 
      u'\\left':u'span class="symbol"', u'\\mbox':u'span class="mbox"', 
      u'\\overline':u'span class="overline"', 
      u'\\right':u'span class="symbol"', u'\\sqrt':u'span class="sqrt"', 
      u'\\underline':u'u', u'^':u'sup', u'_':u'sub', 
      }

  starts = {
      u'FormulaArray':u'\\begin{array}', u'FormulaCases':u'\\begin{cases}', 
      u'FormulaCommand':u'\\', u'beginafter':u'}', u'beginbefore':u'\\begin{', 
      u'complex':u'\\[', u'root':u'\\sqrt', u'simple':u'$', 
      }

  unmodified = [
      u'.', u'*', u'€', u'(', u')', u'[', u']', u':', u'·', u'!', u';', u'|', 
      ]

class GeneralConfig(object):
  "Configuration class from config file"

  version = {
      u'date':u'2009-05-28', u'number':u'0.24', 
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
      u'Center':u'div', u'Chapter':u'h1', u'LyX-Code':u'pre', 
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

