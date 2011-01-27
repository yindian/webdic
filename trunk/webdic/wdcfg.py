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
import sys, os
import logging

def _get_win_shell_folder(name):
	import _winreg
	key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
			r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
			)
	try:
		return _winreg.QueryValueEx(key, name)[0]
	except:
		raise
	finally:
		_winreg.CloseKey(key)

def _get_win_app_data_dir():
	try:
		return _get_win_shell_folder('AppData')
	except Exception, e:
		try:
			return os.environ['APPDATA']
		except:
			raise e

def _get_win_cache_dir():
	try:
		return _get_win_shell_folder('Cache')
	except Exception, e:
		return os.environ.get('TEMP', None) or os.environ['TMP']

def _wd_cfg_cache_dir(name):
	try:
		path = _get_win_app_data_dir()
		cfgdir = os.path.join(path, name)
		path = _get_win_cache_dir()
		cachedir = os.path.join(path, name)
	except:
		logging.debug('Failed getting Windows app/cache directories')
		path = os.path.expanduser('~')
		cfgdir = os.path.join(path, '.'+name)
		cachedir = os.path.join(cfgdir, 'cache')
	while True:
		for path in (cfgdir, cachedir):
			if not os.path.exists(path):
				os.makedirs(path)
		try:
			for path in (cfgdir, cachedir):
				if not os.path.isdir(path):
					raise IOError('%s is not directory' % (path,))
		except:
			if not cfgdir.startswith(sys.path[0]):
				cfgdir = os.path.join(sys.path[0], '.'+name)
				cachedir = os.path.join(cfgdir, 'cache')
			else:
				break
		else:
			break
	logging.debug('Config dir: %s, cache dir: %s' % (cfgdir, cachedir))
	return cfgdir, cachedir

CFGDIR, CACHEDIR = _wd_cfg_cache_dir('webdic')
CFGFILE = os.path.join(CFGDIR, 'webdic.ini')

import ConfigParser
try:
	import cStringIO as StringIO
except:
	import StringIO

_cfg = ConfigParser.RawConfigParser()

def _load_default_config():
	_cfg.readfp(StringIO.StringIO('''\
[preference]
lang=en
[dictlist]
[dicttags]
'''))

def load():
	'''Load preference and dictionary list from configuration file (CFGFILE).
	If the config file is missing, the dictionary list is left empty, and
	the language preference defaults to English.'''
	_load_default_config()
	_cfg.read(CFGFILE)
	_update_dict_list()

def store():
	'''Store preference and dictionary list to configuration file (CFGFILE).'''
	f = open(CFGFILE, 'w')
	_cfg.write(f)
	f.close()

def getlang():
	'Get the language preference'
	return _cfg.get('preference', 'lang')

def setlang(lang):
	'Set the language preference'
	return _cfg.set('preference', 'lang', lang)

_dictlist = []
_dictset  = set()
_dicttags = {}
_tagdicts = {}

def _update_dict_list():
	'Update _dictlist, _dictset, _dicttags and _tagdicts from config'
	global _dictlist, _dictset
	result = dict(_cfg.items('dictlist'))
	_dictset = set(result.iterkeys())

	_dictlist = []
	try:
		order = _cfg.get('preference', 'dictorder')
	except ConfigParser.NoOptionError:
		order = ''
	for s in order.split('\x01'):
		if result.has_key(s):
			_dictlist.append((s, result[s]))
			del result[s]
	_dictlist.extend(result.items())

	global _dicttags, _tagdicts
	_dicttags = {}
	_tagdicts = {}
	for name, tags in _cfg.items('dicttags'):
		if name not in _dictset:
			continue
		_dicttags[name] = set(tags.split(','))
		for t in _dicttags[name]:
			if not _tagdicts.has_key(t):
				_tagdicts[t] = set()
			_tagdicts[t].add(name)

def dictlist():
	'Get the list of dictionaries, each item is a tuple of basename & dict path'
	return _dictlist[:]

def adddict(path, basename):
	'''Add one dictionary with given path and reference basename to the
	dictionary list. Return the actual basename of this dictionary. The
	basename will be used to identify the dictionary and used in its cache
	file name, if any.'''
	for n, p in _dictlist:
		if p == path:
			basename = n
	while True:
		try:
			s = _cfg.get('dictlist', basename)
		except ConfigParser.NoOptionError:
			s = None
		if s is None or s == path:
			break
		basename += '_'
	_cfg.set('dictlist', basename, path)
	_update_dict_list()
	return basename

def deldict(basename):
	'Remove specified dictionary from the dictionary list'
	if _cfg.optionxform(basename) not in _dictset:
		raise KeyError('%s not found in dictionary list.' % (basename,))
	_cfg.remove_option('dictlist', basename)
	_cfg.remove_option('dicttags', basename)
	_update_dict_list()
	reorderdict(_dictlist)

