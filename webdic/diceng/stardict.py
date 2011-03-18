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
try:
	import cStringIO as StringIO
except:
	import StringIO
import logging, traceback
import pdb

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

def GzipFile(filename, mode="rb", compresslevel=9, fileobj=None):
	f = gzip.GzipFile(filename,
			mode=mode, compresslevel=compresslevel, fileobj=fileobj)
	g = StringIO.StringIO(f.read())
	f.close()
	return g

class CachedFile(file):
	'I thought it would be faster than builtin file, but it proved false.'
	def __init__(self, *a, **k):
		file.__init__(self, *a, **k)
		self._cache1 = self._cache1pos = None
		self._cache2 = self._cache2pos = None
	def read(self, size=-1):
		if size < 0 or size > 0x10000:
			return file.read(self)
		elif size == 0:
			return ''
		w = self.tell()
		blk = w ^ (w & 0xFFFF)
		t = w + size - blk
		if self._cache1pos == blk:
			if t <= len(self._cache1):
				self.seek(w+size)
				return self._cache1[w-blk:t]
			elif len(self._cache1) < 0x10000:
				return file.read(self, size)
			elif self._cache2pos == blk + 0x10000:
				self.seek(w+size)
				return self._cache1[w-blk:] + self._cache2[:t-0x10000]
			else:
				self._cache2pos = blk + 0x10000
				self.seek(self._cache2pos)
				self._cache2 = file.read(self, 0x10000)
				self.seek(w+size)
				return self._cache1[w-blk:] + self._cache2[:t-0x10000]
		elif self._cache2pos == blk:
			if t <= len(self._cache2):
				self.seek(w+size)
				return self._cache2[w-blk:t]
			elif len(self._cache2) < 0x10000:
				return file.read(self, size)
			elif self._cache1pos == blk + 0x10000:
				self.seek(w+size)
				return self._cache2[w-blk:] + self._cache1[:t-0x10000]
			else:
				self._cache1pos = blk + 0x10000
				self.seek(self._cache1pos)
				self._cache1 = file.read(self, 0x10000)
				self.seek(w+size)
				return self._cache2[w-blk:] + self._cache1[:t-0x10000]
		else:
			self._cache1pos = blk
			self.seek(blk)
			self._cache1 = file.read(self, 0x10000)
			if w + size < blk + len(self._cache1):
				self.seek(w+size)
				return self._cache1[w-blk:t]
			else:
				self.seek(w)
				return file.read(self, size)

