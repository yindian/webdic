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
import logging

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

def loaddicts():
	for name, path in wdcfg.dictlist():
		if not _adddict(path):
			wdcfg.deldict(name)

def adddict(paths):
	result = []
	if type(paths) in types.StringTypes:
		result = _adddict(paths)
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

def query(qstr, qtype=diceng.QRY_AUTO, cmd=diceng.CMD_QUERY, qparam=None, dictfilter=None, detailfilter=None):
	'Return a list of query results, each item containing dictionary basename, '
	'dictionary name, and entry list of word ID, word string and content ('
	'None if detailfilter(basename, qstr, qtype, word string) returns False).'
	dictlist = filter(dictpool.has_key, [n for n, p in wdcfg.dictlist()])
	dictlist = filter(dictfilter, dictlist)
	enginelist = map(dictpool.get, dictlist)
	if type(qstr) == types.StringType:
		try:
			qstr = qstr.decode('utf-8')
		except:
			logging.error('Query string is not UTF-8 encoded:' + qstr)
	logging.info('Query begin cmd:%d, qstr:%s, qtype:%d' % (cmd, qstr, qtype))
	diceng.asyncquery(enginelist, cmd=cmd, qstr=qstr, qtype=qtype, qparam=qparam)
	result = diceng.fetchresults()
	logging.info('Query end cmd:%d, qstr:%s, qtype:%d' % (cmd, qstr, qtype))
	if cmd != diceng.CMD_QUERY:
		return result
	toshow = []
	for engine, cmd, ar in result:
		if ar:
			entries = []
			for wordid, word in ar:
				if detailfilter and detailfilter(engine.basename, qstr, qtype,
						word):
					logging.info('Get detail for %s %s' % (engine.basename, wordid))
					content = engine.detail(wordid)[0][1]
					logging.info('Get detail done for %s %s' % (engine.basename, wordid))
				else:
					content = None
				entries.append((wordid, word, content))
			toshow.append((engine.basename, engine.name, entries))
	return toshow

def detail(basename, wordid):
	'Return a tuple of word, detail by given dictionary and wordid.'
	if not hasdict(basename):
		return None, None
	engine = dictpool[basename]
	result = engine.detail(wordid)
	return result and tuple(result[0]) or (None, None)

def resource(basename, resid):
	'Return a dictionary for the resource identified by given dictionary name'
	'and resource id. The possible key items in the dictionary is:\n'
	'1. "file": a file-like object\n'
	'2. "filename": the relative local file name of the resource\n'
	'3. "root": the root of local file name of the resource\n'
	'4. "mimetype": the mime type\n'
	'5. "buf": the buffer of the resource content\n'
	if not hasdict(basename):
		return {}
	engine = dictpool[basename]
	result = engine.resource(resid)
	logging.info('Got result for %s %s: %s' % (basename, resid, `result`))
	return result

def suggest(qstr, qtype=diceng.QRY_AUTO, qparam=None, dictfilter=None):
	'Return a list of search suggestion pattern strings'
	result = []
	if qstr and qstr[-1] != '*':
		result.append(qstr + '*')
	return result

if __name__ == '__main__':
	# test
	import pprint
	import pdb
	import traceback
	import time
	wdcfg.load()
	diceng.setcachedir(wdcfg.CACHEDIR)
	t = time.clock()
	loaddicts()
	diceng.diceng._taskqueue.join()
	print 'Loading time:', time.clock() - t
	print dictpool, _usedpath
	t = time.clock()
	print '&*:', pprint.pformat(query('&*'))
	print 'Query time:', time.clock() - t
	#d={}
	#def detailfilter(basename, qstr, qtype, word, d=d):
	#	if d.get(basename, 0) < 3:
	#		d[basename] = d.get(basename, 0) + 1
	#		return True
	#	return False
	#t = time.clock()
	#print '(*:', query('(*', detailfilter=detailfilter)
	#print 'Query time:', time.clock() - t
	for s, p in dictlist():
		deldict(s)
	print dictpool, _usedpath

# vim:ts=4:sw=4:noet:tw=80
