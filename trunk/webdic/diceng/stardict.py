#!/usr/bin/env pytho
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
import types
try:
	import cStringIO as StringIO
except:
	import StringIO
import logging, traceback
import pdb
import time

def parseifo(path):
	f = open(path, 'r')
	try:
		if f.readline().rstrip('\n') != "StarDict's dict ifo file":
			raise diceng.ParseError('Invalid ifo file header')
		d = dict([l.rstrip('\n').decode('utf-8').split('=', 1) for l in f])
		if d.get('version') != '2.4.2':
			raise diceng.ParseError('Invalid ifo version')
		return (d['bookname'],
				d.get('sametypesequence'),
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

def htmlquote(s):
	return s.replace('&', '&amp;').replace('"', '&quot;').replace('<',
			'&lt;').replace('>', '&gt;')

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

# Restriction of collate function:
# 1. collate('\n'.join(array)).splitlines() == map(collate, array)
# 2. collate(collate(str)) == collate(str)
# 3. Question mark and asterisk shall not be stripped
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
		self._resroot = os.path.join(os.path.split(self._path)[0], 'res')
		try:
			self._dicf = dictzip.DictzipFile(root + '.dict.dz', 'rb')
		except IOError:
			self._dicf = open(root + '.dict', 'rb')
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
				self._colwords = None
			else:
				buf = self._idxf.read()
				assert self._idxf.tell() == idxsize
				pos = 0
				ar = []
				cr = [0]
				while pos < len(buf):
					p = buf.find('\0', pos)
					ar.append(buf[pos:p])
					pos = p + 9
					cr.append(pos)
				assert pos == idxsize
				br = collate('\n'.join(ar).decode('utf-8')).splitlines()
				assert len(ar) == len(br)
				dr = range(len(ar))
				dr.sort(key=br.__getitem__)
				self._indices = map(cr.__getitem__, dr)
				br.sort()
				self._colwords = br
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
				self._indices = struct.unpack('<%dL' % (totalcnt,),
						f.read(4*totalcnt))
				self._refindices = struct.unpack('<%dL' % (totalcnt,),
						f.read(4*totalcnt))
				f.close()
				self._colwords = None
			else:
				buf = self._idxf.read()
				assert self._idxf.tell() == idxsize
				pos = 0
				ar = []
				cr = [0]
				while pos < len(buf):
					p = buf.find('\0', pos)
					ar.append(buf[pos:p])
					pos = p + 9
					cr.append(pos)
				assert pos == idxsize
				del cr[-1]
				buf = self._synf.read()
				cr2 = cr[:]
				pos = 0
				cr.append(0x80000000)
				xx = []
				while pos < len(buf):
					p = buf.find('\0', pos)
					ar.append(buf[pos:p])
					pos = p + 5
					cr.append(pos | 0x80000000)
					xx.append(buf[p+1:pos])
				cr2.extend(map(cr.__getitem__, struct.unpack('!%dL' % (len(xx),), ''.join(xx))))
				assert len(ar) == self._wordcnt + self._syncnt
				assert len(ar) == len(cr) - 1 == len(cr2)
				br = collate('\n'.join(ar).decode('utf-8')).splitlines()
				assert len(ar) == len(br)
				dr = range(len(ar))
				dr.sort(key=br.__getitem__)
				self._indices = map(cr.__getitem__, dr)
				self._refindices = map(cr2.__getitem__, dr)
				br.sort()
				self._colwords = br
				f = open(getcachepath(self._basename, '.spo'), 'wb')
				f.write(struct.pack('<%dL'% (len(ar),),
					*self._indices))
				f.write(struct.pack('<%dL'% (len(ar),),
					*self._refindices))
				f.close()
			assert len(self._indices) == len(self._refindices) == totalcnt
		self._totalcnt = len(self._indices)
		self._info = '\n'.join([self._name,
			'%d words' % (self._wordcnt,) + (self._syncnt and 
				', %d synonyms (%d total)' % (self._syncnt, self._totalcnt)
				or ''),
			d.get('description', '')])
		self._lastqstr = self._lastqtype = self._lastqparam = None
		self._lastqmethod = self._lastqresult = None
		self._lastidxstr = self._lastidxtype = self._lastidxparam = None
		self._lastidxrange = None
		self._lastlocatestr = self._lastlocatepos = None
		# index -> (collated word, word, refword, offset, length)
		self._cache = {}
	def _lazyload(self):
		if self._colwords is None:
			self._load_collated_word()
		print 'lazy load done for', self._basename
	def _load_collated_word(self):
		self._idxf.seek(0)
		buf = self._idxf.read()
		pos = 0
		ar = []
		while pos < len(buf):
			p = buf.find('\0', pos)
			ar.append(buf[pos:p])
			pos = p + 9
		if self._syncnt:
			self._synf.seek(0)
			buf = self._synf.read()
			pos = 0
			while pos < len(buf):
				p = buf.find('\0', pos)
				ar.append(buf[pos:p])
				pos = p + 5
		br = collate('\n'.join(ar).decode('utf-8')).splitlines()
		br.sort()
		self._colwords = br
	def _get_idx(self, idx):
		if self._cache.has_key(idx):
			return self._cache[idx]
		if self._syncnt == 0:
			pos = self._indices[idx]
			self._idxf.seek(pos)
			buf = self._idxf.read(64)
			while buf.find('\0') < 0:
				buf += self._idxf.read(64)
			p = buf.index('\0')
			if len(buf) - p < 9:
				buf += self._idxf.read(8)
			try:
				word = buf[:p].decode('utf-8')
			except:
				logging.error('Error decoding %s for %s' % (`buf[:p]`, self._basename))
				logging.error(traceback.format_exc())
				word = buf[:p].decode('utf-8', 'replace')
			offset, length = struct.unpack('!LL', buf[p+1:p+9])
			result = [collate(word), word, None, offset, length]
		else:
			if self._indices[idx] & 0x80000000:
				pos = self._indices[idx] & 0x7FFFFFFF
				self._synf.seek(pos)
				buf = self._synf.read(64)
				while buf.find('\0') < 0:
					buf += self._synf.read(64)
				try:
					word = buf[:buf.index('\0')].decode('utf-8')
				except:
					p = buf.find('\0')
					logging.error('Error decoding %s for %s' % (`buf[:p]`, self._basename))
					logging.error(traceback.format_exc())
					word = buf[:p].decode('utf-8', 'replace')
				pos = self._refindices[idx]
				self._idxf.seek(pos)
				buf = self._idxf.read(64)
				while buf.find('\0') < 0:
					buf += self._idxf.read(64)
				p = buf.index('\0')
				if len(buf) - p < 9:
					buf += self._idxf.read(8)
				try:
					refword = buf[:p].decode('utf-8')
				except:
					logging.error('Error decoding %s for %s' % (`buf[:p]`, self._basename))
					logging.error(traceback.format_exc())
					refword = buf[:p].decode('utf-8', 'replace')
				offset, length = struct.unpack('!LL', buf[p+1:p+9])
				result = [collate(word), word, refword, offset, length]
			else:
				pos = self._indices[idx]
				self._idxf.seek(pos)
				buf = self._idxf.read(64)
				while buf.find('\0') < 0:
					buf += self._idxf.read(64)
				p = buf.index('\0')
				if len(buf) - p < 9:
					buf += self._idxf.read(8)
				try:
					word = buf[:p].decode('utf-8')
				except:
					logging.error('Error decoding %s for %s' % (`buf[:p]`, self._basename))
					logging.error(traceback.format_exc())
					word = buf[:p].decode('utf-8', 'replace')
				offset, length = struct.unpack('!LL', buf[p+1:p+9])
				result = [collate(word), word, None, offset, length]
		self._cache[idx] = result
		return result
	def _locate(self, word):
		if self._lastlocatestr == word:
			return self._lastlocatepos
		key = collate(word)
		lo = 0
		hi = top = self._totalcnt
		while lo < hi:
			mid = (lo + hi) / 2
			c = cmp(key, self._get_idx(mid)[0])
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
		self._lastlocatestr = word
		self._lastlocatepos = lo
		return lo
	def _get_idx_range(self, qstr, qtype, qparam=None):
		if (self._lastidxstr == qstr and self._lastidxtype == qtype and
				self._lastidxparam == qparam):
			return self._lastidxrange
		idxbeg = idxend = self._locate(qstr)
		key = collate(qstr)
		if qtype == diceng.QRY_EXACT:
			while (idxend < self._totalcnt and
					self._get_idx(idxend)[0] == key):
				idxend += 1
			idxend -= 1
			if qparam is not None:
				if type(qparam) == types.IntType:
					extranum = qparam
				elif type(qparam) == types.DictType and qparam.get('num', 0):
					extranum = qparam['num']
				else:
					extranum = 0
				if extranum:
					idxend = min(idxend + extranum, self._totalcnt-1)
		else:
			lo = idxend + 1
			hi = min(lo + 4, self._totalcnt)
			step = 8
			while (hi < self._totalcnt and
					self._get_idx(hi)[0].startswith(key)):
				lo = hi
				hi += step
				step += step
			if hi > self._totalcnt:
				hi = self._totalcnt
			while lo < hi:
				mid = (lo + hi) / 2
				if self._get_idx(mid)[0].startswith(key):
					lo = mid + 1
				else:
					hi = mid
			if lo == self._totalcnt or (lo < self._totalcnt and
					self._get_idx(lo-1)[0].startswith(key) and
					not self._get_idx(lo)[0].startswith(key)):
				idxend = lo - 1
			elif not self._get_idx(idxend)[0].startswith(key):
				idxend -= 1
			if qparam is not None:
				if type(qparam) == types.IntType:
					notexactnum = qparam
				elif type(qparam) == types.DictType and qparam.get('num', 0):
					notexactnum = qparam['num']
				else:
					notexactnum = 0
				if notexactnum:
					idx = idxbeg
					while (idx <= idxend and
							self._get_idx(idx)[0] == key):
						idx += 1
					idxend = min(idxend, idx + notexactnum - 1)
		self._lastidxstr = qstr
		self._lastidxtype = qtype
		self._lastidxparam = qparam
		self._lastidxrange = idxbeg, idxend+1
		return self._lastidxrange
	def _wild_search(self, qstr, qparam=None):
		result = []
		if self._colwords is None:
			self._load_collated_word()
		assert len(self._colwords) == self._totalcnt
		key = collate(qstr)
		p = key.find('*')
		if p < 0 or 0 <= key.find('?') < p:
			p = key.find('?')
		if p < 0:
			p = len(key)
		prefix = key[:p]
		key = re.escape(key).replace(r'\*', '.*?').replace(r'\?', '.')
		pat = re.compile(key+'$')
		if prefix:
			for i in xrange(self._locate(prefix), self._totalcnt):
				if not self._colwords[i].startswith(prefix):
					break
				if pat.match(self._colwords[i]):
					result.append(i)
		else:
			for i in xrange(self._totalcnt):
				if pat.match(self._colwords[i]):
					result.append(i)
		return result
	def _adjust_qtype(self, qstr, qtype, qparam):
		if qtype is None:
			qtype = diceng.QRY_EXACT
		elif qtype == diceng.QRY_AUTO:
			if qstr.count('*') + qstr.count('?') > 0:
				qtype = diceng.QRY_WILD
			else:
				qtype = diceng.QRY_EXACT
		if qtype == diceng.QRY_WILD:
			if (qstr.count('?') == 0 and qstr.count('*') == 1 and 
					qstr[-1] == '*'):
				qstr = qstr[:-1]
				qtype = diceng.QRY_BEGIN
		return qstr, qtype, qparam
	def _query(self, qstr, qtype=None, qparam=None):
		qstr, qtype, qparam = self._adjust_qtype(qstr, qtype, qparam)
		if (self._lastqmethod == 0 and self._lastqstr == qstr and 
				self._lastqtype == qtype and self._lastqparam == qparam):
			return self._lastqresult
		result = []
		if qtype == diceng.QRY_EXACT or qtype == diceng.QRY_BEGIN:
			idxbeg, idxend = self._get_idx_range(qstr, qtype, qparam)
			for idx in xrange(idxbeg, idxend):
				ar = self._get_idx(idx)
				if ar[2] is None:
					result.append((idx, ar[1]))
				else:
					result.append((idx, '%s => %s' % (ar[1], ar[2])))
		elif qtype == diceng.QRY_WILD:
			for idx in self._wild_search(qstr, qparam):
				ar = self._get_idx(idx)
				if ar[2] is None:
					result.append((idx, ar[1]))
				else:
					result.append((idx, '%s => %s' % (ar[1], ar[2])))
		self._lastqmethod = 0
		self._lastqstr = qstr
		self._lastqtype = qtype
		self._lastqparam = qparam
		self._lastqresult = result
		return result[:]
	def _querynum(self, qstr, qtype=None, qparam=None):
		qstr, qtype, qparam = self._adjust_qtype(qstr, qtype, qparam)
		if (self._lastqmethod == 1 and self._lastqstr == qstr and 
				self._lastqtype == qtype and self._lastqparam == qparam):
			return self._lastqresult
		result = None
		if qtype == diceng.QRY_EXACT or qtype == diceng.QRY_BEGIN:
			idxbeg, idxend = self._get_idx_range(qstr, qtype, qparam)
			result = idxend - idxbeg
		elif qtype == diceng.QRY_WILD:
			result = len(self._wild_search(qstr, qparam))
		self._lastqmethod = 1
		self._lastqstr = qstr
		self._lastqtype = qtype
		self._lastqparam = qparam
		self._lastqresult = result
		return result
	def _render_one_type(self, typeseq, buf):
		result = []
		if typeseq == 't':
			if buf:
				result.append('<div class="stardict_ipa">')
				result.append('<span class="stardict_bracket">[</span>%s<span class="stardict_bracket">]</span>' % (htmlquote(buf),))
				result.append('</div>')
		elif typeseq == 'y':
			if buf:
				result.append('<div class="stardict_pinyin">')
				result.append('<span class="stardict_bracket">[</span>%s<span class="stardict_bracket">]</span>' % (htmlquote(buf),))
				result.append('</div>')
		elif typeseq == 'm':
			result.append(htmlquote(buf).replace('\n', '<br>'))
		elif typeseq == 'h':
			ar = buf.split('<')
			result.append(ar[0])
			for i in xrange(1, len(ar)):
				p = ar[i].find('>')
				if p < 0:
					result.append('&lt;')
					result.append(ar[i])
					continue
				s = ar[i][:p]
				if s.startswith('a') or s.startswith('A'):
					q = s.find('bword://')
					if q > 0:
						c = s[q-1]
						if c == '=':
							s = s[:q] + diceng.makequeryurl(s[q+8:])
						else:
							r = s.find(c, q)
							s = s[:q] + diceng.makequeryurl(s[q+8:r]) + s[r:]
				elif s.startswith('img') or s.startswith('IMG'):
					q = s.find('src=')
					if q < 0:
						q = s.find('SRC=')
					if q > 0:
						q += 4
						c = s[q]
						if c == '"' or c == "'":
							q += 1
							r = s.find(c, q)
						else:
							r = len(s)
						if s[q] == '\x1e' and s[r-1] == '\x1f':
							t = s[q+1:r-1]
						else:
							t = s[q:r]
						t = diceng.makeresurl(self._basename, t) or ''
						s = s[:q] + t + s[r:]
				result.append('<')
				result.append(s)
				result.append('>')
				result.append(ar[i][p+1:])
		elif typeseq == 'x':
			buf = buf.replace('\n', '<br>')
			ar = buf.split('<')
			result.append(ar[0])
			for i in xrange(1, len(ar)):
				p = ar[i].find('>')
				if p < 0:
					result.append('&lt;')
					result.append(ar[i])
					continue
				s = ar[i][:p]
				if s == 'abr':
					result.append('<span class="stardict_abbreviation">')
				elif s == 'blockquote':
					result.append('<span class="stardict_blockquote">')
				elif s == 'c' or s.startswith('c '):
					q = s.find('c=')
					if q > 0:
						result.append('<font color=')
						result.append(s[q+2:])
						result.append('>')
					else:
						result.append('<font color="blue">')
				elif s == '/c':
					result.append('</font>')
				elif s == 'ex':
					result.append('<span class="stardict_example">')
				elif s == 'k':
					result.append('<span class="stardict_keyword">')
				elif s == 'tr':
					result.append('<span class="stardict_bracket">[</span><span class="stardict_transliteration">')
				elif s == '/tr':
					result.append('</span><span class="stardict_bracket">]</span>')
				elif s.startswith('/') and (s == '/abr' or s == '/blockquote' or
						s == '/ex' or s == '/k'):
					result.append('</span>')
				elif s == 'kref':
					result.append('<a href="')
					result.append(diceng.makequeryurl(ar[i][p+1:]))
					result.append('">')
				elif s == '/kref':
					result.append('</a>')
				elif s == 'rref':
					pass # TODO
				elif s == '/rref':
					pass # TODO
				else:
					result.append('<')
					result.append(s)
					result.append('>')
				result.append(ar[i][p+1:])
		elif typeseq == 'g':
			pass # TODO
		else:
			result.append('<div class="stardict_unknown_type">')
			result.append('Unsupported type ' + htmlquote(typeseq))
			result.append('</div>')
		return ''.join(result)
	def _html_render(self, buf):
		result = []
		if not self._sametypeseq:
			pass
		else:
			stseq = self._sametypeseq
			while len(stseq) > 1:
				c = stseq[0]
				try:
					if not c.isupper():
						p = buf.index('\0')
						result.append(self._render_one_type(c, buf[:p]))
						buf = buf[p+1:]
					else:
						l = struct.unpack('!L', buf[:4])[0]
						result.append(self._render_one_type(c, buf[4:4+l]))
						buf = buf[4+l:]
				except:
					logging.error(traceback.format_exc())
				stseq = stseq[1:]
			result.append(self._render_one_type(stseq, buf))
		return ''.join(result)
	def _detail(self, wordid=None, word=None):
		if wordid is not None:
			wordid = int(wordid)
			ar = self._get_idx(wordid)
			# (collated word, word, refword, offset, length)
			self._dicf.seek(ar[3])
			buf = self._dicf.read(ar[4])
			return [(ar[1], self._html_render(buf))]
		else:
			idxbeg, idxend = self._get_idx_range(word, diceng.QRY_EXACT)
			result = []
			for idx in xrange(idxbeg, idxend):
				ar = self._get_idx(idx)
				self._dicf.seek(ar[3])
				buf = self._dicf.read(ar[4])
				result.append((ar[1], self._html_render(buf)))
			return result
	def _resource(self, resid):
		d = {}
		d['root'] = self._resroot
		if type(resid) != types.UnicodeType:
			try:
				resid = resid.decode('utf-8')
			except:
				pass
		d['filename'] = resid
		return d

def register():
	print 'Register Stardict'
	diceng.registerengine('stardict', StardictEngine)

# vim:ts=4:sw=4:noet:tw=80