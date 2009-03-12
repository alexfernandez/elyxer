#! /usr/bin/env python
# -*- coding: utf-8 -*-

from parse import *
from output import *
from container import *

class CitationInset(Container):
  "An inset containing a bibitem citation"

  start = '\\begin_inset CommandInset citation'
  ending = '\\end_inset'

  index = 0
  citations = dict()

  def __init__(self):
    self.parser = BoundedParser()
    self.output = TagOutput()
    self.tag = 'sup'
    self.breaklines = False

  def process(self):
    #skip first line
    del self.contents[0]
    # parse second line: fixed string
    string = self.contents[0]
    key = string.contents[0].split('"')[1]
    # make index number
    CitationInset.index += 1
    number = str(CitationInset.index)
    # make tag and new contents
    tag = 'a class="citation" name="cit-' + number + '" href="#bib-' + number + '"'
    self.contents = [TaggedText().constant(number, tag)]
    # store for bibitem
    if not key in CitationInset.citations:
      CitationInset.citations[key] = list()
    CitationInset.citations[key].append(number)

class BibitemInset(Container):
  "An inset containing a bibitem command"
        
  start = '\\begin_inset CommandInset bibitem'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = BoundedParser()
    self.output = ContentsOutput()
    self.breaklines = False

  def process(self):
    #skip first line
    del self.contents[0]
    # parse second line: fixed string
    string = self.contents[0]
    # split around the "
    key = string.contents[0].split('"')[1]
    if not key in CitationInset.citations:
      self.contents = [Constant('[] ')]
      return
    self.contents = [Constant('[')]
    for number in CitationInset.citations[key]:
      tag = 'a class="bibitem" name="bib-' + number + '" href="#cit-' + number + '"'
      self.contents.append(TaggedText().constant(number, tag))
      self.contents.append(Constant(','))
    self.contents.pop()
    self.contents.append(Constant('] '))

ContainerFactory.types += [CitationInset, BibitemInset]

