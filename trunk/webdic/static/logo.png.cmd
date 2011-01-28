convert -size 320x85 xc:transparent -font Arial-Bold-Italic -pointsize 72 -draw "text 25,70 'WebDic'" -channel RGBA -gaussian 0x6 -fill royalblue -stroke lightblue -draw "text 20,65 'WebDic'" -depth 8 logo.png
pngout logo.png
