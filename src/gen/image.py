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
# Alex 20090308
# eLyXer image treatment

import struct
import sys
import os
from util.trace import Trace
from util.translate import *
from gen.container import *
from io.path import *


class Image(Container):
  "An embedded image"

  ignoredtexts = StyleConfig.size['ignoredtexts']
  vectorformats = ImageConfig.formats['vector']
  rasterformats = ImageConfig.formats['raster']
  defaultformat = ImageConfig.formats['default']

  def __init__(self):
    self.parser = InsetParser()
    self.output = TaggedOutput()
    self.type = 'embedded'
    self.width = None
    self.height = None
    self.maxwidth = None
    self.maxheight = None
    self.scale = None

  def process(self):
    "Place the url, convert the image if necessary."
    self.origin = InputPath(self.parameters['filename'])
    if not self.origin.exists():
      Trace.error('Image ' + unicode(self.origin) + ' not found')
      return
    self.destination = self.getdestination(self.origin)
    self.setscale()
    ImageConverter.instance.convert(self)
    self.setsize()
    self.settag()

  def getdestination(self, origin):
    "Convert origin path to destination path."
    "Changes extension of destination to output image format."
    destination = OutputPath(origin)
    forceformat = '.jpg'
    forcedest = Image.defaultformat
    if Options.forceformat:
      forceformat = Options.forceformat
      forcedest = Options.forceformat
    if not destination.hasext(forceformat):
      destination.changeext(forcedest)
    destination.removebackdirs()
    return destination

  def setscale(self):
    "Set the scale attribute if present."
    self.setifparam('scale')

  def setsize(self):
    "Set the size attributes width and height."
    imagefile = ImageFile(self.destination)
    width, height = imagefile.getdimensions()
    if width:
      self.maxwidth = unicode(width) + 'px'
      if self.scale:
        self.width = self.scalevalue(width)
    if height:
      self.maxheight = unicode(height) + 'px'
      if self.scale:
        self.height = self.scalevalue(height)
    self.setifparam('width')
    self.setifparam('height')

  def setifparam(self, name):
    "Set the value in the container if it exists as a param."
    if not name in self.parameters:
      return
    value = unicode(self.parameters[name])
    for ignored in Image.ignoredtexts:
      if ignored in value:
        value = value.replace(ignored, '')
    setattr(self, name, value)

  def scalevalue(self, value):
    "Scale the value according to the image scale and return it as unicode."
    scaled = value * int(self.scale) / 100
    return unicode(int(scaled)) + 'px'

  def settag(self):
    "Set the output tag for the image."
    tag = 'img class="' + self.type + '"'
    if self.origin.exists():
      tag += self.imagetag()
    else:
      tag.append(' src="' + self.origin.url + '"')
    self.output.settag(tag, True, empty=True)

  def imagetag(self):
    "Get the part of the tag corresponding to the image."
    figure = Translator.translate('figure')
    tag = ' src="' + self.destination.url + '"'
    tag += ' alt="' + figure + ' ' + self.destination.url + '" style="'
    if self.width:
      tag += 'width: ' + self.width + '; '
    elif self.height:
      tag += 'width: auto; '
    if self.maxwidth:
      tag += 'max-width: ' + self.maxwidth + '; '
    if self.height:
      tag += 'height: ' + self.height + '; '
    elif self.width:
      tag += 'height: auto; '
    if self.maxheight:
      tag += 'max-height: ' + self.maxheight + '; '
    return tag + '"'

