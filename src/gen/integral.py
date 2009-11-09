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
# Alex 20091109
# eLyXer integral processing
# http://www.nongnu.org/elyxer/


from gen.factory import *
from gen.structure import *
from gen.basket import *


class Integral(object):
  "A processor for an integral document."

  processors = []

  def __init__(self):
    "Create the processor for the integral contents."
    self.storage = []

  def locate(self, container):
    "Locate only containers of the processed type."
    return isinstance(container, self.processedtype)

  def store(self, container):
    "Store a new container."
    self.storage.append(container)

  def process(self):
    "Process the whole storage."
    for container in self.storage:
      self.processeach(container)

class IntegralTOC(Integral):
  "A processor for an integral TOC."

  processedtype = TableOfContents

  def processeach(self, toc):
    "Fill in a Table of Contents."
    toc.output = TaggedOutput().settag('div class="fulltoc"', True)
    Trace.debug('Output tag: ' + toc.output.tag)
    basket = TOCBasket()
    basket.filterheader = True
    for container in self.contents:
      entry = basket.convert(container)
      if entry:
        toc.contents.append(basket.getindent(entry))
        toc.contents.append(entry)

class IntegralBiblioEntry(Integral):
  "A processor for an integral bibliography entry."

  processedtype = BiblioEntry

  def processeach(self, entry):
    "Process each entry."
    number = NumberGenerator.instance.generateunique('integralbib')
    link = Link().complete(number, 'biblio-' + number, type='biblioentry')
    entry.contents = [Constant('['), link, Constant('] ')]
    if entry.key in BiblioCite.cites:
      for cite in BiblioCite.cites[entry.key]:
        cite.complete(number, anchor = 'cite-' + number)
        cite.setdestination(link)

Integral.processors = [IntegralTOC(), IntegralBiblioEntry()]

class MemoryBasket(KeeperBasket):
  "A basket which stores everything in memory, processes it and writes it."

  def finish(self):
    "Process everything which cannot be done in one pass and write to disk."
    for processor in Integral.processors:
      processor.contents = self.contents
    self.searchintegral()
    for processor in Integral.processors:
      processor.process()
    self.flush()

  def searchintegral(self):
    "Search for all containers for all integral processors."
    for container in self.contents:
      if self.integrallocate(container):
        self.integralstore(container)
      else:
        container.locateprocess(self.integrallocate, self.integralstore)

  def integrallocate(self, container):
    "Locate all integrals."
    for processor in Integral.processors:
      if processor.locate(container):
        return True
    return False

  def integralstore(self, contents, index):
    "Store a container."
    container = contents[index]
    for processor in Integral.processors:
      if processor.locate(container):
        processor.store(container)
        return
    Trace.error('No processor wanted to store ' + unicode(container))

