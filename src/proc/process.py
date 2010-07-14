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
# Alex 20100714
# eLyXer: internal processing code


from util.trace import *
from proc.postprocess import *


class Processor(object):
  "Process a container and its contents."

  prestages = []

  def __init__(self):
    self.postprocessor = Postprocessor()

  def preprocess(self, root):
    "Preprocess a root container with all prestages."
    if not root:
      return None
    for stage in self.prestages:
      root = stage.preprocess(root)
      if not root:
        return None
    return root

  def process(self, container):
    "Process a container and its contents, recursively."
    if not container:
      return
    for element in container.contents:
      self.process(element)
    container.process()

  def postprocess(self, root):
    "Postprocess the root container."
    return self.postprocessor.postprocess(root)

