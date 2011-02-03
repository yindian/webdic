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
import sys, os.path
sys.path.append(os.path.join(sys.path[0], '3rdlib'))

from bottle import route, run, debug, template, request, response, static_file,\
		abort, redirect

import functools
@functools.wraps(route)
def route1(path=None, method='GET', **kargs):
	def wrapper(callback):
		if path is None or not path.rstrip('/'):
			return route(path, method, **kargs)(callback)
		elif path.endswith('/'):
			return route(path[:-1], method, **kargs)(
					route(path, method, **kargs)(callback))
		else:
			return route(path, method, **kargs)(
					route(path+'/', method, **kargs)(callback))
	return wrapper

# vim:ts=4:sw=4:noet:tw=80