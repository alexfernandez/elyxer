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


from util.translate import *
from gen.basket import *
from gen.integral import *


class SplitPartLink(IntegralProcessor):
  "A link processor for multi-page output."

  processedtype = Link

  def processeach(self, link):
    "Process each link and add the current page."
    link.page = self.page

class SplitPartNavigation(object):
  "Used to create the navigation links for a new split page."

  def __init__(self):
    self.upanchors = []
    self.lastcontainer = None
    self.nextlink = None
    self.lastnavigation = None

  def writeheader(self, basket, container):
    "Write the header to the basket."
    basket.write(LyXHeader().process())
    basket.write(self.createupanchor(container))
    self.lastnavigation = self.createnavigation(container)
    basket.write(self.lastnavigation)

  def writefooter(self, basket):
    "Write the footer to the basket."
    if self.lastnavigation:
      basket.write(self.lastnavigation)
    basket.write(LyXFooter())

  def createnavigation(self, container):
    "Create the navigation bar with all links."
    #upanchor = self.createupanchor(container)
    prevlink = Link().complete(' ', 'prev', type='prev')
    if self.nextlink:
      self.setlinkname(prevlink, Translator.translate('prev'), self.lastcontainer)
      self.setlinkname(self.nextlink, Translator.translate('next'), container)
      prevlink.setmutualdestination(self.nextlink)
    self.nextlink = Link().complete(' ', Translator.translate('next'), type='next')
    uplink = Link().complete(Translator.translate('up'), url='', type='up')
    self.setlinkname(uplink, Translator.translate('up'), self.getupdestination(container))
    uplink.destination = self.getupdestination(container)
    prevcontainer = TaggedText().complete([prevlink], 'span class="prev"')
    nextcontainer = TaggedText().complete([self.nextlink], 'span class="next"')
    upcontainer = TaggedText().complete([uplink], 'span class="up"')
    contents = [prevcontainer, Constant('\n'), upcontainer, Constant('\n'), nextcontainer]
    header = TaggedText().complete(contents, 'div class="splitheader"', True)
    self.lastcontainer = container
    return header
  
  def createupanchor(self, container):
    "Create the up anchor for the up links."
    level = self.getlevel(container)
    while len(self.upanchors) > level:
      del self.upanchors[-1]
    while len(self.upanchors) < level:
      self.upanchors.append(self.upanchors[-1])
    return self.insertupanchor()

  def insertupanchor(self):
    "Insert the up anchor into the list of anchors."
    upanchor = Link().complete('', '')
    upanchor.output = EmptyOutput()
    self.upanchors.append(upanchor)
    return upanchor

  def getupdestination(self, container):
    "Get the name of the up page."
    level = self.getlevel(container)
    if len(self.upanchors) < level:
      uppage = self.upanchors[-1]
    else:
      uppage = self.upanchors[level - 1]
    return uppage

  def getlevel(self, container):
    "Get the level of the container."
    if not hasattr(container, 'level'):
      return 1
    else:
      return container.level + 1

  def setlinkname(self, link, type, container):
    "Set the name on the link."
    if hasattr(container, 'mustsplit'):
      entry = container.mustsplit
    elif isinstance(container, Link):
      link.contents = [Constant(type)]
      return
    else:
      Trace.debug('Up: ' + unicode(container))
      entry = container.entry
    link.contents = [Constant(type + ': ' + entry)]

class SplitTOCBasket(MemoryBasket):
  "A memory basket which contains a split table of contents."

  def __init__(self):
    MemoryBasket.__init__(self)
    self.entrycount = 0
    self.root = None
    self.converter = TOCConverter()

  def write(self, container):
    "Keep track of numbered layouts."
    MemoryBasket.write(self, container)
    if not hasattr(container, 'partkey'):
      return
    entry = self.converter.convert(container)
    if not entry:
      return
    self.entrycount += 1
    self.root = entry

  def addtoc(self):
    "Add the table of contents if necessary."
    if self.entrycount != 1:
      return
    if self.root.branches == []:
      return
    text = Translator.translate('toc-for') + self.root.entry
    toc = TableOfContents().create(text)
    self.addbranches(self.root, toc)
    toc.add(self.converter.translate(LyXFooter()))
    self.write(toc)

  def addbranches(self, entry, toc):
    "Add an entry and all of its branches to the table of contents."
    for branch in entry.branches:
      toc.add(self.converter.indent(branch))
      self.addbranches(branch, toc)
  
class SplitPartBasket(Basket):
  "A basket used to split the output in different files."

  baskets = []

  def setwriter(self, writer):
    if not hasattr(writer, 'filename') or not writer.filename:
      Trace.error('Cannot use standard output for split output; ' +
          'please supply an output filename.')
      exit()
    self.writer = writer
    self.filename = writer.filename
    self.converter = TOCConverter()
    self.basket = MemoryBasket()
    self.basket.page = writer.filename
    return self

  def write(self, container):
    "Write a container, possibly splitting the file."
    self.basket.write(container)

  def finish(self):
    "Process the whole basket, create page baskets and flush all of them."
    self.basket.process()
    basket = self.firstbasket()
    navigation = SplitPartNavigation()
    basket.write(navigation.insertupanchor())
    for container in self.basket.contents:
      if self.mustsplit(container):
        filename = self.getfilename(container)
        Trace.debug('New page ' + filename)
        basket.addtoc()
        navigation.writefooter(basket)
        basket = self.addbasket(filename)
        navigation.writeheader(basket, container)
      basket.write(container)
    for basket in self.baskets:
      basket.process()
    for basket in self.baskets:
      basket.flush()

  def firstbasket(self):
    "Create the first basket."
    return self.addbasket(self.filename, self.writer)

  def addbasket(self, filename, writer = None):
    "Add a new basket."
    if not writer:
      writer = LineWriter(filename)
    basket = SplitTOCBasket()
    basket.setwriter(writer)
    self.baskets.append(basket)
    # set the page name everywhere
    basket.page = filename
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
    base, extension = os.path.splitext(self.filename)
    return base + '-' + partname + extension

