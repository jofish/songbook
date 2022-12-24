import xml.dom.minidom, string, os, codecs, sys, math, subprocess, modes

maxpagelength = 60 #normal setup on US Letter pages is 60 lines of lyrics plus 2 lines for title
chorddirectory= "diagrams/"
unknownchords = {"guitar":[], "ukulele": [], "banjo": []}
songs = {}
songsbytitle = {}
currentlyodd=True #we always start on an odd page
holdlist=[] #we'll use this to put 2+ page songs into if they would start on an odd page
discardmode, lulumode = False, False

def getText(nodelist):	#this just deals with XML
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE: rc = rc + node.data
	return rc
		
def insertchords(mysong): #inserts the table with the chords
	chords = songs[mysong][3]
	chordtable="""<div class="chords" style="position:absolute;top:0;right:0;z-index:1;"><table border=0 style="z-index:0"><tr><th width=20%> </th><th width=40%>Guitar</th><th width=40%>Uke</th></tr>\n""" #column headings	
	for chord in chords.split():#and now the chord table		
		chordtable+='<tr><td style="text-align: right">'+chord+"</td>" #first the name
		chord=chord.replace('/','_') #fix the fact we can't have slashes in filenames
		for instrument in ['guitar','ukulele']:		#could add, say, banjo	
			if os.path.isfile(chorddirectory+instrument+"/"+chord+".png"): #first check to see if it exists in the chords generated from ChordPro data
				chordtable+='<td width=40 height=40><img src="'+chorddirectory+instrument+"/"+chord.replace("#","%23")+'.png"></td>\n'
			elif os.path.isfile(chorddirectory+instrument+"-truechord"+"/"+chord+".png"): #see if we've generated with truechord automatically, which is less reliable
				chordtable+='<td width=40 height=40><img src="'+chorddirectory+instrument+"-truechord"+"/"+chord.replace("#","%23")+'.png"></td>\n'
			#and here is where we would put the inline generating code in to make truechord automatically generate these on the fly
			#which is something like 
			#printlist = ["/usr/bin/python3","ThatChord/thatchord.py",chord,"--instrument",instrument,"--directory",chorddirectory+instrument]
			#subprocess.call(printlist)
			else: 
				chordtable+='<td width=40 height=40>_?_</td>\n' #if it's not, i got nothing for you.  but we can search for this string.
				unknownchords[instrument]+=[chord.replace('_','/')] #and let's keep track of them.
		chordtable+='</tr>'
	chordtable+="</table></div>\n" #end of table-within-a-table and end of chords div
	tocfile.write(chordtable)

#this writes each of the components of the songs in turn
def writesong(mysong):
	try:
		tocfile.write('<div class="song">\n')
		tocfile.write('<h1><span class="artist">'+songs[mysong][0]+'</span> - ')
		tocfile.write('<span class="songtitle">'+songs[mysong][1]+'</span></h1>\n')
		tocfile.write('<a name="'+mysong+'" id="'+mysong+'" />\n')#internal anchor so TOC works
		tocfile.write('<div class="chords" style="position:absolute;top:0;right:0;z-index:1;"')
		insertchords(mysong)
		tocfile.write("</div>\n")#chords				
		tocfile.write('<div class="lyrics" style="left:0;z-index:0;">'+songs[mysong][2]+'</div>\n')
		global currentlyodd
		if songpagelength % 2 == 1: currentlyodd = not(currentlyodd) 
	except UnicodeEncodeError:
		print("ERROR in song cos of unicode characters (this song will not be included)",song)


#ok let's go. first, let's check the arguments are correct
if len(sys.argv)<2: sys.exit("usage: python songbookmaker.py root-of-xml-file.xml\nwill output root-of-xmlfile.html and root-of-xmlfile.pdf and root-of-xmlfile.pdf.old")
xmlfile = sys.argv[1]
htmlfile = xmlfile.replace("xml","html")
pdffile = xmlfile.replace("xml","pdf")
oldfile = xmlfile.replace("xml","old")
if len(sys.argv)>2:
	if sys.argv[2]=="lulu": lulumode=True
	elif sys.argv[2]=="discard": discardmode=True

