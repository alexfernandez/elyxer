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

class IntegralLayout(IntegralProcessor):
  "A processor for layouts that will appear in the TOC."

  processedtype = Layout
  tocentries = []

  def processeach(self, layout):
    "Keep only layouts that have an entry."
    if not hasattr(layout, 'entry'):
      return
    IntegralLayout.tocentries.append(layout)

class IntegralTOC(IntegralProcessor):
  "A processor for an integral TOC."

  processedtype = TableOfContents

  def processeach(self, toc):
    "Fill in a Table of Contents."
    toc.output = TaggedOutput().settag('div class="fulltoc"', True)
    converter = TOCConverter()
    for container in IntegralLayout.tocentries:
      toc.contents += converter.translate(container)
    # finish off with the footer to align indents
    toc.contents += converter.translate(LyXFooter())

  def writetotoc(self, entries, toc):
    "Write some entries to the TOC."
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
        cite.destination = link

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

  def processeach(self, listof):
    "Fill in a list of floats."
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
    link = self.createlink(float)
    return TaggedText().complete([link], 'div class="toc"', True)

  def createlink(self, float):
    "Create the link to the float label."
    captions = float.searchinside(float.contents, Caption)
    labels = float.searchinside(float.contents, Label)
    if len(labels) > 0:
      label = labels[0]
    else:
      label = Label().create(' ', float.entry.replace(' ', '-'))
      float.contents.insert(0, label)
      labels.append(label)
    if len(labels) > 1:
      Trace.error('More than one label in ' + float.entry)
    link = Link().complete(float.entry + u': ')
    for caption in captions:
      link.contents += caption.contents[1:]
    link.destination = label
    return link

class IntegralReference(IntegralProcessor):
  "A processor for a reference to a label."

  processedtype = Reference

  def processeach(self, reference):
    "Extract the text of the original label."
    text = self.extracttext(reference.destination)
    if text:
      reference.contents.insert(0, Constant(text))

  def extracttext(self, container):
    "Extract the final text for the label."
    while not hasattr(container, 'number'):
      if not hasattr(container, 'parent'):
        # no number; label must be in some unnumbered element
        return None
      container = container.parent
    return container.number

class MemoryBasket(KeeperBasket):
  "A basket which stores everything in memory, processes it and writes it."

  def __init__(self):
    "Create all processors in one go."
    KeeperBasket.__init__(self)
    self.processors = [
        IntegralLayout(), IntegralTOC(), IntegralBiblioEntry(),
        IntegralFloat(), IntegralListOf(), IntegralReference()
        ]

  def finish(self):
    "Process everything which cannot be done in one pass and write to disk."
    self.process()
    self.flush()

  def process(self):
    "Process everything with the integral processors."
    self.searchintegral()
    for processor in self.processors:
      processor.process()

  def searchintegral(self):
    "Search for all containers for all integral processors."
    for container in self.contents:
      # container.tree()
      if self.integrallocate(container):
        self.integralstore(container)
      container.locateprocess(self.integrallocate, self.integralstore)

  def integrallocate(self, container):
    "Locate all integrals."
    for processor in self.processors:
      if processor.locate(container):
        return True
    return False

  def integralstore(self, container):
    "Store a container in one or more processors."
    for processor in self.processors:
      if processor.locate(container):
        processor.store(container)

class IntegralLink(IntegralProcessor):
  "Integral link processing for multi-page output."

  processedtype = Link

  def processeach(self, link):
    "Process each link and add the current page."
    link.page = self.page

class SplittingBasket(Basket):
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
    if not hasattr(container, 'number'):
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

