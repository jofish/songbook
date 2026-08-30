import xml.dom.minidom, string, re, os, codecs, sys, math, subprocess, pprint, webbrowser, datetime

# --- edit these for your own book ---------------------------------
VERSION   = "10.0"
BOOKTITLE = "a guitar, uke &amp; piano music book\n\t\t<br>300 100% guaranteed bangers"
DISCARDTITLE = "the discard pile"
WEBURL    = ""                          # e.g. "http://example.com/songbook"; blank omits the line
DISCARDURL = ""
PRINCE    = "/opt/homebrew/bin/prince"  # or /usr/local/lib/prince/bin/prince on intel macs & linux
# ------------------------------------------------------------------

usecolumns = False
usechords = True
songpagelength=0
orderbytitle = False
FIRSTPAGE = 61   # lines on a song's first page — the h1 and its blank line take the other two
NEXTPAGE  = 63   # lines on every page after that

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
	chordheight = 50
	chordwidth = round(chordheight * 140 / 150) + 4   # guitar is the widest at 140x150
	rows = ['<tr><th></th>' + ''.join(
		'<th width=%d>%s</th>' % (chordwidth, labels[i]) for i in instruments) + '</tr>']

	for chord in chords.split():
		filename = chord.replace('/', '_')   # can't have slashes in filenames
		row = '<tr><td><i>'+chord+'</i></td>'
		for instrument in instruments:
			src = chorddirectory+instrument+"/"+filename+".png"
			if not os.path.isfile(src):   # fall back to the less reliable auto-generated ones
				src = chorddirectory+instrument+"-truechord/"+filename+".png"
			if not os.path.isfile(src):   # still nothing — leave a blank grid to fill in by hand
				src = chorddirectory+instrument+"/empty.png"
				unknownchords[instrument] += [chord]
			row += '<td><img style="display:block" height='+str(chordheight)+' src="'+src.replace("#", "%23")+'"></td>'
		rows.append(row + '</tr>')

	tocfile.write('<div class="chords" style="z-index:0">'
		'<table border=0 style="width:auto; margin-left:auto; border-collapse:collapse;">'
		+ '\n'.join(rows) + '</table></div>')

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
			overflow = (songlength + 1 - FIRSTPAGE) % NEXTPAGE
			if songlength + 1 > FIRSTPAGE and 0 < overflow < 15:
				print("might save a page by cutting", overflow, "lines:", songlength+1, "lines", songtitle)

			if usechords: chords = getText(song.getElementsByTagName("chords")[0].childNodes)
			if "Alfred, the Alligator" in songtitle: lyrics+='<p><img src="alfred-music.jpg" />' #this is filthy
			if "When The Saints Go Marching In" in songtitle: lyrics+='<p><img src="saints.jpg" />' #this is still filthy

			if not orderbytitle: indexkey = (artist+songtitle).lower().replace(" ","")
			else:indexkey = (songtitle+artist).lower().replace(" ","")
			titlekey = (songtitle+artist).lower().replace(" ","")
			songpagelength = 1 + (songlength - 61 + 63) // 63 #61 lines on the first page, 63 on all subsequent
			if usechords: songs[indexkey]=[artist,songtitle,lyrics,chords,songpagelength]
			else:songs[indexkey]=[artist,songtitle,lyrics,songpagelength]
			songsbytitle[titlekey]=indexkey
	except:
		print("failure on reading song:", songtitle)

if len(sys.argv)<2: sys.exit("usage: python songbookmaker.py root-of-xml-file.xml\nwill output root-of-xmlfile.html and root-of-xmlfile.pdf and root-of-xmlfile.pdf.old")

INSTRUMENTS = {          # command-line word -> diagrams/ subdirectory
	'guitar':   ('guitar',  'Guitar'),
	'uke':      ('ukulele', 'Uke'),
	'ukulele':  ('ukulele', 'Uke'),
	'banjo':    ('banjo',   'Banjo'),
}

lulu, andy = False, False
instruments, labels = [], {}
for arg in sys.argv[2:]:
	for word in re.split(r'[\s,]+', arg.lower()):
		if word == 'lulu':
			lulu = True
			print("running in lulu mode")
		elif word == 'andy':
			andy = True
			orderbytitle = True
			print("running in andy mode")
		elif word in INSTRUMENTS:
			directory, label = INSTRUMENTS[word]
			if directory not in instruments:      # first mention wins the position
				instruments.append(directory)
				labels[directory] = label

if not instruments: instruments = ['guitar', 'ukulele']
labels.setdefault('guitar', 'Guitar'); labels.setdefault('ukulele', 'Uke')
print("chord diagrams:", ", ".join(instruments))

unknownchords = {i: [] for i in instruments}

xmlfile = sys.argv[1]
discards = "discard" in xmlfile

def instrumentphrase():	#"guitar & uke", "guitar, uke & banjo"
	names = [labels[i].lower() for i in instruments]
	if len(names) == 1: return names[0]
	return ", ".join(names[:-1]) + " &amp; " + names[-1]

basename = "songbook-" + VERSION + "-" + "-".join(labels[i].lower() for i in instruments)
if discards: basename += "-discards"
if andy: basename += "-andy"
if lulu: basename += "-lulu"
htmlfile, pdffile, oldfile = basename+".html", basename+".pdf", basename+".old"

print(xmlfile, htmlfile, pdffile, oldfile)



if andy:
	andysongs = []
	with open('andy-songbook.txt', 'r') as file: andysongs = [line.strip().replace("&","&amp;") for line in file]

