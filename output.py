#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090203
# Generate custom HTML version from Lyx document
# Html outputters

import codecs
from trace import Trace


class EmptyOutput(object):
  "The output for some container"

  def gethtml(self, container):
    "Return empty HTML code"
    return []

class FixedOutput(object):
  "Fixed output"

  def gethtml(self, container):
    "Return constant HTML code"
    return container.html

class ContentsOutput(object):
  "Outputs the contents converted to HTML"

  def gethtml(self, container):
    "Return the HTML code"
    html = []
    for element in container.contents:
      html += element.gethtml()
    return html

class TagOutput(ContentsOutput):
  "Outputs an HTML tag surrounding the contents"

  def gethtml(self, container):
    "Return the HTML code"
    html = [self.getopen(container)]
    html += ContentsOutput.gethtml(self, container)
    html.append(self.getclose(container))
    return html

  def getopen(self, container):
    "Get opening line"
    if container.tag == '':
      return ''
    open = '<' + container.tag + '>'
    if container.breaklines:
      return open + '\n'
    return open

  def getclose(self, container):
    "Get closing line"
    if container.tag == '':
      return ''
    close = '</' + container.tag.split()[0] + '>'
    if container.breaklines:
      return '\n' + close + '\n'
    return close

class MirrorOutput(object):
  "Returns as output whatever comes along"

  def gethtml(self, container):
    "Return what is put in"
    return container.contents

