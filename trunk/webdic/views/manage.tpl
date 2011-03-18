<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
<title>Dictionary Management - WebDic</title>
</head>
<body>
<center>
%if promptmsg:
{{promptmsg}}
<hr>
%end
<form name="f">
%if dictlist:
<select name="focus" size=8>
%for s, t in dictlist:
%if s == focusdict:
 <option selected value="{{s}}">{{t}}</option>
%else:
 <option value="{{s}}">{{t}}</option>
%end
%end
</select>
<br>
%end
<input name="add" value="Add" type="submit">
<input name="up" value="Up" type="submit">
<input name="down" value="Down" type="submit">
<input name="del" value="Del" type="submit">
<br>
<input name="path" size="55" title="File path">
<script type="text/javascript">
document.write('<input type="file" id="hiddenfile" size=1 style="border:none; color:white;" onchange="sync()">');
function sync() {
// hack for Opera. See http://united-coders.com/matthias-reuter/circumvention-of-operas-upload-field-path-protection
var uploadField = document.getElementById("hiddenfile");
var clone = uploadField.cloneNode(true);
try {
clone.type = "text";
}catch(err){ // not Opera
clone=uploadField; // this only works for IE
}
document.f.path.value = clone.value;
}
</script>
<br>
</form>
<a href="/">Back</a>
</center>
</body>
</html>
