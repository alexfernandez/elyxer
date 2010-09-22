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
# Alex 20100828
# Container size parsing and output

from util.trace import Trace
from gen.container import *


class ContainerSize(object):
  "The size of a container."

  width = None
  height = None
  maxwidth = None
  maxheight = None
  scale = None

  def set(self, width = None, height = None):
    "Set the proper size with width and height."
    if width:
      self.width = width
    if height:
      self.height = height
    return self

  def setmax(self, maxwidth = None, maxheight = None):
    "Set max width and/or height."
    if maxwidth:
      self.maxwidth = maxwidth
    if maxheight:
      self.maxheight = maxheight
    return self

  def readparameters(self, container):
    "Read some size parameters off a container."
    self.setparameter(container, 'width')
    self.setparameter(container, 'height')
    self.setparameter(container, 'scale')
    self.checkvalidheight(container)
    return self

  def setparameter(self, container, name):
    "Read a size parameter off a container, and set it if present."
    value = self.extractparameter(container, name)
    if value:
      setattr(self, name, value)

  def checkvalidheight(self, container):
    "Check if the height parameter is valid; otherwise erase it."
    heightspecial = self.extractparameter(container, 'height_special')
    if self.height and self.extractnumber(self.height) == '1' and heightspecial == 'totalheight':
      self.height = None

  def extractparameter(self, container, name):
    "Extract a parameter from a container, if present."
    if not name in container.parameters:
      return None
    result = container.parameters[name]
    if self.extractnumber(result) == '0':
      return None
    for ignored in StyleConfig.size['ignoredtexts']:
      if ignored in result:
        result = result.replace(ignored, '')
    return result

  def extractnumber(self, text):
    "Extract the first number in the given text."
    result = ''
    decimal = False
    for char in text:
      if char.isdigit():
        result += char
      elif char == '.' and not decimal:
        result += char
        decimal = True
      else:
        return result
    return result

  def checkimage(self, width, height):
    "Check image dimensions, set them if possible."
    if width:
      self.maxwidth = unicode(width) + 'px'
      if self.scale and not self.width:
        self.width = self.scalevalue(width)
    if height:
      self.maxheight = unicode(height) + 'px'
      if self.scale and not self.height:
        self.height = self.scalevalue(height)
    if self.width and not self.height:
      self.height = 'auto'
    if self.height and not self.width:
      self.width = 'auto'

  def scalevalue(self, value):
    "Scale the value according to the image scale and return it as unicode."
    scaled = value * int(self.scale) / 100
    return unicode(int(scaled)) + 'px'

  def removepercentwidth(self):
    "Remove percent width if present, to set it at the figure level."
    if not self.width:
      return None
    if not '%' in self.width:
      return None
    width = self.width
    self.width = None
    if self.height == 'auto':
      self.height = None
    return width

  def addstyle(self, container):
    "Add the proper style attribute to the output tag."
    if not isinstance(container.output, TaggedOutput):
      Trace.error('No tag to add style, in ' + unicode(container))
    if not self.width and not self.height and not self.maxwidth and not self.maxheight:
      # nothing to see here; move along
      return
    tag = ' style="'
    tag += self.styleparameter('width')
    tag += self.styleparameter('maxwidth')
    tag += self.styleparameter('height')
    tag += self.styleparameter('maxheight')
    if tag[-1] == ' ':
      tag = tag[:-1]
    tag += '"'
    container.output.tag += tag

  def styleparameter(self, name):
    "Get the style for a single parameter."
    value = getattr(self, name)
    if value:
      return name.replace('max', 'max-') + ': ' + value + '; '
    return ''

