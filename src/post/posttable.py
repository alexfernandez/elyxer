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

  processedclass = Table

  def postprocess(self, last, table, next):
    "Postprocess a table: long table, multicolumn rows"
    self.longtable(table)
    for row in table.contents:
      index = 0
      while index < len(row.contents):
        self.checkforplain(row, index)
        self.checkmulticolumn(row, index)
        index += 1
    return table

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

  def checkforplain(self, row, index):
    "Make plain layouts visible if necessary."
    cell = row.contents[index]
    plainlayouts = cell.searchall(PlainLayout)
    if len(plainlayouts) <= 1:
      return
    for plain in plainlayouts:
      plain.makevisible()

  def checkmulticolumn(self, row, index):
    "Process a multicolumn attribute"
    cell = row.contents[index]
    if not hasattr(cell, 'parameters') or not 'multicolumn' in cell.parameters:
      return
    mc = cell.parameters['multicolumn']
    if mc != '1':
      Trace.error('Unprocessed multicolumn=' + unicode(multicolumn) +
          ' cell ' + unicode(cell))
      return
    total = 1
    index += 1
    while self.checkbounds(row, index):
      del row.contents[index]
      total += 1
    cell.setmulticolumn(total)

  def checkbounds(self, row, index):
    "Check if the index is within bounds for the row"
    if index >= len(row.contents):
      return False
    if not 'multicolumn' in row.contents[index].parameters:
      return False
    if row.contents[index].parameters['multicolumn'] != '2':
      return False
    return True

Postprocessor.stages.append(PostTable)

