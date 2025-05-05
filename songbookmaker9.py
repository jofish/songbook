import xml.dom.minidom, string, re, os, codecs, sys, math, subprocess, pprint, webbrowser

usecolumns = False
usechords = True
songpagelength=0
unknownchords = {"guitar":[], "ukulele": [], "banjo": []}
orderbytitle = False

def getText(nodelist):	#this just deals with XML
	rc = ""
	for node in nodelist:
		try:
			if node.nodeType == node.TEXT_NODE: rc = rc + node.data
		except:
			print("nodetype: ", str(node.nodeType), "node: ",str(node.data))
	return rc
		
def insertchords(mysong): 
	chords = songs[mysong][3]
	if len(chords)==0: print("NO CHORDS: ",mysong)
	chorddirectory= "diagrams/"
	chordcounter=0
	#chordtable='<table border=0 style="border-collapse: collapse; z-index:0;"><tr><th width=50%>Guitar</th><th width=50%> Uke </th></tr>\n' #column headings
	
	# for chord in chords.split():#and now the chord table		
	# 	chordtable+='<tr><td colspan="2" style="text-align: center; padding: 0; margin: 0; line-height: 1;">'+chord+"</td></tr><tr>" #first the name
	# 	chord=chord.replace('/','_') #fix the fact we can't have slashes in filenames
	# 	for instrument in ['guitar','ukulele']:			
	# 		if os.path.isfile(chorddirectory+instrument+"/"+chord+".png"): #first check to see if it exists. 
	# 			chordtable+='<td width=40 height=30><div style="margin-top: -15x;"><img src="'+chorddirectory+instrument+"/"+chord.replace("#","%23")+'.png"></div></td>\n'
	# 		elif os.path.isfile(chorddirectory+instrument+"-truechord"+"/"+chord+".png"): #see if we've generated with truechord automatically, which is less reliable
	# 			chordtable+='<td width=40 height=30><div style="margin-top: -15px;"><img src="'+chorddirectory+instrument+"-truechord"+"/"+chord.replace("#","%23")+'.png"></div></td>\n'
	# 		#and here is where we would put the inline generating code in to make truechord automatically generate these on the fly
	# 		#ALSO we should have some code to say "was that a # and there's a b version, just use that, or vice versa. but it might be easier to just dupe some files.
	# 		else: 
	# 			chordtable+='<td width=40 height=40><img src="'+chorddirectory+instrument+"/"+'empty.png"></td>\n' #fill it in yourself!
	# 			unknownchords[instrument]+=[chord.replace('_','/')] #let's put it back for now
	# 	chordtable+='</tr>'
	# 	chordcounter+=1
	# chordtable+="</table>" #end of table-within-a-table
	# tocfile.write('<div class="chords" style="z-index:0">'+chordtable+'</div>\n')

	chordtable='<table border=0 style="z-index:0"><tr><th width=10%> </th><th width=45%>Guitar</th><th width=45%> Uke </th></tr>\n' #column headings
	for chord in chords.split():#and now the chord table		
		chordtable+='<tr><td style="text-align: right">'+chord+"</td>" #first the name
		chord=chord.replace('/','_') #fix the fact we can't have slashes in filenames
		for instrument in ['guitar','ukulele']:			
			if os.path.isfile(chorddirectory+instrument+"/"+chord+".png"): #first check to see if it exists. 
				chordtable+='<td width=40 height=30><img src="'+chorddirectory+instrument+"/"+chord.replace("#","%23")+'.png"></td>\n'
			elif os.path.isfile(chorddirectory+instrument+"-truechord"+"/"+chord+".png"): #see if we've generated with truechord automatically, which is less reliable
				chordtable+='<td width=40 height=30><img src="'+chorddirectory+instrument+"-truechord"+"/"+chord.replace("#","%23")+'.png"></td>\n'
			#and here is where we would put the inline generating code in to make truechord automatically generate these on the fly
			#ALSO we should have some code to say "was that a # and there's a b version, just use that, or vice versa. but it might be easier to just dupe some files.
			else: 
				chordtable+='<td width=40 height=30><img src="'+chorddirectory+instrument+"/"+'empty.png"></td>\n' #fill it in yourself!
				unknownchords[instrument]+=[chord.replace('_','/')] #let's put it back for now
		chordtable+='</tr>'
		chordcounter+=1
	chordtable+="</table>" #end of table-within-a-table
	tocfile.write('<div class="chords" style="z-index:0">'+chordtable+'</div>\n')

	#if chordcounter>15: print(chordcounter,"chords in ",songs[song][1])#keep track of ones with too many chords to fit on a page

	#print(mysong, songs[mysong][1], len(songs[mysong][3].split()),chordcounter, len(songs[mysong][3].split())-chordcounter)

