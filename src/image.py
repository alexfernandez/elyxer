#!/usr/bin/python
# -*- coding: utf-8 -*-

# eLyXer: LyX to HTML converter
# Copyright 2009 Alex Fernández
# Published under the GPLv3, see LICENSE for details

# Alex 20090308
# eLyXer image treatment

import os
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

  converter = True

  def __init__(self):
    self.parser = ImageCommand()
    self.output = ImageOutput()
    self.figure = False

  def process(self):
    self.url = self.relativepath(self.header[1])
    if not os.path.exists(self.url):
      Trace.error('Image ' + self.url + ' does not exist')
      return
    self.destination = os.path.splitext(self.url)[0] + '.png'
    factor = 100
    self.convert(self.url, self.destination, factor)
    self.width, self.height = self.getdimensions(self.destination)

  def convert(self, origin, destination, factor):
    "Convert an image to PNG"
    if not Image.converter:
      return
    if origin == destination:
      return
    if os.path.exists(destination):
      if os.path.getmtime(origin) <= os.path.getmtime(destination):
        # file has not changed; do not convert
        return
    dir = os.path.dirname(destination)
    if len(dir) > 0 and not os.path.exists(dir):
      os.makedirs(dir)
    try:
      result = subprocess.call('convert -density ' + str(factor) + ' '
          + origin + ' ' + destination, shell=True)
      if result != 0:
        Trace.error('ImageMagick not installed; images will not be processed')
        Image.converter = False
        return
      Trace.debug('Converted ' + origin + ' to ' + destination
          + ' with density ' + str(factor))
    except OSError:
      Trace.error('Error while converting image ' + origin)

  dimensions = dict()

  def getdimensions(self, filename):
    "Get the dimensions of a PNG image"
    if not os.path.exists(filename):
      return None, None
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

  def relativepath(self, url):
    "Convert the given path to a relative path"
    path = os.path.realpath(url)
    current = os.path.realpath(os.getcwd())
    common = os.path.commonprefix([path, current])
    return path[len(common) + 1:]

class ImageOutput(object):
  "Returns an image in the output"

  def gethtml(self, container):
    "Get the HTML output of the image as a list"
    cssclass = 'embedded'
    if container.figure:
      cssclass = 'figure'
    html = ['<img class="' + cssclass + '"']
    if hasattr(container, 'destination'):
      html.append(' src="' + container.destination +
          '" alt="figure ' + container.destination + '" width="' +
          str(container.width) + '" height="' + str(container.height) + '"')
    else:
      html.append(' src="' + container.url + '"')
    html.append('/>\n')
    return html

ContainerFactory.types.append(Image)