songs = {}
songsbytitle = {}
#readInSongs(xml.dom.minidom.parse(xmlfile))
readInSongs(xml.dom.minidom.parse(xmlfile))
print(len(songs), "songs read in")

toc = []
#tocfile = codecs.open(htmlfile,'w','utf-8')
tocfile = open(htmlfile, 'w', encoding='utf-8')

tocfile.write("""<html><meta charset="UTF-8"><?xml version="1.0" encoding="utf-8"?>
		<?xml-stylesheet type="text/css" href="songbook.css"?>
		<link rel="stylesheet" type="text/css" href="songbook.css" />

		\n<body>\n""") 
if not lulu: #for lulu publishing, we don't want to generate the cover or the inside cover
	tocfile.write("""
		<div class="titlepage">
		<br>{booktitle}
		<br>{edition} chords edition
		<br>version {version} {today}
		<br>shorter and cleaner than ever!<br>
		{weblink}<br><br><br><br><br></div>
		<div class="titlepage"><br><br>this page left blank for printing<br>delete before sending to lulu</div>""".format(
			booktitle = DISCARDTITLE if discards else BOOKTITLE,
			ordering  = "song title" if orderbytitle else "artist first name",
			edition   = instrumentphrase(),
			version   = VERSION,
			today     = datetime.date.today().isoformat(),
			weblink   = ("<br>pdf: " + (DISCARDURL if discards else WEBURL)) if (DISCARDURL if discards else WEBURL) else ""))



def generateToc():
	tocfile.write("""<div class="titlepage"><h1>songlist by artist</h1><span class="tocnote">(these are links, click to follow)</span></div>""")
	tocfile.write('<ul class="toc">')
	for song in sorted(songs.keys()):
		try: tocfile.write('<li class="tocline1"><a href="#'+song+'">'+songs[song][0]+' - '+songs[song][1]+"</a>\n")
		except: print("ERROR TOC:",song)
	tocfile.write("</ul>\n")

	#let's list by title too
	tocfile.write("""<div class="titlepage"><h1>songlist by title</h1><span class="tocnote">(these are links, click to follow)</span></div>""")
	tocfile.write('<ul class="toc">')
	for song in sorted(songsbytitle.keys()):
		thekey = songsbytitle[song]
		tocfile.write('<li class="tocline1"><a href="#'+thekey+'">'+songs[thekey][1]+' - '+songs[thekey][0]+"</a>\n")
	tocfile.write("</ul>\n")

if not andy: generateToc() #for the shorter version, it's just at the end, because it's only one page.

#ok now let's do the songs

currentlyodd=True #we always start on an odd page
holdlist=[] #we'll use this to put 2+ page songs into if they would start on an odd page
shouldbeonpage = 13 #starting page

def writesong(mysong):
	global currentlyodd, shouldbeonpage
	try:#for debugging page testing:
		#if ((songpagelength>1) or (songs[mysong][2].count("\n")>57 )): 
		#	print("about to write ",mysong, "  currentlyodd:", currentlyodd, "pagelength: ",songpagelength, "  on page:",shouldbeonpage, "  page length: ",str(songs[mysong][2].count("\n")))	   
		tocfile.write('<div class="song">')
		anchor = '<a name="'+mysong+'" id="'+mysong+'"></a>'
		if not orderbytitle:
			tocfile.write('<h1>'+anchor+'<span class="artist">'+songs[mysong][0]+'</span> - ')
			tocfile.write('<span class="songtitle">'+songs[mysong][1]+'</span></h1>')
		else:
			tocfile.write('<h1>'+anchor+'<span class="songtitle">'+songs[mysong][1]+'</span> - ')
			tocfile.write('<span class="artist">'+songs[mysong][0]+'</span></h1>')

		tocfile.write('<div class="chords" style="position:absolute;top:0;right:0;z-index:1;">')
		if usechords: insertchords(mysong)
		tocfile.write("</div>")#chords
		tocfile.write('\n<div class="lyrics" style="position:relative;z-index:2;">'+songs[mysong][2]+'</div>')#gives one blank line, lyrics on top of chords
		tocfile.write('</div>')#song

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
tocfile.write('<img src="ukechords-larger.jpg">')
tocfile.write('</div>\n')  
tocfile.write('<div class="song">\n')
tocfile.write('<img src="piano_chords.jpg">')
tocfile.write('</div>\n')  
tocfile.write('<div class="song">\n')
tocfile.write('<img src="banjochart-larger.jpg">')
tocfile.write('</div>\n')

if not lulu:
	if os.path.isfile('changes'+VERSION+'.txt'):
		tocfile.write('<h1>Changes</h1>' + open('changes'+VERSION+'.txt', encoding='utf-8').read())
	else:
		print("no changes"+VERSION+".txt - skipping the changes page")

if andy: generateToc()
tocfile.write('</body></html>\n')  
tocfile.close()


path=str(os.getcwd()+"/")
if os.access(path+oldfile, os.F_OK): os.remove(path+oldfile)
if os.access(path+pdffile, os.F_OK): os.rename(path+pdffile,path+oldfile)

missing = {k: v for k, v in unknownchords.items() if v}
if missing: print("unknown chords: ", missing)

if andy: print("remaining: ",andysongs)

print("now running prince:", PRINCE, path+htmlfile, "-o", path+pdffile)
result = subprocess.run([PRINCE, path+htmlfile, "-o", path+pdffile])
if result.returncode == 0:
	subprocess.run(["open", path+pdffile])
else:
	print("prince failed with exit code", result.returncode, "- not opening the pdf")

