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
from gen.image import *
from ref.label import *
from post.postprocess import *


class Float(Container):
  "A floating inset"

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput().settag('div class="float"', True)
    self.parentfloat = None
    self.children = []
    self.number = None

  def process(self):
    "Get the float type."
    self.type = self.header[2]
    self.processfloats()
    self.processtags()
    self.processnumber()

  def processnumber(self):
    "Number a float if it isn't numbered"
    if self.number:
      return
    if self.parentfloat:
      self.parentfloat.processnumber()
      index = self.parentfloat.children.index(float)
      self.number = NumberGenerator.letters[index + 1].lower()
      self.entry = '(' + self.number + ')'
    else:
      self.number = NumberGenerator.instance.generatechaptered(self.type)
      self.entry = Translator.translate('float-' + self.type) + self.number

  def processtags(self):
    "Process the HTML tags."
    embeddedtag = self.getembeddedtag()
    wideningtag = self.getwideningtag()
    self.embed(embeddedtag + wideningtag)

  def processfloats(self):
    "Process all floats contained inside."
    floats = self.searchall(Float)
    for float in floats:
      float.output.tag = float.output.tag.replace('div', 'span')
      float.parentfloat = self
      self.children.append(float)

  def getembeddedtag(self):
    "Get the tag for the embedded object."
    floats = self.searchall(Float)
    if len(floats) > 0:
      return 'div class="multi' + self.type + '"'
    return 'div class="' + self.type + '"'

  def getwideningtag(self):
    "Get the tag to set float width, if present."
    images = self.searchall(Image)
    if len(images) != 1:
      return ''
    image = images[0]
    if not image.width:
      return ''
    if not '%' in image.width:
      return ''
    image.type = 'figure'
    width = image.width
    image.width = None
    return ' style="max-width: ' + width + ';"'

  def embed(self, tag):
    "Embed the whole contents in a div"
    tagged = TaggedText().complete(self.contents, tag, True)
    self.contents = [tagged]

  def searchinside(self, contents, type):
    "Search for a given type in the contents"
    list = []
    for element in contents:
      list += self.searchinelement(element, type)
    return list

  def searchinelement(self, element, type):
    "Search for a given type outside floats"
    if isinstance(element, Float):
      return []
    if isinstance(element, type):
      return [element]
    return self.searchinside(element.contents, type)

  def __unicode__(self):
    "Return a printable representation"
    return 'Floating inset of type ' + self.type

class Wrap(Float):
  "A wrapped (floating) float"

  def processtags(self):
    "Add the widening tag to the parent tag."
    embeddedtag = self.getembeddedtag()
    self.embed(embeddedtag)
    placement = self.parameters['placement']
    wideningtag = self.getwideningtag()
    self.output.tag = 'div class="wrap-' + placement + '"' + wideningtag

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
    self.parselstparams()
    self.type = 'listing'
    captions = self.searchremove(Caption)
    newcontents = []
    for container in self.contents:
      newcontents += self.extract(container)
    tagged = TaggedText().complete(newcontents, 'code class="listing"', False)
    self.contents = [TaggedText().complete(captions + [tagged],
      'div class="listing"', True)]
    self.processnumber()

  def processparams(self):
    "Process listing parameteres."
    self.parselstparams()
    if not 'numbers' in self.parameters:
      return
    self.numbered = self.parameters['numbers']

  def extract(self, container):
    "Extract the container's contents and return them"
    if isinstance(container, StringContainer):
      return self.modifystring(container)
    if isinstance(container, StandardLayout):
      return self.modifylayout(container)
    if isinstance(container, PlainLayout):
      return self.modifylayout(container)
    Trace.error('Unexpected container ' + container.__class__.__name__ +
        ' in listing')
    container.tree()
    return []

  def modifystring(self, string):
    "Modify a listing string"
    if string.string == '':
      string.string = u'​'
    return self.modifycontainer(string)

  def modifylayout(self, layout):
    "Modify a standard layout"
    if len(layout.contents) == 0:
      layout.contents = [Constant(u'​')]
    return self.modifycontainer(layout)

  def modifycontainer(self, container):
    "Modify a listing container"
    contents = [container, Constant('\n')]
    if self.numbered:
      self.counter += 1
      tag = 'span class="number-' + self.numbered + '"'
      contents.insert(0, TaggedText().constant(unicode(self.counter), tag))
    return contents

class PostFloat(object):
  "Postprocess a float: number it and move the label"

  processedclass = Float

  def postprocess(self, last, float, next):
    "Move the label to the top and number the caption"
    captions = float.searchinside(float.contents, Caption)
    for caption in captions:
      self.postlabels(float, caption)
      self.postnumber(caption, float)
    return float

  def postlabels(self, float, caption):
    "Search for labels and move them to the top"
    labels = caption.searchremove(Label)
    if len(labels) == 0:
      return
    float.contents = labels + float.contents

  def postnumber(self, caption, float):
    "Number the caption"
    caption.contents.insert(0, Constant(float.entry + u' '))

class PostWrap(PostFloat):
  "For a wrap: exactly like a float"

  processedclass = Wrap

class PostListing(PostFloat):
  "For a listing: exactly like a float"

  processedclass = Listing

Postprocessor.stages += [PostFloat, PostWrap, PostListing]

