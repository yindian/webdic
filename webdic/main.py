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
import sys, os.path, getopt
import logging
import pdb

assert __name__ == '__main__'

opts, args = getopt.getopt(sys.argv[1:], 'p:vh', ['help'])
opts = dict(opts)
if opts.has_key('-h') or opts.has_key('--help'):
	print "Usage: %s [-p port_number] [-v]" % (os.path.basename(sys.argv[0]),)
	sys.exit(0)
port = opts.get('-p', 8080)

if opts.has_key('-v'):
	logging.basicConfig(level=logging.DEBUG)

from wdutil import *
import webdic

if opts.has_key('-v'):
	debug(True)
	run(host='localhost', port=port, reloader=True)
else:
	run(host='localhost', port=port)

# vim:ts=4:sw=4:noet:tw=80
