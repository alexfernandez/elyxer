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
# Alex 20100128
# eLyXer link postprocessing

from util.trace import Trace
from ref.label import *
from ref.biblio import *
from gen.layout import *
from post.postprocess import *


class PostBiblio(object):
  "Insert a Bibliography legend before the first item"

  processedclass = Bibliography

  def postprocess(self, last, element, next):
    "If we have the first bibliography insert a tag"
    if isinstance(last, Bibliography) or Options.nobib:
      return element
    bibliography = Translator.translate('bibliography')
    header = TaggedText().constant(bibliography, 'h1 class="biblio"')
    layout = StandardLayout().complete([header, element])
    return layout

class PostLabel(object):
  "Postprocessing of a label: assign number of the referenced part."

  processedclass = Label

  def postprocess(self, last, label, next):
    "Remember the last numbered container seen."
    label.lastnumbered = LayoutNumberer.instance.lastnumbered
    return label

Postprocessor.stages += [PostBiblio, PostLabel]

