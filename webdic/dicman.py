#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Homepage: http://code.google.com/p/webdic/

License (MIT)
-------------
  Copyright (c) 2011, Yin Dian.
  
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  
  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
  
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.

'''
from wdutil import *
import wdcfg
from wdcfg import dictlist, hasdict, deldict, reorderdict
import diceng

dictpool = []
_usedpath = set()

def adddict(path):
	if os.path.abspath(path) in _usedpath:
		return
	for engine in diceng.enginepool.itervalues():
		ar = engine.getbasename(path)
		if ar:
			if type(ar) not in (type([]), type(())):
				ar = [ar]
			result = []
			for name in ar:
				name = wdcfg.adddict(path, name)
				dictpool.append(engine(name, path))
				result.append(name)
			_usedpath.add(os.path.abspath(path))
			return result

def deldict(basename):
	d = dict(wdcfg.dictlist())
	wdcfg.deldict(basename)
	path = d[basename]
	del d[basename]
	if path not in d.values():
		_usedpath.remove(os.path.abspath(path))

def dictnamelist():
	return wdcfg.dictlist()

if __name__ == '__main__':
	# test
	import pprint
	import pdb
	import traceback
	wdcfg.load()
	#pdb.set_trace()
	print adddict(r'Y:\temp\temp\newoxford\mob\out\En-Ch-newoxford.ifo')

# vim:ts=4:sw=4:noet:tw=80
