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

if __name__ == '__main__':
	# test
	import pdb
	#pdb.set_trace()
	print `_get_win_app_data_dir()`
	print `_get_win_cache_dir()`
	print `_wd_cfg_cache_dir('webdic')`
# vim:ts=4:sw=4:noet:tw=80
