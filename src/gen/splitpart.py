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


class SplitPartLink(IntegralProcessor):
  "A link processor for multi-page output."

  processedtype = Link

  def processeach(self, link):
    "Process each link and add the current page."
    link.page = self.page

class SplitPartHeader(object):
  "The header that comes with a new split page."

  lastbasket = None

  def create(self, basket):
    "Write the header to the basket."
    basket.write(LyXHeader())
    return
    basket.write(self.createheader(basket))
    if self.lastbasket:
      self.lastbasket.nextlink.page = basket.page
    self.lastbasket = basket

  def createheader(self, basket):
    "Create the header with all links."
    prevlink = Link().complete('prev', url='', type='prev')
    prevlink.page = self.lastbasket.page
    nextlink = Link().complete('next', url='', type='next')
    basket.nextlink = nextlink
    toplink = Link().complete('top', url='', type='top')
    prevcontainer = TaggedText().complete([prevlink], 'span class="prev"')
    nextcontainer = TaggedText().complete([nextlink], 'span class="next"')
    topcontainer = TaggedText().complete([toplink], 'span class="top"')
    contents = [prevcontainer, topcontainer, nextcontainer]
    header = TaggedText().complete(contents, 'div class="splitheader"', True)
    return header

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
    header = SplitPartHeader()
    basket = self.addbasket(self.writer)
    for container in self.basket.contents:
      if self.mustsplit(container):
        filename = self.getfilename(container)
        Trace.debug('New page ' + filename)
        basket.write(LyXFooter())
        basket = self.addbasket(LineWriter(filename))
        header.create(basket)
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
    splitpartlink = SplitPartLink()
    splitpartlink.page = os.path.basename(basket.page)
    basket.processors = [splitpartlink]
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
    container.mustsplit = found[0].lower().replace('print', '')
    return True

  def getfilename(self, container):
    "Get the new file name for a given container."
    if hasattr(container, 'mustsplit'):
      partname = container.mustsplit
    else:
      if container.level == Options.splitpart and container.number != '':
        partname = container.number
      else:
        if container.number == '':
          partname = container.partkey.replace('toc-', '').replace('*', '-')
        else:
          partname = container.type + '-' + container.number
    return self.base + '-' + partname + self.extension