#	we may go back to inline generating at some point.		
#			if not os.path.isfile(chorddirectory+instrument+"/"+chord+".png"): #if it doesn't exist generate it
#				print "failed on",instrument,chord
#				printlist = ["/usr/bin/python3","ThatChord/thatchord.py",chord,"--instrument",instrument,"--directory",chorddirectory+instrument]
#				subprocess.call(printlist)

#def handlecolumns(): #haven't tested now I moved this out of the main loop
#			maxwidth=0
#			for line in songs[song][2].split('\n'): maxwidth=max(maxwidth, len(line.strip()))
#		 #print songs[song][1], maxwidth
#		 #assumes that the max width is 80. The reality is it's something a bit closer to 96
#		 #if maxwidth<40: print maxwidth, songs[song][1]+" is a candidate for columns"

#sorting algorithm
#if not tagged as a band name, then
	# if it's got a slash or a comma, cut at the punctuation and sort by the last word before it. 
	# if it's two or more words, then sort under the last word.

		
def readInSongs(myfeed):
	try:
		for song in myfeed.getElementsByTagName("song"):
			artist = getText(song.getElementsByTagName("artist")[0].childNodes).strip()
			artist = re.sub("&","&amp;",artist) #fix ampersands
			songtitle = getText(song.getElementsByTagName("songtitle")[0].childNodes).strip()
			songtitle = re.sub("&","&amp;",songtitle) #fix ampersand
			if andy:
				songcandidate = artist + " - " + songtitle
				if songcandidate not in andysongs: continue
				else: 
					print("adding :",artist + " - " + songtitle)
					andysongs.remove(songcandidate) #remove it from the list
			
			lyrics = getText(song.getElementsByTagName("lyrics")[0].childNodes)
			lyrics = re.sub("&","&amp;",lyrics).rstrip().strip("\n") #swap out ampersands and strip trailing whitespace and initial carriage returns
			songlength = lyrics.count("\n")
			if ((songlength+2) % 61 < 15) & (songlength % 61 >0): print("might be shortenable to 59 lines plus n*61 lines to save pages:", songlength+2, "lines", songtitle) 
			if usechords: chords = getText(song.getElementsByTagName("chords")[0].childNodes)
			if "Alfred, the Alligator" in songtitle: lyrics+='<p><img src="alfred-music.jpg" />' #this is filthy
			if "When The Saints Go Marching In" in songtitle: lyrics+='<p><img src="saints.jpg" />' #this is still filthy

			if not orderbytitle: indexkey = (artist+songtitle).lower()
			else:indexkey = (songtitle+artist)
			titlekey = (songtitle+artist).lower()
			songpagelength = 1 + (songlength - 59 + 60) // 61 #there are 59 lines on the first page and 61 on all subsequent
			if usechords: songs[indexkey]=[artist,songtitle,lyrics,chords,songpagelength]
			else:songs[indexkey]=[artist,songtitle,lyrics,songpagelength]
			songsbytitle[titlekey]=indexkey
	except:
		print("failure on reading song:", songtitle)

if len(sys.argv)<2: sys.exit("usage: python songbookmaker.py root-of-xml-file.xml\nwill output root-of-xmlfile.html and root-of-xmlfile.pdf and root-of-xmlfile.pdf.old")

lulu, andy = False, False
if len(sys.argv)>2:
	if "lulu" in sys.argv[2]: 
		lulu=True
		print("running in lulu mode")
	if "andy" in sys.argv[2]:
		andy=True
		orderbytitle=True
		print("running in andy mode")

