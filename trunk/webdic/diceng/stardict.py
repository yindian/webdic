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
import os, string, struct, re, gzip, dictzip
import logging, traceback

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

def getcachepath(basename, ext):
	return os.path.join(diceng.getcachedir(), basename + ext)

def hascache(root, basename, ext, size=0):
	path = getcachepath(basename, ext)
	if not os.path.exists(path):
		return False
	try:
		st = os.stat(path)
		if size and st.st_size != size:
			return False
		if st.st_mtime < os.stat(root + '.ifo').st_mtime:
			return False
	except:
		logging.error(traceback.format_exc())
		return False
	return True

idxentrypat = re.compile(r'(.*?)\x00.{8}', re.S)
synentrypat = re.compile(r'(.*?)\x00.{4}', re.S)
lower = string.lower

class StardictEngine(diceng.BaseDictionaryEngine):
	@staticmethod
	def _getbasename(path):
		root, ext = os.path.splitext(path)
		if ext.lower() == '.ifo':
			try:
				parseifo(path)
				return os.path.basename(root)
			except:
				logging.error(traceback.format_exc())
				pass
	def _load(self):
		print 'loading', self._basename
		self._name, self._sametypeseq, idxsize, self._wordcnt, self._syncnt, d\
				= parseifo(self._path)
		root, ext = os.path.splitext(self._path)
		try:
			self._idxf = open(root + '.idx', 'rb')
		except IOError:
			self._idxf = gzip.GzipFile(root + '.idx.gz', 'rb')
		if hascache(root, self._basename, '.pos', size=4*self._wordcnt):
			f = open(getcachepath(self._basename, '.pos'), 'rb')
			buf = f.read()
			f.close()
			self._indices = struct.unpack('<%dL' % (self._wordcnt,), buf)
			indices = None
		else:
			buf = self._idxf.read()
			assert self._idxf.tell() == idxsize
			indices = [] #(collated word, entry offset)
			pos = 0
			for s in idxentrypat.findall(buf):
				indices.append((lower(s.decode('utf-8')), pos))
				pos += len(s) + 9
			assert pos == idxsize
			indices.sort()
			self._indices = [p for s, p in indices]
			f = open(getcachepath(self._basename, '.pos'), 'wb')
			f.write(struct.pack('<%dL' % (self._wordcnt,), *self._indices))
			f.close()
		assert len(self._indices) == self._wordcnt
		if self._syncnt > 0:
			try:
				self._synf = open(root + '.syn', 'rb')
			except IOError:
				self._synf = gzip.GzipFile(root + '.syn.gz', 'rb')
			if hascache(root, self._basename, '.spo', size=4*(self._wordcnt +
				self._syncnt)):
				f = open(getcachepath(self._basename, '.spo'), 'rb')
				buf = f.read()
				f.close()
				self._synindices = struct.unpack('<%dL' % (len(buf)/4,), buf)
			else:
				if indices is None:
					buf = self._idxf.read()
					assert self._idxf.tell() == idxsize
					indices = [] #(collated word, entry offset)
					pos = 0
					for s in idxentrypat.findall(buf):
						indices.append((lower(s.decode('utf-8')), pos))
						pos += len(s) + 9
					assert pos == idxsize
				buf = self._synf.read()
				pos = 0
				for s in synentrypat.findall(buf):
					indices.append((lower(s.decode('utf-8')), pos & 0x8000000))
					pos += len(s) + 5
				assert len(indices) ==  self._wordcnt + self._syncnt
				indices.sort()
				self._synindices = [p for s, p in indices]
				f = open(getcachepath(self._basename, '.spo'), 'wb')
				f.write(struct.pack('<%dL' % (len(indices),),*self._synindices))
				f.close()
		else:
			self._synf = self._synindices = None
	def _query(self, qstr, qtype=None, qparam=None):
		if qtype is None or qtype in (diceng.QRY_EXACT, diceng.QRY_BEGIN):
			pass

def register():
	print 'Register Stardict'
	diceng.registerengine('stardict', StardictEngine)

# vim:ts=4:sw=4:noet:tw=80
