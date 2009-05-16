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
# Alex 20090503
# eLyXer table parsing

from util.trace import Trace
from gen.container import *
from parse.parser import *
from io.output import *


class TableParser(BoundedDummy):
  "Parse the whole table"

  row = '<row'
  column = '<column'

  def __init__(self):
    BoundedDummy.__init__(self)
    self.columns = list()

  def parse(self, reader):
    "Parse table header as parameters, rows and end of table"
    contents = []
    while not self.checkcurrent(reader, ContainerConfig.endings[TableParser.__name__]):
      if self.checkcurrent(reader, TableParser.row):
        rows = self.factory.createsome(reader)
        contents += rows
      elif self.checkcurrent(reader, TableParser.column):
        self.parsecolumn(reader)
      else:
        self.parseparameter(reader)
    BoundedDummy.parse(self, reader)
    return contents

  def checkcurrent(self, reader, start):
    "Check if the current line starts with the given string"
    return reader.currentline().strip().startswith(start)

  def parsecolumn(self, reader):
    "Parse a column definition"
    self.parseparameter(reader)
    self.columns.append(self.parameters['column'])

class TablePartParser(BoundedParser):
  "Parse a table part (row or cell)"

  def parseheader(self, reader):
    "Parse the header"
    self.parsexml(reader)
    parameters = dict()
    if len(self.parameters) > 1:
      Trace.error('Too many parameters in table part')
    for key in self.parameters:
      parameters = self.parameters[key]
    self.parameters = parameters
    return list()


