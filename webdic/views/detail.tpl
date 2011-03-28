<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title>{{word}} - WebDic</title>
<link rel="stylesheet" type="text/css" href="/css/webdic.css">
</head>
<body>
%if detail is None:
<div class="noresult">No detail available.</div>
%else:
{{!detail}}
%end
<hr>
<form action="/lookup">
<input maxlength="256" name="q" value="{{word}}" title="Query">
<input value="Lookup" type="submit">
<a href="/">Home</a>
<a href="{{referer or '/'}}" onclick="history.back()">Back</a>
</form>
</body>
</html>
