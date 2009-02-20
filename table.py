#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090207
# Generate custom HTML version from Lyx document
# Tables
# Containers for Lyx data that output HTML

from trace import Trace
from container import Container
from parse import *
from output import *


class Table(Container):
  "A lyx table"

  start = '\\begin_inset Tabular'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'table'

class TableHeader(Container):
  "The headers for the table"

  starts = ['<lyxtabular', '<lyxtabular', '<features', '<column', '</lyxtabular']

  def __init__(self):
    self.parser = LoneCommand()
    self.output = EmptyOutput()

class Row(Container):
  "A row in a table"

  start = '<row'
  ending = '</row'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'tr'

  def process(self):
    if len(self.header) > 1:
      self.tag += ' class="header"'

class Cell(Container):
  "A cell in a table"

  start = '<cell'
  ending = '</cell'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.breaklines = True
    self.tag = 'td'


