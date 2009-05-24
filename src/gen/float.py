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
# Alex 20090518
# LyX floats

from util.trace import Trace
from util.numbering import *
from parse.parser import *
from io.output import *
from gen.container import *
from gen.structure import *
from gen.layout import *
from ref.label import *
from post.postprocess import *


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
    self.embed()
    for float in self.searchall(Float):
      float.parent = self
      self.children.append(float)

  def embed(self):
    "Embed the whole contents in a div"
    tagged = TaggedText().complete(self.contents, 'div class="' + self.type + '"', True)
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

class Listing(Container):
  "A code listing"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('code class="listing"', True)
    self.numbered = None
    self.counter = 0

  def process(self):
    "Remove all layouts"
    self.processparams()
    newcontents = []
    for container in self.contents:
      newcontents += self.extract(container)
    Trace.debug('Contents: ' + unicode(newcontents))
    self.contents = newcontents
    Trace.debug('HTML: ' + unicode(self.gethtml()))

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
      return [container]
    if isinstance(container, Layout):
      return self.modifylayout(container.contents)
    if isinstance(container, Caption):
      return [container]
    Trace.error('Unexpected container ' + container.__class__.__name__ +
        ' in listing')
    return []

  def modifylayout(self, contents):
    "Modify a listing layout contents"
    if len(contents) == 0:
      contents = [Constant(u'​')]
    contents.append(Constant('\n'))
    if self.numbered:
      self.counter += 1
      tag = 'span class="number-' + self.numbered + '"'
      contents.insert(0, TaggedText().constant(unicode(self.counter), tag))
    return contents

class PostFloat(object):
  "Postprocess a float: number it and move the label"

  processedclass = Float

  def postprocess(self, float, last):
    "Postprocess captions and subfloats"
    if float.parent:
      return float
    float.number = NumberGenerator.instance.generatechaptered(float.type)
    self.postcaptions(float)
    self.postsubfloats(float)
    return float

  def postcaptions(self, float):
    "Move the label to the top and number the caption"
    captions = self.searchcaptions(float.contents)
    if len(captions) == 0:
      Trace.debug('No captions')
      return
    if len(captions) != 1:
      Trace.error('Too many captions in float: ' + unicode(len(captions)))
    for caption in captions:
      self.postlabels(float, caption)
    self.postnumber(captions[0], float)

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
      Trace.debug('Caption!')
      return [element]
    if not isinstance(element, Container):
      return []
    return self.searchcaptions(element.contents)

  def postlabels(self, float, caption):
    "Search for labels and move them to the top"
    labels = []
    caption.searchprocess(Label,
        lambda contents, index: self.searchremovelabels(labels, contents, index))
    if len(labels) == 0:
      return
    float.contents = labels + float.contents

  def searchremovelabels(self, list, contents, index):
    "Search for labels and remove them, returning the list"
    list.append(contents[index])
    del contents[index]

  def postnumber(self, caption, float):
    "Number the caption"
    Trace.debug('Post float ' + float.type + ': ' + unicode(float.number))
    prefix = TranslationConfig.floats[float.type]
    caption.contents.insert(0, Constant(prefix + float.number + u' '))

  def postsubfloats(self, float):
    "Postprocess subfloats"
    if not float.number:
      return
    prefix = TranslationConfig.floats[float.type]
    for index, subfloat in enumerate(float.children):
      subfloat.number = float.number + NumberGenerator.letters[index + 1]
      self.postcaptions(subfloat)

Postprocessor.contents.append(PostFloat)