xmlfile = sys.argv[1]
htmlfile = xmlfile.replace("xml","html")
pdffile = xmlfile.replace("xml","pdf")
oldfile = xmlfile.replace("xml","old")
if andy:
	htmlfile = htmlfile.replace(".html","-andy.html")
	pdffile = pdffile.replace(".pdf","-andy.pdf")
	oldfile = oldfile.replace(".old","-andy.old")

print(xmlfile, htmlfile, pdffile, oldfile)



if andy:
	andysongs = []
	with open('andy-songbook.txt', 'r') as file: andysongs = [line.strip().replace("&","&amp;") for line in file]

songs = {}
songsbytitle = {}
#readInSongs(xml.dom.minidom.parse(xmlfile))
readInSongs(xml.dom.minidom.parse(xmlfile))
print(len(songs), "songs read in")

discardtext="""<div class="titlepage">
	<br><br><br><br><br><br><br>jofish's guitar, uke & piano music book
		<br>the discard pile<br>

			<br>alphabetical by artist first name
		<br>table of contents<br>by title and artist in front<br>
	<br>version 9.1<br> guitar &amp; uke &amp; piano chords in back <br>
	<br><br>22 September 2024<br><br>http://jofish.com/discards<br><br><br><br><br>
	<br>&nbsp;<br>&nbsp;<br>&nbsp;<br>&nbsp;<br>
	<br><br><br><br><br>this page left blank for printing; delete before sending to lulu</div>"""

toc = []
#tocfile = codecs.open(htmlfile,'w','utf-8')
tocfile = open(htmlfile, 'w', encoding='utf-8')

tocfile.write("""<html><meta charset="UTF-8"><?xml version="1.0" encoding="utf-8"?>
		<?xml-stylesheet type="text/css" href="jofishprint.css"?>
		<link rel="stylesheet" type="text/css" href="jofishprint.css" />

		\n<body>\n""") 

if not lulu: #for lulu publishing, we don't want to generate the cover or the inside cover
	if "discard" in xmlfile: 
		tocfile.write(discardtext)
	else: 
		tocfile.write("""
		<div class="titlepage">
		<br><br><br><br><br>jofish's guitar, uke & piano music book
		<br>300 100% guaranteed bangers<br>
		<br>alphabetical by artist first name
		<br>table of contents<br>by title and artist in front<br>
		<br>guitar, uke, piano and banjo<br>chord charts in back
		<br>version 9.1<br>2025-02-22<br><br>shorter and cleaner than ever!<br><br>pdf: http://jofish.com/songbook<br><br><br><br><br><br></div>
		<div class="titlepage"><br><br>this page left blank for printing<br>delete before sending to lulu</div>""")

def generateToc():
	tocfile.write("""<div class="titlepage">
	<h1>songlist by artist</h1></div>""") 
	tocfile.write('<ul class="toc">')
	for song in sorted(songs.keys()):
		try: tocfile.write('<li class="tocline1"><a href="#'+song+'">'+songs[song][0]+' - '+songs[song][1]+"</a>\n")
		except: print("ERROR TOC:",song)
	tocfile.write("</ul>\n")

	#let's list by title too
	if "discard" in xmlfile: tocfile.write("""<div class="titlepage"><h1>songlist by title - in the discard pile</h1></div>""")
	else: tocfile.write("""<div class="titlepage"><h1>songlist by title</h1></div>""") 

	tocfile.write('<ul class="toc">')
	for song in sorted(songsbytitle.keys()):
		thekey = songsbytitle[song]
		tocfile.write('<li class="tocline1"><a href="#'+thekey+'">'+songs[thekey][1]+' - '+songs[thekey][0]+"</a>\n")
	tocfile.write("</ul>\n")

if not andy: generateToc()

#ok now let's do the songs

currentlyodd=True #we always start on an odd page
holdlist=[] #we'll use this to put 2+ page songs into if they would start on an odd page
shouldbeonpage = 13 #starting page