class ImageConverter(object):
  "A converter from one image file to another."

  active = True
  instance = None

  def convert(self, image):
    "Convert an image to PNG"
    if not ImageConverter.active:
      return
    if image.origin.path == image.destination.path:
      return
    if image.destination.exists():
      if image.origin.getmtime() <= image.destination.getmtime():
        # file has not changed; do not convert
        return
    image.destination.createdirs()
    converter, command = self.buildcommand(image)
    try:
      Trace.debug(converter + ' command: "' + command + '"')
      result = os.system(command.encode(sys.getfilesystemencoding()))
      if result != 0:
        Trace.error(converter + ' not installed; images will not be processed')
        ImageConverter.active = False
        return
      Trace.message('Converted ' + unicode(image.origin) + ' to ' +
          unicode(image.destination))
    except OSError, exception:
      Trace.error('Error while converting image ' + unicode(image.origin)
          + ': ' + unicode(exception))

  def buildcommand(self, image):
    "Build the command to convert the image."
    if not Options.converter in ImageConfig.converters:
      Trace.error('Converter ' + Options.converter + ' not configured.')
      ImageConverter.active = False
      return ''
    command = ImageConfig.converters[Options.converter]
    params = self.getparams(image)
    for param in params:
      command = command.replace('$' + param, unicode(params[param]))
    # remove unwanted options
    while '[' in command and ']' in command:
      command = self.removeparam(command)
    return Options.converter, command

  def removeparam(self, command):
    "Remove an unwanted param."
    if command.index('[') > command.index(']'):
      Trace.error('Converter command should be [...$...]: ' + command)
      exit()
    before = command[:command.index('[')]
    after = command[command.index(']') + 1:]
    between = command[command.index('[') + 1:command.index(']')]
    if '$' in between:
      return before + after
    return before + between + after

  def getparams(self, image):
    "Get the parameters for ImageMagick conversion"
    params = dict()
    params['input'] = image.origin
    params['output'] = image.destination
    if image.origin.hasexts(Image.vectorformats):
      scale = 100
      if image.scale:
        scale = image.scale
        # descale
        image.scale = None
      params['scale'] = scale
    # elif image.origin.hasext('.pdf'):
      # params['define'] = 'pdf:use-cropbox=true'
    return params

ImageConverter.instance = ImageConverter()

class ImageFile(object):
  "A file corresponding to an image (JPG or PNG)"

  dimensions = dict()

  def __init__(self, path):
    "Create the file based on its path"
    self.path = path

  def getdimensions(self):
    "Get the dimensions of a JPG or PNG image"
    if not self.path.exists():
      return None, None
    if unicode(self.path) in ImageFile.dimensions:
      return ImageFile.dimensions[unicode(self.path)]
    dimensions = (None, None)
    if self.path.hasext('.png'):
      dimensions = self.getpngdimensions()
    elif self.path.hasext('.jpg'):
      dimensions = self.getjpgdimensions()
    ImageFile.dimensions[unicode(self.path)] = dimensions
    return dimensions

  def getpngdimensions(self):
    "Get the dimensions of a PNG image"
    pngfile = self.path.open()
    pngfile.seek(16)
    width = self.readlong(pngfile)
    height = self.readlong(pngfile)
    pngfile.close()
    return (width, height)

  def getjpgdimensions(self):
    "Get the dimensions of a JPEG image"
    jpgfile = self.path.open()
    start = self.readword(jpgfile)
    if start != int('ffd8', 16):
      Trace.error(unicode(self.path) + ' not a JPEG file')
      return (None, None)
    self.skipheaders(jpgfile, ['ffc0', 'ffc2'])
    self.seek(jpgfile, 3)
    height = self.readword(jpgfile)
    width = self.readword(jpgfile)
    jpgfile.close()
    return (width, height)

  def skipheaders(self, file, hexvalues):
    "Skip JPEG headers until one of the parameter headers is found"
    headervalues = [int(value, 16) for value in hexvalues]
    header = self.readword(file)
    safetycounter = 0
    while header not in headervalues and safetycounter < 30:
      length = self.readword(file)
      if length == 0:
        Trace.error('End of file ' + file.name)
        return
      self.seek(file, length - 2)
      header = self.readword(file)
      safetycounter += 1

  def readlong(self, file):
    "Read a long (32-bit) value from file"
    return self.readformat(file, '>L', 4)

  def readword(self, file):
    "Read a 16-bit value from file"
    return self.readformat(file, '>H', 2)

  def readformat(self, file, format, bytes):
    "Read any format from file"
    read = file.read(bytes)
    if read == '':
      Trace.error('EOF reached')
      return 0
    tuple = struct.unpack(format, read)
    return tuple[0]

  def seek(self, file, bytes):
    "Seek forward, just by reading the given number of bytes"
    file.read(bytes)

