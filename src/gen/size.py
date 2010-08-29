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
    self.readparameter(container, 'width')
    self.readparameter(container, 'height')
    return self

  def readparameter(self, container, name):
    "Read a size parameter off a container."
    if not name in container.parameters:
      return
    result = container.parameters[name]
    if TextPosition(result).globnumber() == '0':
      Trace.debug('Zero width: ' + result)
      return
    Trace.debug('Container ' + name + ': ' + result)
    setattr(self, name, result)

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

