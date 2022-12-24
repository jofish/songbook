
def titletext(discardmode=False,lulumode=False):
	titletext=("""<html><?xml version="1.0" ?>
			<?xml-stylesheet type="text/css" href="songbook.css"?>
			<link rel="stylesheet" type="text/css" href="songbook.css" />
			\n<body>\n""") 

	if discardmode:
		titletext+="""<div class="titlepage">
		<br><br><br><br><br><br><br>songbook: guitar, uke & piano music book
		<br>the discard pile<br>
		<br>version 7.0<br> guitar &amp; uke &amp; piano chords in back <br>
		<br><br>22 July 2022<br><br>http://github.com/jofish/songbook<br><br><br><br><br>
		<br>&nbsp;<br>&nbsp;<br>&nbsp;<br>&nbsp;<br>
		<br><br><br><br><br>this page left blank for printing; delete before sending to lulu</div>"""

	elif lulumode:
		titletext+=""

	else: #normal mode
		titletext+="""
			<div class="titlepage">
			<br><br><br><br><br><br><br>songbook: guitar, uke & piano music book<br><br>
			<br>version 8.0<br> guitar &amp; uke chords
			<br>
			<br>full chord charts in back
			<br>2022-11-22<br><br>http://github.com/jofish/songbook<br><br><br><br><br><br><br><br></div>
			<div class="titlepage"><br><br>this page left blank for printing<br>delete before sending to lulu<br>or use lulu mode</div>"""
	
	return(titletext)

