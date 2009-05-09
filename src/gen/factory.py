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
# Alex 20090509
# eLyXer factory to create and parse containers

from util.trace import Trace
from parse.parser import *
from io.output import *
from conf.config import *
from gen.styles import *
from ref.link import *
from ref.label import *
from ref.biblio import *
from math.formula import *
from math.command import *
from gen.table import *
from gen.image import *
from gen.structure import *
from gen.inset import *
from math.array import *


class ContainerFactory(object):
  "Creates containers depending on the first line"

  def __init__(self):
    "Read table that convert start lines to containers"
    typenames = ContainerConfig.starts
    types = dict()
    for start, typename in typenames.iteritems():
      types[start] = globals()[typename]
    self.tree = ParseTree(types)

  def create(self, reader):
    "Get the container and parse it"
    #Trace.debug('processing "' + reader.currentline() + '"')
    type = self.tree.find(reader)
    container = type.__new__(type)
    container.__init__()
    self.parse(container, reader)
    return container

  def parse(self, container, reader):
    "Parse a container"
    parser = container.parser
    if hasattr(container, 'ending'):
      #Trace.error('Pending ending in ' + container.__class__.__name__)
      parser.ending = container.ending
    parser.factory = self
    container.header = parser.parseheader(reader)
    container.begin = parser.begin
    container.contents = parser.parse(reader)
    container.parameters = parser.parameters
    container.process()
    container.parser = None



