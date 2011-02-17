convert -size 320x85 xc:transparent -font Arial-Bold-Italic -pointsize 72 -draw "text 25,70 'WebDic'" -channel RGBA -gaussian 0x6 -fill royalblue -stroke lightblue -draw "text 20,65 'WebDic'" -depth 8 logo.png
pngnq -n 256 logo.png
move /y logo-nq8.png logo.png
pngout logo.png