idxentrypat = re.compile(r'(.*?)\x00.{8}', re.S)
synentrypat = re.compile(r'(.*?)\x00(.{4})', re.S)
collate = string.lower

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
			self._idxf = GzipFile(root + '.idx.gz', 'rb')
		if self._syncnt == 0:
			if hascache(root, self._basename, '.pos', size=4*self._wordcnt):
				f = open(getcachepath(self._basename, '.pos'), 'rb')
				buf = f.read()
				f.close()
				self._indices = struct.unpack('<%dL' % (self._wordcnt,), buf)
			else:
				buf = self._idxf.read()
				assert self._idxf.tell() == idxsize
				indices = [] #(collated word, entry offset)
				pos = 0
				for s in idxentrypat.findall(buf):
					indices.append((collate(s.decode('utf-8')), pos, pos))
					pos += len(s) + 9
				assert pos == idxsize
				indices.sort()
				self._indices = [p for s, p, pp in indices]
				f = open(getcachepath(self._basename, '.pos'), 'wb')
				f.write(struct.pack('<%dL' % (self._wordcnt,), *self._indices))
				f.close()
			assert len(self._indices) == self._wordcnt
			self._synf = None
		else:
			try:
				self._synf = open(root + '.syn', 'rb')
			except IOError:
				self._synf = GzipFile(root + '.syn.gz', 'rb')
			assert idxsize < 0x80000000
			totalcnt = self._wordcnt + self._syncnt
			if hascache(root, self._basename, '.spo', size=8*totalcnt):
				f = open(getcachepath(self._basename, '.spo'), 'rb')
				self._indices = zip(struct.unpack('<%dL' % (totalcnt,),
					f.read(4*totalcnt)), struct.unpack('<%dL' % (totalcnt,),
						f.read()))
				f.close()
			else:
				buf = self._idxf.read()
				assert self._idxf.tell() == idxsize
				indices = [] #(collated word, entry offset)
				pos = 0
				for s in idxentrypat.findall(buf):
					indices.append((collate(s.decode('utf-8')), pos, pos))
					pos += len(s) + 9
				assert pos == idxsize
				buf = self._synf.read()
				pos = 0
				for s, t in synentrypat.findall(buf):
					x = struct.unpack('!L', t)[0]
					indices.append((collate(s.decode('utf-8')), pos| 0x80000000,
						indices[x][1]))
					pos += len(s) + 5
				assert len(indices) ==  self._wordcnt + self._syncnt
				assert pos == self._synf.tell()
				indices.sort()
				ar = [p for s, p, pp in indices]
				br = [pp for s, p, pp in indices]
				self._indices = zip(ar, br)
				f = open(getcachepath(self._basename, '.spo'), 'wb')
				f.write(struct.pack('<%dL'% (len(indices),),
					*ar))
				f.write(struct.pack('<%dL'% (len(indices),),
					*br))
				f.close()
			assert len(self._indices) == totalcnt
		self._totalcnt = len(self._indices)
		self._lastqstr = self._lastqtype = self._lastqparam = None
		self._lastqmethod = self._lastqresult = None
		# index -> (collated word, word, refword, offset, length)
		self._cache = {}
	def _get_idx(self, idx):
		if self._cache.has_key(idx):
			return self._cache[idx]
		result = None
		if self._syncnt == 0:
			pos = self._indices[idx]
			self._idxf.seek(pos)
			buf = self._idxf.read(64)
			while buf.find('\0') < 0:
				buf += self._idxf.read(64)
			p = buf.index('\0')
			if len(buf) - p < 9:
				buf += self._idxf.read(8)
			word = buf[:p]
			offset, length = struct.unpack('!LL', buf[p+1:p+9])
			result = [collate(word), word, None, offset, length]
		else:
			if self._indices[idx][0] & 0x80000000:
				pos = self._indices[idx][0] & 0x7FFFFFFF
				self._synf.seek(pos)
				buf = self._synf.read(64)
				while buf.find('\0') < 0:
					buf += self._synf.read(64)
				word = buf[:buf.index('\0')]
				pos = self._indices[idx][1]
				self._idxf.seek(pos)
				buf = self._idxf.read(64)
				while buf.find('\0') < 0:
					buf += self._idxf.read(64)
				p = buf.index('\0')
				if len(buf) - p < 9:
					buf += self._idxf.read(8)
				refword = buf[:p]
				offset, length = struct.unpack('!LL', buf[p+1:p+9])
				result = [collate(word), word, refword, offset, length]
			else:
				pos = self._indices[idx][1]
				self._idxf.seek(pos)
				buf = self._idxf.read(64)
				while buf.find('\0') < 0:
					buf += self._idxf.read(64)
				p = buf.index('\0')
				if len(buf) - p < 9:
					buf += self._idxf.read(8)
				word = buf[:p]
				offset, length = struct.unpack('!LL', buf[p+1:p+9])
				result = [collate(word), word, None, offset, length]
		self._cache[idx] = result
		return result
	def _locate(self, word):
		key = collate(word)
		lo = 0
		hi = top = self._totalcnt
		while lo < hi:
			mid = (lo + hi) / 2
			ar = self._get_idx(mid)
			c = cmp(key, ar[0])
			if c < 0: # lo word mid hi
				hi = mid
			elif c > 0: # lo mid word hi
				lo = mid + 1
			else:
				lo = mid
				break
		if lo >= top and lo > 0:
			lo = top - 1
		while lo > 0 and self._get_idx(lo-1)[0] == key:
			lo -= 1
		while lo < top-1 and self._get_idx(lo)[0] < key:
			lo += 1
		return lo
	def _get_idx_range(self, qstr, qtype):
		idxbeg = idxend = self._locate(qstr)
		key = collate(qstr)
		if qtype == diceng.QRY_EXACT:
			while (idxend < self._totalcnt and
					self._get_idx(idxend)[0] == key):
				idxend += 1
			idxend -= 1
		else:
			lo = idxend + 1
			hi = min(lo + 4, self._totalcnt)
			step = 8
			while (hi < self._totalcnt and
					self._get_idx(hi)[0].startswith(key)):
				lo = hi
				hi += step
				step *= 2
			if hi > self._totalcnt:
				hi = self._totalcnt
			while lo < hi:
				mid = (lo + hi) / 2
				if self._get_idx(mid)[0].startswith(key):
					lo = mid + 1
				else:
					hi = mid
			if lo == self._totalcnt or (lo < self._totalcnt and
					not self._get_idx(lo)[0].startswith(key)):
				idxend = lo - 1
		return idxbeg, idxend+1
	def _query(self, qstr, qtype=None, qparam=None):
		if qtype is None:
			qtype = diceng.QRY_EXACT
		if (self._lastqmethod == 0 and self._lastqstr == qstr and 
				self._lastqtype == qtype and self._lastqparam == qparam):
			return self._lastqresult
		result = []
		if qtype == diceng.QRY_EXACT or qtype == diceng.QRY_BEGIN:
			for idx in xrange(*self._get_idx_range(qstr, qtype)):
				result.append((idx, self._get_idx(idx)[1]))
		self._lastqmethod = 0
		self._lastqstr = qstr
		self._lastqtype = qtype
		self._lastqparam = qparam
		self._lastqresult = result
		return result[:]
	def _querynum(self, qstr, qtype=None, qparam=None):
		if qtype is None:
			qtype = diceng.QRY_EXACT
		if (self._lastqmethod == 1 and self._lastqstr == qstr and 
				self._lastqtype == qtype and self._lastqparam == qparam):
			return self._lastqresult
		result = None
		if qtype == diceng.QRY_EXACT or qtype == diceng.QRY_BEGIN:
			idxbeg, idxend = self._get_idx_range(qstr, qtype)
			result = idxend - idxbeg
		self._lastqmethod = 1
		self._lastqstr = qstr
		self._lastqtype = qtype
		self._lastqparam = qparam
		self._lastqresult = result
		return result

def register():
	print 'Register Stardict'
	diceng.registerengine('stardict', StardictEngine)

# vim:ts=4:sw=4:noet:tw=80