def readInSongs(myfeed):
	for song in myfeed.getElementsByTagName("song"):
			artist = getText(song.getElementsByTagName("artist")[0].childNodes).strip().replace("&","&amp;")
			songtitle = getText(song.getElementsByTagName("songtitle")[0].childNodes).strip().replace("&","&amp;")
			lyrics = getText(song.getElementsByTagName("lyrics")[0].childNodes).strip().replace("&","&amp;")
			songlength = lyrics.count("\n") + 2 #2 line title
			if (songlength % maxpagelength < 10) & (songlength % maxpagelength >0): print("might be shortenable to a multiple of",maxpagelength," lines to save pages:", songlength, "lines", songtitle) 
			chords = getText(song.getElementsByTagName("chords")[0].childNodes)
			indexkey = (artist+songtitle).lower()
			titlekey = (songtitle+artist).lower()
			songs[indexkey]=[artist,songtitle,lyrics,chords]
			songsbytitle[titlekey]=indexkey
		
#if we're going to print to lulu, we handle the front pages separately. 
readInSongs(xml.dom.minidom.parse(xmlfile))
print(len(songs), "songs read in")
tocfile = codecs.open(htmlfile,'w','ascii') #should probably switch to something that handles unicode

#now let's put in the opening material
tocfile.write(modes.titletext(discardmode,lulumode)) #titletext is defined in the modes.py file

#and now the table of contents pages that will be filled out by princeXML
tocfile.write("""<div class="titlepage"><h1>songlist by artist</h1></div><ul class="toc">""")
for song in sorted(songs.keys()):
	try: tocfile.write('<li class="tocline1"><a href="#'+song+'">'+songs[song][0]+' - '+songs[song][1]+"</a>\n")
	except: print("ERROR TOC:",song)
tocfile.write("</ul>\n")

#and now let's list sorted by title too
tocfile.write("""<div class="titlepage"><h1>songlist by title</h1></div><ul class="toc">""")
for song in sorted(songsbytitle.keys()):
	thekey = songsbytitle[song]
	tocfile.write('<li class="tocline1"><a href="#'+thekey+'">'+songs[thekey][1]+' - '+songs[thekey][0]+"</a>\n")
tocfile.write("</ul>\n")


for song in sorted(songs.keys()): 
	songpagelength =math.ceil((len(songs[song][2].splitlines())+2.0) / maxpagelength) #60 lines/pg + 2 line title
	if songpagelength>1 and currentlyodd: #if it's a long song and we're on an odd page
		holdlist.append(song) #add it to the hold stack
		continue
	writesong(song)
	while ((not currentlyodd) and (len(holdlist)>0)): 
		popsong=holdlist.pop(0)
		writesong(popsong)
if len(holdlist)>0: writesong(holdlist.pop(0)) #just to check nothing left over which could theoretically happen

#ok now let's write our closing material, which is a bunch of chord charts
closingmaterial = """<div class="song"><img src="charts/guitar-chords-chord-chart-enlarged-300dpi.jpg"></div>\n
			     <div class="song"><img src="charts/ukechords.png"></div>\n
			     <div class="song"><img src="charts/piano_chords.jpg"></div>\n
			     <div class="song"><img src="charts/banjochart.jpg"><p>Thanks to Pete Seeger</p></div>\n 
			     </body></html>\n'"""
			     
tocfile.write(closingmaterial)
tocfile.close()

#now let's make a backup of our most recent file
path=str(os.getcwd()+"/") 
if os.access(path+oldfile, os.F_OK): os.remove(path+oldfile)
if os.access(path+pdffile, os.F_OK): os.rename(path+pdffile,path+oldfile)
if len(unknownchords)>0: print("unknown chords: ",str(unknownchords))

os.execl("/usr/local/lib/prince/bin/prince", "/usr/local/lib/prince/bin/prince",path+htmlfile,"-o",path+pdffile)
#subprocess.run(["/usr/local/lib/prince/bin/prince", "/usr/local/lib/prince/bin/prince",path+htmlfile,"-o",path+pdffile], check=False)
#os.system(path+pdffile)
