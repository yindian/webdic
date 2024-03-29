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
import threading, Queue
import logging
import traceback
import time

class ParseError(Exception):
	pass

class BaseDictionaryEngine(object):
	'Base class for all dictionary engines that defines basic interfaces.'
	def __init__(self, basename, path, failcb=None):
		self._basename = basename
		self._path = path
		self._lock = threading.Lock()
		self._loaded = False
		self.lock()
		switchcontext(self.load, _exception_callback=failcb)
	def __repr__(self):
		return '<%s (%s)>' % (self._basename, self.__class__.__name__)
	@staticmethod
	def _getbasename(path): pass
	@classmethod
	def getbasename(cls, path):
		'Return a list of available basenames if the given file is in supported'
		' format. Return None or empty list otherwise.'
		return cls._getbasename(path)
	def _load(self): pass
	def load(self):
		'Load dictionary data from disk synchronously.'
		try:
			t = time.clock()
			self._load()
			self.loadtime = time.clock() - t
			self._loaded = True
			switchcontext_lazy(self.lazyload)
		except:
			raise
		finally:
			self.unlock()
	def _lazyload(self): pass
	def lazyload(self):
		'Load extra data lazily from disk. Caution: self not locked.'
		self._lazyload()
	def _query(self, qstr, qtype=None, qparam=None): pass
	def query(self, qstr, qtype=None, qparam=None):
		'Query given pattern and return a list of matching words synchronously.'
		' The query type and param are defined by specific engines. The return '
		'result is a list of (wordid, word) pairs.'
		self.lock()
		try:
			return self._query(qstr, qtype=qtype, qparam=qparam)
		except:
			raise
		finally:
			self.unlock()
	def _querynum(self, qstr, qtype=None, qparam=None): pass
	def querynum(self, qstr, qtype=None, qparam=None):
		'Query given pattern and return the number of matching words '
		'synchronously.'
		self.lock()
		try:
			return self._querynum(qstr, qtype=qtype, qparam=qparam)
		except:
			raise
		finally:
			self.unlock()
	def _detail(self, wordid=None, word=None): pass
	def detail(self, wordid=None, word=None):
		'Return detailed explanation of given word in a query result list. The '
		'return value is a list of (word, detail) pairs. If wordid is given, '
		'the list must have at most one element.'
		self.lock()
		try:
			return self._detail(wordid=wordid, word=word)
		except:
			raise
		finally:
			self.unlock()
	def _resource(self, resid): pass
	def resource(self, resid):
		'Return a dictionary for the resource identified by given '
		'resource id. The possible key items in the dictionary is:\n'
		'1. "file": a file-like object\n'
		'2. "filename": the local file name of the resource\n'
		'3. "root": the root of local file name of the resource\n'
		'4. "mimetype": the mime type\n'
		'5. "buf": the buffer of the resource content\n'
		'See dicman.resource'
		self.lock()
		try:
			return self._resource(resid)
		except:
			raise
		finally:
			self.unlock()
	def lock(self):
		self._lock.acquire()
	def unlock(self):
		self._lock.release()
	def ready(self):
		return self._loaded
	@property
	def basename(self):
		return self._basename
	@property
	def path(self):
		return self._path
	@property
	def name(self):
		try:
			return self._name
		except:
			return 'Put the name / title of your dictionary in self._name'
	@property
	def info(self):
		try:
			return self._info
		except:
			return 'Put the detailed information / description of your dictionary in self._info'

QRY_AUTO  = 0	#Auto match
QRY_EXACT = 1	#Exact match
QRY_BEGIN = 2	#Forward match
QRY_END   = 3	#Backward match
QRY_CROSS = 4	#Partial match
QRY_WILD  = 5	#Wildcard match
QRY_FULL  = 6	#Full-text search
QRY_CPLX  = 7	#Complex match. Query parameter is mandatory.

CMD_QUERY  = 0
CMD_QRYNUM = 1
CMD_DETAIL = 2

