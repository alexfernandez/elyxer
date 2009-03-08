#!/usr/bin/python
# -*- coding: utf-8 -*-

# Alex 20090308
# eLyXer
# Image treatment

import os.path
import subprocess
import array
from trace import Trace
from container import *
from output import MirrorOutput


class Image(Container):
  "An embedded image"

  start = '\\begin_inset Graphics'
  ending = '\\end_inset'

  def __init__(self):
    self.parser = ImageCommand()
    self.output = ImageOutput()
    self.figure = False

  def process(self):
    self.url = self.header[1]
    self.destination = os.path.splitext(self.url)[0] + '.png'
    factor = 100
    self.convert(self.url, self.destination, factor)
    self.width, self.height = self.getdimensions(self.destination)

  def convert(self, origin, destination, factor):
    "Convert an image to PNG"
    if not os.path.exists(origin):
      Trace.error('Error in image origin ' + origin)
      return
    if os.path.exists(destination) and os.path.getmtime(origin) <= os.path.getmtime(destination):
      # file has not changed; do not convert
      return
    dir = os.path.dirname(destination)
    if not os.path.exists(dir):
      os.makedirs(dir)
    Trace.debug('Converting ' + origin + ' to ' + destination + ' with density ' + str(factor))
    subprocess.call('convert -density ' + str(factor) + ' ' + origin + ' ' + destination, shell=True)

  dimensions = dict()

  def getdimensions(self, filename):
    "Get the dimensions of a PNG image"
    if filename in Image.dimensions:
      return Image.dimensions[filename]
    pngfile = codecs.open(filename, 'rb')
    pngfile.seek(16)
    dimensions = array.array('l')
    dimensions.fromfile(pngfile, 2)
    dimensions.byteswap()
    pngfile.close()
    Image.dimensions[filename] = dimensions
    return dimensions

class ImageOutput(object):
  "Returns an image in the output"

  def gethtml(self, container):
    "Get the HTML output of the image as a list"
    cssclass = 'embedded'
    if container.figure:
      cssclass = 'figure'
    return ['<img class="' + cssclass + '" src="' + container.destination +
        '" alt="figure ' + container.destination + '" width="' +
        str(container.width) + '" height="' + str(container.height) + '"/>\n']

