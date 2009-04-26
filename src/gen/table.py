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
    self.columns = list()

  def setcolumns(self, columns):
    "Process alignments for every column"
    if len(columns) != len(self.contents):
      Trace.error('Columns: ' + str(len(columns)) + ', cells: ' + str(len(self.contents)))
      return
    for index, column in enumerate(columns):
      alignment = column['alignment']
      if alignment == 'block':
        alignment = 'justify'
      self.contents[index].setalignment(alignment)
      valignment = column['valignment']
      self.contents[index].setvalignment(valignment)

class Cell(Container):
  "A cell in a table"

  start = '<cell'
  ending = '</cell'

  def __init__(self):
    self.parser = TablePartParser()
    self.output = TaggedOutput().settag('td', True)

  def setmulticolumn(self, span):
    "Set the cell as multicolumn"
    self.setattribute('colspan', span)

  def setalignment(self, alignment):
    "Set the alignment for the cell"
    self.setattribute('align', alignment)

  def setvalignment(self, valignment):
    "Set the vertical alignment"
    self.setattribute('valign', valignment)

  def setattribute(self, attribute, value):
    "Set a cell attribute in the tag"
    self.output.tag += ' ' + attribute + '="' + unicode(value) + '"'

class TableParser(BoundedDummy):
  "Parse the whole table"

  ending = '</lyxtabular'
  column = '<column'

  def __init__(self):
    BoundedDummy.__init__(self)
    self.columns = list()

  def parse(self, reader):
    "Parse table header as parameters, rows and end of table"
    contents = []
    while not self.checkcurrent(reader, TableParser.ending):
      if self.checkcurrent(reader, Row.start):
        row = self.factory.create(reader)
        row.setcolumns(self.columns)
        contents.append(row)
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

ContainerFactory.types += [Table, Row, Cell]