class _AgentThread(threading.Thread):
	def __init__(self, taskqueue):
		threading.Thread.__init__(self)
		self._q = taskqueue
	def run(self):
		while True:
			cb, fct, args, kwargs = self._q.get()
			if kwargs.has_key('_exception_callback'):
				ecb = kwargs['_exception_callback']
				del kwargs['_exception_callback']
			else:
				ecb = None
			try:
				result = fct(*args, **kwargs)
				if cb:
					cb(result)
			except:
				logging.error('cb=%s, fct=%s, args=%s, kwargs=%s\n%s' % (
					cb, fct, args, kwargs, traceback.format_exc()))
				if ecb:
					ecb(fct)
			self._q.task_done()

_taskqueue = Queue.Queue()
_t = _AgentThread(_taskqueue)
_t.setDaemon(True)
_t.start()

def switchcontext(fct, *args, **kwargs):
	_taskqueue.put((None, fct, args, kwargs))

def switchcontext_ex(cb, fct, *args, **kwargs):
	_taskqueue.put((cb, fct, args, kwargs))

_lazytaskqueue = Queue.Queue()
_t = _AgentThread(_lazytaskqueue)
_t.setDaemon(True)
_t.start()

def switchcontext_lazy(fct, *args, **kwargs):
	_lazytaskqueue.put((None, fct, args, kwargs))


_queryq = Queue.Queue()
_resultq = Queue.Queue()

class _QueryWorkerThread(threading.Thread):
	def __init__(self, queryq, resultq):
		threading.Thread.__init__(self)
		self._q = queryq
		self._outq = resultq
	def run(self):
		while True:
			ar = self._q.get()
			try:
				seq, engine, cmd = ar[:3]
				if cmd == CMD_QUERY:
					qstr, qargs = ar[3:]
					result = engine.query(qstr, **qargs)
				elif cmd == CMD_QRYNUM:
					qstr, qargs = ar[3:]
					result = engine.querynum(qstr, **qargs)
				elif cmd == CMD_DETAIL:
					word, wordid = ar[3:]
					result = engine.detail(word=word, wordid=wordid)
				else:
					logging.error('Unknown command %s for %s seq %s' % (cmd, 
						engine.name, seq))
			except:
				logging.error(traceback.format_exc())
			else:
				self._outq.put((seq, engine, cmd, result))
			self._q.task_done()

for _i in xrange(5):
	_t = _QueryWorkerThread(_queryq, _resultq)
	_t.setDaemon(True) # setting .daemon doesn't work in Python 2.5
	_t.start()

_seq = 0
def asyncquery(engines, cmd=CMD_QUERY, qstr=None, word=None, wordid=None, **k):
	'Perform async query on given engines sequencially.'
	_resultq.join()
	global _seq
	if _seq > 10000:
		_seq = 0
	for engine in engines:
		if cmd == CMD_DETAIL:
			_queryq.put((_seq, engine, cmd, word or qstr, wordid))
		else:
			_queryq.put((_seq, engine, cmd, qstr, k))
		_seq += 1

def fetchresults():
	'Return a list of results of async queries. Each element is a tuple of '
	'dictionary engine object, query command and query result.'
	_queryq.join()
	ar = []
	while not _resultq.empty():
		seq, engine, cmd, result = _resultq.get()
		ar.append((seq, engine, cmd, result))
		_resultq.task_done()
	ar.sort()
	return [s[1:] for s in ar]

_enginepool = {}

def registerengine(name, engine):
	global _enginepool
	_enginepool[name] = engine

def iterengine():
	return _enginepool.itervalues()

_cachedir = ''

def setcachedir(path):
	global _cachedir
	_cachedir = path

def getcachedir():
	return _cachedir

def makequeryurl(word, **k):
	pass

def makedetailurl(basename, wordid, **k):
	pass

def makeresurl(basename, resid, **k):
	pass

def setmakeurlfunc(query=None, detail=None, resource=None):
	global makequeryurl, makedetailurl, makeresurl
	makequeryurl = query or makequeryurl
	makedetailurl = detail or makedetailurl
	makeresurl = resource or makeresurl

# vim:ts=4:sw=4:noet:tw=80
