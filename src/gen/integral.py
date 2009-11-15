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


class IntegralProcessor(object):
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

class IntegralTOC(IntegralProcessor):
  "A processor for an integral TOC."

  processedtype = TableOfContents

  def processeach(self, toc):
    "Fill in a Table of Contents."
    toc.output = TaggedOutput().settag('div class="fulltoc"', True)
    basket = TOCBasket()
    for container in self.contents:
      entries = basket.translate(container)
      for entry in entries:
        toc.contents.append(entry)

class IntegralBiblioEntry(IntegralProcessor):
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

class IntegralFloat(IntegralProcessor):
  "Store all floats in the document by type."

  processedtype = Float
  bytype = dict()

  def processeach(self, float):
    "Store each float by type."
    if not float.type in IntegralFloat.bytype:
      IntegralFloat.bytype[float.type] = []
    IntegralFloat.bytype[float.type].append(float)

class IntegralListOf(IntegralProcessor):
  "A processor for an integral list of floats."

  processedtype = ListOf
  basket = TOCBasket()

  def processeach(self, listof):
    "Fill in a list of floats."
    Trace.debug('List of ' + listof.type)
    listof.output = TaggedOutput().settag('div class="fulltoc"', True)
    if not listof.type in IntegralFloat.bytype:
      Trace.message('No floats of type ' + listof.type)
      return
    for float in IntegralFloat.bytype[listof.type]:
      entry = self.processfloat(float)
      if entry:
        listof.contents.append(entry)

  def processfloat(self, float):
    "Get an entry for the list of floats."
    if float.parentfloat:
      return None
    captions = float.searchall(Caption)
    Trace.debug(float.type + ', ' + float.number + ', captions: ' + unicode(len(captions)))
    return Constant('a')

IntegralProcessor.processors = [IntegralTOC(), IntegralBiblioEntry(), IntegralFloat(), IntegralListOf()]

class MemoryBasket(KeeperBasket):
  "A basket which stores everything in memory, processes it and writes it."

  def finish(self):
    "Process everything which cannot be done in one pass and write to disk."
    for processor in IntegralProcessor.processors:
      processor.contents = self.contents
    self.searchintegral()
    for processor in IntegralProcessor.processors:
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
    for processor in IntegralProcessor.processors:
      if processor.locate(container):
        return True
    return False

  def integralstore(self, contents, index):
    "Store a container."
    container = contents[index]
    for processor in IntegralProcessor.processors:
      if processor.locate(container):
        processor.store(container)
        return
    Trace.error('No processor wanted to store ' + unicode(container))

