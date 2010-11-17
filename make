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
./exportconfig.py py
./coalesce.py principal.py > ../elyxer.py
./coalesce.py loremipsumize.py > ../loremipsumize.py
./coalesce.py maths/math2html.py > ../math2html.py
cd ..
chmod 755 elyxer.py

# internationalize
cd src
./exportconfig.py po
cd ../po
for file in *.po; do
  lang=$(basename "$file" .po)
  mkdir -p locale/$lang/LC_MESSAGES
  msgfmt -o locale/$lang/LC_MESSAGES/elyxer.mo $lang.po
done
cd ..

# remove artifacts
rm -f docs/*.lyx~
rm -f test/*.lyx~
rm -f test/subdir/*.lyx~

# prepare documentation
./elyxer.py --title "eLyXer User Guide" --css "lyx.css" docs/userguide.lyx docs/userguide.html
./elyxer.py --toc --toctarget "userguide.html" --target "contents" --css "toc.css" docs/userguide.lyx docs/userguide-toc.html
./elyxer.py --title="eLyxer Developer Guide" --css "lyx.css" docs/devguide.lyx docs/devguide.html
./elyxer.py --title=eLyXer --css "lyx.css" docs/index.lyx docs/index.html
./elyxer.py --title="eLyXer changelog" --css "lyx.css" docs/changelog.lyx docs/changelog.html
./elyxer.py --title="eLyxer Math Showcase (non-Unicode edition)" --css "lyx.css" docs/math.lyx docs/math.html
./elyxer.py --title="eLyxer Math Showcase (Unicode edition)" --unicode --css "lyx.css" docs/math.lyx docs/math-unicode.html
./elyxer.py --title="eLyxer Math Showcase (ISO-8859-15 edition)" --iso885915 --css "lyx.css" docs/math.lyx docs/math-iso885915.html
./elyxer.py --title="eLyxer Math Showcase (jsMath edition)" --jsmath "./jsMath" --css "lyx.css" docs/math.lyx docs/math-jsmath.html
./elyxer.py --title="eLyxer Math Showcase (MathJax edition)" --mathjax "./MathJax" --css "lyx.css" docs/math.lyx docs/math-mathjax.html

# insert current version
VERSION=$(./elyxer.py --hardversion)
DATE=$(./elyxer.py --versiondate)
cd src
./textchange.py "the latest version" "the latest version $VERSION, created on $DATE," ../docs/index.html
cd ..

# run the test suite
./run-tests

