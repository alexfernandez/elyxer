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
# Alex 20090207
# eLyXer tables

from util.trace import Trace
from gen.container import *
from io.parse import *
from io.output import *


class Table(Container):
  "A lyx table"

  start = '\\begin_inset Tabular'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = TableParser()
    self.output = TaggedOutput().settag('table', True)

class Row(Container):
  "A row in a table"

  start = '<row'
  ending = '</row'

  def __init__(self):
    self.parser = TablePartParser()
    self.output = TaggedOutput().settag('tr', True)

  def process(self):
    if len(self.header) > 1:
      self.output.tag += ' class="header"'

class Cell(Container):
  "A cell in a table"

  start = '<cell'
  ending = '</cell'

  def __init__(self):
    self.parser = TablePartParser()
    self.output = TaggedOutput().settag('td', True)

class TableParser(BoundedDummy):
  "Parse the whole table"

  ending = '</lyxtabular'

  def parse(self, reader):
    "Parse table header as parameters, rows and end of table"
    contents = []
    while not reader.currentline().strip().startswith(TableParser.ending):
      if reader.currentline().strip().startswith(Row.start):
        row = self.factory.create(reader)
        contents.append(row)
      else:
        self.parseparameter(reader)
    BoundedDummy.parse(self, reader)
    return contents

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

ContainerFactory.types += [Table, Row, Cell]

