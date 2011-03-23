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
import dicman
import bottle
import os.path, urllib
import time

def template2(tpl, **kwargs):
	'Wrapped template with translation'
	f, e = os.path.splitext(tpl)
	lang = wdcfg.getlang()
	if lang != 'en':
		cand = ''.join((f, '_', lang, e))
		try:
			result = template(cand, **kwargs)
		except bottle.TemplateError:
			pass
		else:
			return result
	return template(tpl, **kwargs)

_ = lambda s: s

wdcfg.load()
dicman.diceng.setcachedir(wdcfg.CACHEDIR)
dicman.loaddicts()

@route1('/redir')
def redir():
	url = request.GET.get('url')
	msg = request.GET.get('msg')
	if not url:
		abort(400, _('Invalid redirection URL.'))
	return template2('redir.tpl', promptmsg=msg, url=url)

def redirect2(url, msg=None):
	if not msg:
		redirect('/redir?url=%s' % (urllib.quote(url),))
	else:
		redirect('/redir?url=%s&msg=%s' % map(urllib.quote, (url, msg)))

@route1('/save')
def save():
	wdcfg.store()
	redirect('/')

@route1('/reset')
def reset():
	wdcfg.load()
	redirect('/manage')

@route1('/')
@route1('/web')
def index():
    return template2('web.tpl')

@route1('/lookup')
def lookup():
	query = request.GET.get('q')
	if not query:
		abort(400, _('Empty query string.'))
	urlparam = ''
	d = {}
	def detailfilter(basename, qstr, qtype, word, d=d):
		if d.get(basename, 0) < 3:
			d[basename] = d.get(basename, 0) + 1
			return True
		return False
	t = time.clock()
	result = dicman.query(query, detailfilter=detailfilter)
	suggest = dicman.suggest(query)
	t = time.clock() - t
	return template2('lookup.tpl', query=query, result=result,
			urlparam=urlparam, suggest=suggest, querytime=t)

@route1('/manage')
def manage():
	param = {
			'dictlist': None,
			'promptmsg': None,
			'focusdict': None,
			}
	def errmsg(s):
		param['promptmsg'] = s
	if request.GET.has_key('add'):
		path = request.GET.get('path')
		if path.startswith('"') and path.endswith('"'):
			path = path[1:-1]
		if not os.path.exists(path):
			errmsg(_('File "%s" not exists.') % (path,))
		else:
			ar = dicman.adddict(path)
			if ar:
				param['focusdict'] = ar[0]
	elif request.GET.has_key('up') or request.GET.has_key('down'):
		focus = request.GET.get('focus')
		dictlist = dicman.dictlist()
		p = -1
		for i in xrange(len(dictlist)):
			if dictlist[i][0] == focus:
				p = i
				break
		if p >= 0:
			if request.GET.has_key('up'):
				if p > 0:
					dictlist[p-1:p+1] = dictlist[p-1:p+1][::-1]
				else:
					dictlist.append(dictlist.pop(0))
			else:
				if p < len(dictlist) - 1:
					dictlist[p:p+2] = dictlist[p:p+2][::-1]
				else:
					dictlist.insert(0, dictlist.pop())
			dicman.reorderdict(dictlist)
			param['focusdict'] = focus
	elif request.GET.has_key('del'):
		focus = request.GET.get('focus')
		dicman.deldict(focus)
	elif request.GET.has_key('focus'):
		focus = request.GET.get('focus')
		if dicman.hasdict(focus):
			param['focusdict'] = focus
	param['dictlist'] = dicman.dictnamelist()
	if not param['focusdict'] and param['dictlist']:
		param['focusdict'] = param['dictlist'][0][0]
	return template2('manage.tpl', **param)

@route('/images/:name')
@route('/css/:name')
@route('/js/:name')
def static(name):
	return static_file(name, root='./static')

# vim:ts=4:sw=4:noet:tw=80
