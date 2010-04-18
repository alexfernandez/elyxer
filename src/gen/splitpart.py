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
# Alex 20100418
# eLyXer split part processing
# http://www.nongnu.org/elyxer/


from gen.integral import *


class SplitPartBasket(Basket):
  "A basket used to split the output in different files."

  baskets = []

  def setwriter(self, writer):
    if not hasattr(writer, 'filename') or not writer.filename:
      Trace.error('Cannot use standard output for split output; ' +
          'please supply an output filename.')
      exit()
    self.writer = writer
    self.base, self.extension = os.path.splitext(writer.filename)
    self.converter = TOCConverter()
    self.basket = MemoryBasket()
    return self

  def write(self, container):
    "Write a container, possibly splitting the file."
    self.basket.write(container)

  def finish(self):
    "Process the whole basket, create page baskets and flush all of them."
    self.basket.process()
    basket = self.addbasket(self.writer)
    for container in self.basket.contents:
      if self.mustsplit(container):
        filename = self.getfilename(container)
        Trace.debug('New page ' + filename)
        basket.write(LyXFooter())
        basket = self.addbasket(LineWriter(filename))
        basket.write(LyXHeader())
      basket.write(container)
    for basket in self.baskets:
      basket.process()
    for basket in self.baskets:
      basket.flush()

  def addbasket(self, writer):
    "Add a new basket."
    basket = MemoryBasket()
    basket.setwriter(writer)
    self.baskets.append(basket)
    # set the page name everywhere
    basket.page = writer.filename
    integrallink = IntegralLink()
    integrallink.page = os.path.basename(basket.page)
    basket.processors = [integrallink]
    return basket

  def mustsplit(self, container):
    "Find out if the oputput file has to be split at this entry."
    if self.splitalone(container):
      return True
    if not hasattr(container, 'entry'):
      return False
    entry = self.converter.convert(container)
    if not entry:
      return False
    if hasattr(entry, 'split'):
      return True
    return entry.depth <= Options.splitpart

  def splitalone(self, container):
    "Find out if the container must be split in its own page."
    found = []
    container.locateprocess(
        lambda container: container.__class__ in [PrintNomenclature, PrintIndex],
        lambda container: found.append(container.__class__.__name__))
    if not found:
      return False
    container.depth = 0
    container.split = found[0].lower().replace('print', '')
    return True

  def getfilename(self, container):
    "Get the new file name for a given container."
    if hasattr(container, 'split'):
      partname = '-' + container.split
    else:
      entry = self.converter.convert(container)
      if entry.depth == Options.splitpart:
        partname = '-' + container.number
      else:
        partname = '-' + container.type + '-' + container.number
    return self.base + partname + self.extension