def writesong(mysong):
	global currentlyodd, shouldbeonpage
	try:#for debugging page testing:
		#if ((songpagelength>1) or (songs[mysong][2].count("\n")>57 )): 
		#	print("about to write ",mysong, "  currentlyodd:", currentlyodd, "pagelength: ",songpagelength, "  on page:",shouldbeonpage, "  page length: ",str(songs[mysong][2].count("\n")))	   
		tocfile.write('<div class="song">\n')
		if not orderbytitle:
			tocfile.write('<h1><span class="artist">'+songs[mysong][0]+'</span> - ')
			tocfile.write('<span class="songtitle">'+songs[mysong][1]+'</span></h1>\n')
		else:
			tocfile.write('<h1><span class="songtitle">'+songs[mysong][1]+'</span> - ')
			tocfile.write('<span class="artist">'+songs[mysong][0]+'</span></h1>\n')

		tocfile.write('<a name="'+mysong+'" id="'+mysong+'" />\n')
		#tocfile.write('<table border=0 width=100%><tr><td width=85%>') #so for the chords, let's make a table with two columns, and put the chords on the right
		#if usecolumns: handlecolumns()
		#tocfile.write('<div class="lyrics" style="position:absolute;top:20;left:0;z-index:0;">'+songs[mysong][2]+'</div>\n')
		#shit absolutely positioned blocks cannot be split across multiple pages,  https://www.princexml.com/forum/topic/4566/problem-with-page-break
		tocfile.write('<div class="chords" style="position:absolute;top:0;right:0;z-index:1;"')
		if usechords: insertchords(mysong)
		tocfile.write("</div>\n")#chords				
		tocfile.write('<div class="lyrics" style="left:0;z-index:0;">'+songs[mysong][2]+'</div>\n')	
		#tocfile.write('</td></table>')
		if songpagelength % 2 == 1: currentlyodd = not(currentlyodd) 
		shouldbeonpage+=songpagelength
		
	except UnicodeEncodeError as e: #this should no longer ever run!!!!
		print("ERROR in song cos of unicode characters (this song will not be included)",song)
		print(e.object[e.start:e.end])
		print("Context before the problematic string:")
		print(e.object[max(0, e.start - 50):e.start])
		print("Context after the problematic string:")
		print(e.object[e.end:min(len(e.object), e.end + 80)])

for song in sorted(songs.keys()): 
	songpagelength = songs[song][4]
	
	if songpagelength>1 and currentlyodd: #if it's a long song and we're on an odd page
		holdlist.append(song) #add it to the hold stack
		continue
	writesong(song)	
		
	while ((not currentlyodd) and (len(holdlist)>0)): 
		popsong=holdlist.pop(0)
		songpagelength = songs[popsong][4]
		writesong(popsong)

if len(holdlist)>0: writesong(holdlist.pop(0)) #just to check nothing left over
tocfile.write('<div class="song">\n')
tocfile.write('<img src="guitar-chords-chord-chart-enlarged-300dpi.jpg">')
tocfile.write('</div>\n')		
tocfile.write('<div class="song">\n')
tocfile.write('<img src="ukechords-larger.jpg"')
tocfile.write('</div>\n')  
tocfile.write('<div class="song">\n')
tocfile.write('<img src="piano_chords.jpg"')
tocfile.write('</div>\n')  
tocfile.write('<div class="song">\n')
tocfile.write('<img src="banjochart-larger.jpg"')
tocfile.write('</div>\n')
#tocfile.write('<div class="song" style="column-count: 2; column-gap: 20px; overflow-wrap: break-word;word-wrap: break-word;">>\n')
#tocfile.write('<h1>Changes</h1>'+open('changes.txt', 'r').read().replace("/n","<p>"))
#tocfile.write('</div>\n')

if andy: generateToc()
tocfile.write('</body></html>\n')  
tocfile.close()


path=str(os.getcwd()+"/")
if os.access(path+oldfile, os.F_OK): os.remove(path+oldfile)
if os.access(path+pdffile, os.F_OK): os.rename(path+pdffile,path+oldfile)

if len(unknownchords)>0: print("unknown chords: ",str(unknownchords))

if andy: print("remaining: ",andysongs)
	
myargs = "/usr/local/lib/prince/bin/prince "+path+htmlfile+" -o "+path+pdffile
print("now running prince: "+myargs)
os.execl("/usr/local/lib/prince/bin/prince", "/usr/local/lib/prince/bin/prince",path+htmlfile,"-o",path+pdffile)
#subprocess.run(["/usr/local/lib/prince/bin/prince", "/usr/local/lib/prince/bin/prince",path+htmlfile,"-o",path+pdffile], check=False)
#os.system(path+pdffile)
