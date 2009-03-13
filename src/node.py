#! /usr/bin/env python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090131
# eLyXer general index and hierarchy

from trace import Trace
from container import *
from output import MirrorOutput
from link import *


class Hierarchy(object):
  "A hierarchy of elements"

  def __init__(self, filename):
    self.root = Node()
    self.root.level = 0
    self.root.filename = filename
    self.currentlist = [self.root]

  def add(self, container):
    "Add all elements in a container to the hierarchy"
    self.addcontainer(container)
    if not isinstance(container, Container):
      return
    for element in container.contents:
      self.add(element)
  
  def addcontainer(self, container):
    "Add a container to the hierarchy"
    if isinstance(container, NodeLink):
      # store node in link destination
      container.origin = self.getlatest()
      container.destination = self.getlatest()
      return
    if isinstance(container, Numbered):
      return
    if Node.hasnode(container):
      node = Node()
      node.setcontainer(container)
      self.addnode(node)
      node.process()
      return
    if Leaf.hasleaf(container):
      leaf = Leaf()
      leaf.setcontainer(container)
      self.addleaf(leaf)
      leaf.process()

  def addnode(self, node):
    "Add a new node at the given level"
    currentnode = self.getcurrent(node.level)
    currentnode.addnode(node)
    if node.level == len(self.currentlist):
      self.currentlist.append(node)
    else:
      self.currentlist[node.level] = node
    # cut further levels
    self.currentlist = self.currentlist[:node.level + 1]

  def addleaf(self, leaf):
    "Add a new leaf at its level"
    currentnode = self.getcurrent(leaf.level)
    if not currentnode:
      Trace.error('No level at ' + str(leaf.level) + ' for ' + str(leaf))
    currentnode.addleaf(leaf)
    leaf.filename = self.getlatest().filename

  def getcurrent(self, level):
    "Get the current node at a certain level"
    top = len(self.currentlist)
    if level > top:
      Trace.error('Level ' + str(level) + ' is beyond current level ' + str(top) +
          ' for ' + str(self.currentlist[-1]))
      return None
    if level < 1:
      Trace.error('Level ' + str(level) + ' is below 1')
      return None
    return self.currentlist[level - 1]

  def getlatest(self):
    "Get the latest node seen"
    return self.getcurrent(len(self.currentlist))

class Numbered(object):
  "The destination for a link"

  def __init__(self):
    self.number = list()
    self.filename = None
    self.parent = None

  def getnumber(self):
    "Get the number to show"
    number = ''
    for level in self.number:
      number += str(level) + '.'
    number += '.'
    return number.replace('..', '')

  def dashnumber(self):
    "Get the number separated by dashes"
    return self.getnumber().replace('.', '-')

  def getkey(self):
    "Get a unique key"
    return self.keyprefix + '-' + self.dashnumber()

  def leading(self):
    "Get the leading constant"
    if not self.name:
      return ''
    return self.name + ' ' + self.getnumber() + ': '

class Leaf(Numbered):
  "A node always at the end of the hierarchy"

  names = {'figure':'Figura', 'table':'Tabla', 'algorithm':'Listado'}

  @classmethod
  def hasleaf(cls, container):
    if not hasattr(container, 'type'):
      return False
    if not isinstance(container, Float):
      return False
    if not container.type in Leaf.names:
      return False
    return True

  def setcontainer(self, container):
    "Set the container for the leaf"
    self.container = container
    self.level = 2
    self.type = self.container.type

  def process(self):
    "Process the container contents"
    self.container.node = self
    self.name = Leaf.names[self.type]
    caption = self.container.searchfor(Caption)
    caption.contents.insert(0, Constant(self.leading()))
    label = caption.searchfor(Label)
    self.keyprefix = label.key.split(':')[0]
    label.node = self
    anchor = TaggedText().constant(' ', 'a class="leaf" name="' + self.getkey() + '"')
    self.container.contents.insert(0, anchor)

  def __str__(self):
    return 'Leaf ' + self.getnumber() + '(' + str(self.type) + ')'

class Node(Numbered):
  "Any node in the hierarchy"

  levels = {'Chapter':1, 'Section':2, 'Subsection':3, 'Subsubsection*':4}
  names = [u'Capítulo', u'Sección', u'Apartado', None]
  newfile = 2
  current = None

  @classmethod
  def hasnode(cls, container):
    if not hasattr(container, 'type'):
      return False
    if not container.type in Node.levels:
      return False
    return True

  def __init__(self):
    Numbered.__init__(self)
    self.children = list()
    self.branches = dict()
    self.next = None
    self.last = None
    self.up = None

  def setcontainer(self, container):
    "Set a container for the node"
    self.container = container
    self.level = Node.levels[container.type]
    self.name = Node.names[self.level - 1]

  def process(self):
    "Process the container contents"
    self.container.node = self
    if self.level <= Node.newfile:
      self.beginfile()
    label = self.container.searchfor(Label)
    if not label:
      self.container.contents.insert(0, Constant(self.leading()))
      self.keyprefix = '?'
      return
    self.keyprefix = label.key.split(':')[0]
    label.node = self
    tag = 'a class="node" name="' + self.getkey() + '"'
    anchor = TaggedText().constant(self.leading(), tag)
    self.container.contents.insert(0, anchor)

  def beginfile(self):
    "Begin a new file"
    self.filename = 'book-' + self.dashnumber() + '.html'
    if Node.current:
      Node.current.next = self
      self.last = Node.current
    Node.current = self

  def addnode(self, node):
    "Add a node"
    children = self.getchildren(node)
    self.add(node, children)

  def addleaf(self, leaf):
    "Add a leaf"
    branch = self.getbranch(leaf)
    self.add(leaf, branch)

  def add(self, thing, children):
    "Add a thing and set the number"
    children.append(thing)
    thing.parent = self
    thing.number = self.number[:] + [len(children)]
    if not thing.filename:
      thing.filename = self.filename

  def getchildren(self, node):
    "Get the node children"
    if node.level != self.level + 1:
      Trace.error('Node is not child node')
      return []
    return self.children

  def getbranch(self, leaf):
    "Get the right branch for the leaf"
    if leaf.level != self.level + 1:
      Trace.error('Leaf is not child leaf')
      return []
    if leaf.type not in self.branches:
      self.branches[leaf.type] = []
    return self.branches[leaf.type]

  def getname(self):
    "Get the name to display"
    if self.level >= len(Node.names):
      return None
    return Node.names[self.level]

  def __str__(self):
    return 'Node ' + self.getnumber() + '(' + str(self.level) + ')'


