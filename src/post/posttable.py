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
# Alex 20090420
# eLyXer postprocessor for tables

from util.trace import Trace
from gen.table import *
from post.postprocess import *


class PostTable(object):
  "Postprocess a table"

  def postprocess(self, current, last):
    "Look for a table and postprocess it"
    tables = current.searchall(Table)
    if len(tables) == 0:
      return current
    for table in current.searchall(Table):
      self.posttable(table)
    return current

  def posttable(self, table):
    "Postprocess the table"
    self.longtable(table)
    for row in table.contents:
      Trace.debug('Row: ' + str(row.parameters))
      for cell in row.contents:
        Trace.debug('Cell: ' + str(cell.parameters))

  def longtable(self, table):
    "Postprocess a long table, removing unwanted rows"
    if not 'features' in table.parameters:
      return
    features = table.parameters['features']
    if not 'islongtable' in features:
      return
    if features['islongtable'] != 'true':
      return
    if self.hasrow(table, 'endfirsthead'):
      self.removerows(table, 'endhead')
    if self.hasrow(table, 'endlastfoot'):
      self.removerows(table, 'endfoot')

  def hasrow(self, table, attrname):
    "Find out if the table has a row of first heads"
    for row in table.contents:
      if attrname in row.parameters:
        return True
    return False

  def removerows(self, table, attrname):
    "Remove the head rows, since the table has first head rows."
    for row in table.contents:
      if attrname in row.parameters:
        row.output = EmptyOutput()

Postprocessor.unconditional.append(PostTable)

