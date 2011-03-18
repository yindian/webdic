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
%for engine, cmd, ar in result:
%if ar:
<div class="dictname">{{engine.name}}</div>
<ul>
%for wordid, word in ar:
<li><a href="/detail?dict={{engine.basename}}&id={{wordid}}">{{word.replace('\0', ' => ')}}</a></li>
%end
</ul>
%end
%end
<hr>
<form action="/lookup">
<input maxlength="256" size="55" name="q" value="{{query}}" title="Query">
<input value="Lookup" type="submit">
</form>
</body>
</html>
