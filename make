#!/bin/bash

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

# Alex 20090310: make script to generate "binary"

# create executable
cd src
./conflate.py elyxer.py > elyxer
mv elyxer ..
cd ..
chmod 755 elyxer
# prepare documentation
cd docs
rm -f *.png
../elyxer userguide.lyx userguide.html
../elyxer devguide.lyx devguide.html
../elyxer index.lyx index.html
rm -f *.lyx~
cd ..
# make compressed files
mkdir -p dist
cd ..
DATE=$(date +%Y%m%d)
tar --exclude "elyxer/dist" --exclude "elyxer/.git" \
  --exclude "elyxer/samples" --exclude "src/*.pyc" \
  -czf elyxer-$DATE.tar.gz elyxer
mv elyxer-$DATE.tar.gz elyxer/dist
zip -q elyxer-$DATE.zip elyxer/* -x *dist*
zip -qr elyxer-$DATE.zip elyxer/src/*.py
zip -qr elyxer-$DATE.zip elyxer/docs
zip -qr elyxer-$DATE.zip elyxer/test
mv elyxer-$DATE.zip elyxer/dist
cd elyxer
# run tests
echo "Testing eLyXer -- any text below this line signals an error"
cd test
for file in $(ls *.lyx); do
name=$(basename $file .lyx)
../elyxer --quiet $name.lyx $name-test.html
diff $name-test.html $name-good.html
done

