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
import diceng
import os.path

def parseifo(path):
	f = open(path, 'r')
	try:
		if f.readline().rstrip('\n') != "StarDict's dict ifo file":
			raise diceng.ParseError('Invalid ifo file header')
		d = dict([l.rstrip('\n').split('=', 1) for l in f])
		if d.get('version') != '2.4.2':
			raise diceng.ParseError('Invalid ifo version')
		return (d['bookname'].decode('utf-8'),
				d['sametypesequence'],
				int(d['idxfilesize']),
				int(d['wordcount']),
				int(d.get('synwordcount', '0')),
				d)
	except:
		raise
	finally:
		f.close()

class StardictEngine(diceng.BaseDictionaryEngine):
	@staticmethod
	def _getbasename(path):
		root, ext = os.path.splitext(path)
		if ext.lower() == '.ifo':
			try:
				parseifo(path)
				return os.path.basename(root)
			except:
				pass
	def _load(self):
		print 'loading', self._basename
		self._name, self._sametypeseq, idxsize, self._wordcnt, self._syncnt, d\
				= parseifo(self._path)
	def _query(self, qstr, qtype=None, qparam=None):
		pass

def register():
	print 'Register Stardict'
	diceng.registerengine('stardict', StardictEngine)

# vim:ts=4:sw=4:noet:tw=80
