<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title>{{query}} - WebDic</title>
<link rel="stylesheet" type="text/css" href="/css/webdic.css">
</head>
<body>
%if not result:
<div class="noresult">No results found.</div>
%end
%for basename, dictname, entries in result:
<div class="onedict">
<div class="dictname">{{dictname}}</div>
<ul>
%for wordid, word, content in entries:
<li><a href="/detail?dict={{basename}}&id={{wordid}}">{{word}}</a>
%if content is not None:
<div class="detail">
{{!content}}
</div>
%end
</li>
%end
</ul>
</div>
%end
<div class="querytime">
Query time: {{querytime}} seconds
</div>
%if suggest:
%import urllib
<div class="suggestion">
Related queries:
%for s in suggest:
<a href="/lookup?q={{urllib.quote(s) + urlparam}}">{{s}}</a>
%end
</div>
%end
<hr>
<form action="/lookup">
<input maxlength="256" size="55" name="q" value="{{query}}" title="Query">
<input value="Lookup" type="submit">
<a href="/">Home</a>
</form>
</body>
</html>
