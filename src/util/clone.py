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
# Alex 20091101
# eLyXer object cloning

from util.trace import Trace


class Cloner(object):
  "An object used to clone other objects."

  clonelist = ['contents']

  def clone(cls, original):
    "Return an exact copy of an object."
    "The original object must have an empty constructor."
    type = original.__class__
    clone = type.__new__(type)
    clone.__init__()
    return clone

  clone = classmethod(clone)

class ContainerExtractor(object):
  "A class to extract certain containers."

  def extract(self, container, config):
    "Extract a group of selected containers from a container."
    "The config parameter is a map containing three lists: allowed, copied and extracted."
    "Each of the three is a list of class names for containers."
    "Copied containers are copied as is into the result."
    "Allowed containers are cloned and placed into the result."
    "Extracted containers are looked into."
    list = []
    allow = lambda c: c.__class__.__name__ in config.allowed
    locate = lambda c: c.__class__.__name__ in config.extract
    process = lambda c: list.append(c)
    container.recursivesearch(allow, locate, process)
    return list

  def extractinside(self, container, config):
    "Extract from a container only if it is in the extracted list."
    if not container.__class__.__name__ in config['extracted']:
      return None
    return self.extract(container, config)


