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
from wdcfg import reorderdict
import diceng
import types

dictpool = {}
_usedpath = set()

def _adddict(path):
	if os.path.abspath(path) in _usedpath:
		return
	for engine in diceng.iterengine():
		ar = engine.getbasename(path)
		if ar:
			if hasattr(ar, 'lower'):
				ar = [ar]
			result = []
			for name in ar:
				name = wdcfg.adddict(path, name)
				dictpool[name] = engine(name, path,
						lambda f: deldict(name))
				result.append(name)
			_usedpath.add(os.path.abspath(path))
			return result
	return []

def adddict(paths):
	result = []
	if type(paths) in types.StringTypes:
		result.append((paths, _adddict(paths)))
	else:
		for path in paths:
			result.append((path, _adddict(path)))
	diceng.diceng._taskqueue.join()
	return result

def deldict(basename):
	d = dict(wdcfg.dictlist())
	wdcfg.deldict(basename)
	del dictpool[basename]
	path = d[basename]
	del d[basename]
	if path not in d.values():
		_usedpath.remove(os.path.abspath(path))

def hasdict(basename):
	return dictpool.has_key(basename)

def dictlist():
	result = []
	for name, path in wdcfg.dictlist():
		if dictpool.has_key(name):
			result.append((name, path))
	return result

def dictnamelist():
	result = []
	for name, path in wdcfg.dictlist():
		if dictpool.has_key(name):
			result.append((name, dictpool[name].name))
	return result

def query(qstr, qtype=None, cmd=diceng.CMD_QUERY, qparam=None, dictfilter=None, detailfilter=None):
	dictlist = filter(dictpool.has_key, [n for n, p in wdcfg.dictlist()])
	dictlist = filter(dictfilter, dictlist)
	enginelist = map(dictpool.get, dictlist)
	diceng.asyncquery(enginelist, cmd=cmd, qstr=qstr, qtype=qtype, qparam=qparam)
	return diceng.fetchresults()

if __name__ == '__main__':
	# test
	import pprint
	import pdb
	import traceback
	import time
	wdcfg.load()
	diceng.setcachedir(wdcfg.CACHEDIR)
	#pdb.set_trace()
	t = time.clock()
	ar = adddict(r'Y:\temp\temp\newoxford\mob\out\En-Ch-newoxford.ifo')
	ar = adddict(r'Y:\temp\temp\newoxford\out\newoxford.ifo')
	ar = adddict(r'Y:\temp\temp\qqdict\Data\out\ecceqq.ifo')
	diceng.diceng._taskqueue.join()
	print 'Loading time:', time.clock() - t
	print ar
	print dictpool, _usedpath
	t = time.clock()
	print 'Hello:', pprint.pformat(query('hello'))
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'Hello:', pprint.pformat(query('Hello', diceng.QRY_BEGIN))
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'yours:', pprint.pformat(query('yours', diceng.QRY_BEGIN))
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'y:'
	query('y', diceng.QRY_BEGIN)
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'y:', query('y', diceng.QRY_BEGIN, diceng.CMD_QRYNUM)
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'a:', query('a', diceng.QRY_BEGIN, diceng.CMD_QRYNUM)
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'a:'
	query('a', diceng.QRY_BEGIN)
	print 'Query time:', time.clock() - t
	t = time.clock()
	print ':', query('', diceng.QRY_BEGIN, diceng.CMD_QRYNUM)
	print 'Query time:', time.clock() - t
	print 'a:'
	query('a', diceng.QRY_BEGIN)
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'a:', pprint.pformat(query('a', diceng.QRY_BEGIN, qparam=10))
	print 'Query time:', time.clock() - t
	t = time.clock()
	print 'cop:'
	query('cop', cmd=diceng.CMD_DETAIL)
	print 'Query time:', time.clock() - t
	for s, p in dictlist():
		deldict(s)
	print dictpool, _usedpath

# vim:ts=4:sw=4:noet:tw=80
