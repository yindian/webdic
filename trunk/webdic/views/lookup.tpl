<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title>{{query}} - WebDic</title>
<style type="text/css">
.dictname {
font-size: large
}
</style>
</head>
<body>
%for basename, dictname, entries, more in result:
<div class="onedict">
<div class="dictname">{{dictname}}</div>
<ul>
%for wordid, word, content in entries:
<li><a href="/detail?dict={{basename}}&id={{wordid}}">{{word.replace('\0', ' => ')}}</a>
%if content is not None:
<div class="detail">
{{content}}
</div>
%end
</li>
%end
</ul>
%if more:
<div class="morequery">
<a href="lookup?dict={{basename}}&qtype={{more[0][0]}}">{{more[0][1]}} more result{{more[0][1] > 1 and '(s)' or ''}}...</a>
</div>
%end
</div>
%end
<div class="querytime">
Query time: {{querytime}} seconds
</div>
<hr>
<form action="/lookup">
<input maxlength="256" size="55" name="q" value="{{query}}" title="Query">
<input value="Lookup" type="submit">
</form>
</body>
</html>