def reorderdict(dictlist):
	'''Update the dictionary order according to the given dictionary list,
	which shall contain the same set of (name, path) pairs as the dictionary
	list returned by dictlist().'''
	global _dictlist
	if dictlist is not _dictlist:
		assert dict(_dictlist) == dict(dictlist)
	order = [name for name, path in dictlist]
	order = '\x01'.join(order)
	_cfg.set('preference', 'dictorder', order)
	if _dictlist == dictlist:
		return
	del _dictlist
	_dictlist = dictlist[:]

def tagdict(basename, tag):
	'Add a tag to given dictionary.'
	basename = _cfg.optionxform(basename)
	if basename not in _dictset:
		raise KeyError('%s not found in dictionary list.' % (basename,))
	if not tag or tag.find(',') >= 0:
		raise ValueError('Invalid tag %s for %s' % (tag, basename))
	if not _dicttags.has_key(basename):
		_dicttags[basename] = set()
	_dicttags[basename].add(tag)
	if not _tagdicts.has_key(tag):
		_tagdicts[tag] = set()
	_tagdicts[tag].add(basename)
	_cfg.set('dicttags', basename, ','.join(_dicttags[basename]))

def untagdict(basename, tag):
	'Remove a tag from given dictionary.'
	basename = _cfg.optionxform(basename)
	if basename not in _dictset:
		raise KeyError('%s not found in dictionary list.' % (basename,))
	_dicttags[basename].remove(tag)
	_tagdicts[tag].remove(basename)
	if _dicttags[basename]:
		_cfg.set('dicttags', basename, ','.join(_dicttags[basename]))
	else:
		_cfg.remove_option('dicttags', basename)
	if not _tagdicts[tag]:
		del _tagdicts[tag]

def taglist():
	'Return a list of available tags in undefined order.'
	return _tagdicts.keys()

def taggeddicts(tag):
	'''Return a list of basenames of dictionaries with given tag in undefined
	order.'''
	return list(_tagdicts.get(tag, []))

def dicttags(basename):
	'Return a list of tags of given dictionary in undefined order'
	basename = _cfg.optionxform(basename)
	if basename not in _dictset:
		raise KeyError('%s not found in dictionary list.' % (basename,))
	return list(_dicttags.get(basename, []))

if __name__ == '__main__':
	# test
	import pprint
	import pdb
	import traceback
	#pdb.set_trace()
	print `_get_win_app_data_dir()`
	print `_get_win_cache_dir()`
	print `_wd_cfg_cache_dir('webdic')`
	load()
	buf = StringIO.StringIO()
	_cfg.write(buf)
	print '===\n' + buf.getvalue() + '===='
	del buf
	print adddict(r'Y:\temp\temp\newoxford\mob\out\En-Ch-newoxford.ifo',
			'En-Ch-newoxford')
	print adddict(r'Y:\temp\temp\newoxford\out\En-Ch-newoxford.ifo',
			'En-Ch-newoxford')
	print 'Lang:', getlang()
	print 'Dictionaries:'
	dl = dictlist()
	pprint.pprint(dl)
	dl.reverse()
	reorderdict(dl)

	tagdict('En-Ch-newoxford', '1')
	tagdict('En-Ch-newoxford', 'En-Ch')
	tagdict('En-Ch-newoxford_', 'En-Ch')
	print taglist()
	for t in taglist():
		print t, taggeddicts(t)
	for n, p in dictlist():
		print n, dicttags(n)
	a,b,c,d = _dictlist[:], _dictset.copy(), _dicttags.copy(), _tagdicts.copy()
	store()
	load()
	assert a == _dictlist
	assert b == _dictset 
	assert c == _dicttags
	assert d == _tagdicts

	deldict('En-Ch-newoxford')
	untagdict('En-Ch-newoxford_', 'En-Ch')
	buf = StringIO.StringIO()
	_cfg.write(buf)
	print '===\n' + buf.getvalue() + '===='
	pprint.pprint(dictlist())
	try:
		untagdict('En-Ch-newoxford_', 'En-Ch')
	except:
		traceback.print_exc()
	try:
		tagdict('En-Ch-newoxford_', '1,')
	except:
		traceback.print_exc()
	try:
		tagdict('En-Ch-newoxford', '1')
	except:
		traceback.print_exc()
	try:
		untagdict('En-Ch-newoxford', 'En-Ch')
	except:
		traceback.print_exc()
	print taglist()
	for t in taglist():
		print t, taggeddicts(t)
	for n, p in dictlist():
		print n, dicttags(n)
	print 'Seems to work right?'
# vim:ts=4:sw=4:noet:tw=80
