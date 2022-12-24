# -*- coding: utf-8 -*-
import xml.dom.minidom, string, re, codecs, sys

#guitardict={'D':'D','E':'E','Gmodo2': 'Gmodo2', 'C79': 'C7_9_', 'Am.G': 'Am.G', 'C6.9': 'C6.9', 'Bm7_b5_': 'Bm7_b5_', 'Dm79': 'Dm7_9_', 'Emod2': 'Emod2', 'D79': 'D7_9_', 'Fstm7_b5_': 'Fstm7_b5_', 'G': 'G', 'B7_b9_': 'B7_b9_', 'Em7': 'Em7', 'C7M2': 'C7M2', 'E7.Gst': 'E7.Gst', 'Dm7': 'Dm7', 'Cm7': 'Cm7', 'Fstm7modo2': 'Fstm7modo2', 'Cstm7': 'Cstm7', 'C7M_9_': 'C7M_9_', 'Fstm7b5': 'Fstm7_b5_', 'A7Mmodo2': 'A7Mmodo2', 'F7M': 'F7M', 'A#': 'Bb', 'Asus2': 'Asus2', 'Asus4': 'Asus4', 'Bb': 'Bb', 'G7M': 'G7M', 'Dm7_9_': 'Dm7_9_', 'Cm': 'Cm', 'Fstm': 'Fstm', 'B7b9': 'B7_b9_', 'Bm7b5': 'Bm7_b5_', 'A7': 'A7', 'Dmod2': 'Dmod2', 'E7': 'E7', 'Gstm': 'Gstm', 'C7': 'C7', 'Fm': 'Fm', 'Bm7': 'Bm7', 'A': 'A', 'G7': 'G7', 'C': 'C', 'D7_9_': 'D7_9_', 'Gstm7.png': 'Gstm7.png', 'D': 'D', 'C7M9': 'C7M_9_', 'F': 'F', 'Asus4_2': 'Asus4_2', 'Fm7': 'Fm7', 'Fstm7': 'Fstm7', 'A7M': 'A7M', 'Dm': 'Dm', 'Asus42': 'Asus4_2', 'Gm7modo2': 'Gm7modo2', 'C7_9_': 'C7_9_', 'G7modo2': 'G7modo2', 'Gm7': 'Gm7', 'E7_b9_': 'E7_b9_', 'Em': 'Em', 'E7b9': 'E7_b9_', 'Dm7mod2': 'Dm7mod2', 'F6': 'F6', 'F7': 'F7', 'G7.4': 'G7.4', 'Fm7mod2': 'Fm7mod2', 'Am': 'Am', 'D#': 'Eb', 'Eb': 'Eb', 'B7': 'B7', 'C7M': 'C7M', 'Dmmod2': 'Dmmod2', 'F7mod2': 'F7mod2', 'D7': 'D7', 'B': 'B', 'Am7': 'Am7', 'D7M': 'D7M'}
#ukedict={'Fmaj9': 'Fmaj9', 'E':'E','Gdim': 'Gdim', 'Fmaj7': 'Fmaj7', 'Abmaj7': 'Abmaj7', 'BmM7': 'BmM7', 'Abmaj9': 'Abmaj9', 'G7': 'G7', 'Asus4': 'Asus4', 'Bb': 'Bb', 'Bm': 'Bm', 'D#aug': 'Ebaug', 'G#': 'Ab', 'blank.png': 'blank.png', 'G7sus4': 'G7sus4', 'Aadd9': 'Aadd9', 'Caug': 'Caug', 'A7': 'A7', 'Bsus4': 'Bsus4', 'A#maj9': 'Bbmaj9', 'C7sus4': 'C7sus4', 'Gb7': 'Gb7', 'A#maj7': 'Bbmaj7', 'B7': 'B7', 'Gb': 'Gb', 'Ebaug': 'Ebaug', 'Gm': 'Gm', 'Csm': 'Csm', 'Gsus4': 'Gsus4', 'Dm7': 'Dm7', 'A#m': 'Bbm', 'G#maj9': 'Abmaj9', 'G#aug': 'Abaug', 'G#maj7': 'Abmaj7', 'Fsus4': 'Fsus4', 'F#7': 'Gb7', 'F#m7-5': 'Gbm7-5', 'Dsus4': 'Dsus4', 'F#': 'Gb', 'E9': 'E9', 'Eaug': 'Eaug', 'Dsus2': 'Dsus2', 'E7': 'E7', 'C': 'C', 'G': 'G', 'Fdim': 'Fdim', 'Gbm7-5': 'Gbm7-5', 'A#6': 'Bb6', 'Em': 'Em', 'Eb': 'Eb', 'Bbdim': 'Bbdim', 'F#m': 'Gbm', 'Bbm': 'Bbm', 'Bdim': 'Bdim', 'F#maj9': 'Gbmaj9', 'Csus2': 'Csus2', 'Em7': 'Em7', 'Cmaj7': 'Cmaj7', 'Csus4': 'Csus4', 'G#dim': 'Abdim', 'Cmaj9': 'Cmaj9', 'Bm7-5': 'Bm7-5', 'G#m7-5': 'Abm7-5', 'C7': 'C7', 'Fm': 'Fm', 'Dbdim': 'Dbdim', 'B': 'B', 'Fadd9': 'Fadd9', 'F': 'F', 'Gbm': 'Gbm', 'Ebmaj7': 'Ebmaj7', 'Gadd9': 'Gadd9', 'Bb6': 'Bb6', 'Ebmaj9': 'Ebmaj9', 'Gm7': 'Gm7', 'C#dim': 'Dbdim', 'Cm': 'Cm', 'Cadd9': 'Cadd9', 'C6': 'C6', 'Amaj7': 'Amaj7', 'Bm7': 'Bm7', 'Abaug': 'Abaug', 'Gbmaj9': 'Gbmaj9', 'Am7': 'Am7', 'A#dim': 'Bbdim', 'Bbmaj7': 'Bbmaj7', 'Ddim': 'Ddim', 'Bbmaj9': 'Bbmaj9', 'Abm7-5': 'Abm7-5', 'D': 'D', 'A#': 'Bb', 'Dm': 'Dm', 'Em7-5': 'Em7-5', 'Dmaj7': 'Dmaj7', 'A': 'A', 'D#maj9': 'Ebmaj9', 'D#maj7': 'Ebmaj7', 'Aaug': 'Aaug', 'Abdim': 'Abdim', 'Ab': 'Ab', 'Am': 'Am', 'D#': 'Eb', 'Gmaj9': 'Gmaj9', 'D6': 'D6', 'D7': 'D7'}
#guitardict = json5.load(open('/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/guitar.json',encoding="UTF-8"))
#ukuleledict = json5.load(open("/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/ukulele.json",encoding="UTF-8"))

#let's just find them algorithmically and live dangerously

allchords = []

def getText(nodelist):	#this just deals with XML
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE: rc = rc + node.data
	return rc

def sortedDictValues3(adict): 
	keys = adict.keys()
	keys.sort()
	return keys

def readInSongs(myfeed):
	for song in myfeed.getElementsByTagName("song"):
		artist = getText(song.getElementsByTagName("artist")[0].childNodes).strip()
		artist = string.capwords(re.sub("&","&amp;",artist))
		if '(' in artist:#stupid capwords doesn't capitalize after (s so we do it manually
			loc=artist.find('(')+1
			artist=artist[:loc]+artist[loc].upper()+artist[loc+1:]
		songtitle = getText(song.getElementsByTagName("songtitle")[0].childNodes).strip()
		songtitle = string.capwords(re.sub("&","&amp;",songtitle))
		if '(' in songtitle:#stupid capwords doesn't capitalize after (s so we do it manually
			loc=songtitle.find('(')+1
			songtitle=songtitle[:loc]+songtitle[loc].upper()+songtitle[loc+1:]
		lyrics = getText(song.getElementsByTagName("lyrics")[0].childNodes)
		lyrics = re.sub("&","&amp;",lyrics)
		
		try: chords = getText(song.getElementsByTagName("chords")[0].childNodes)
		except: chords = ""

		indexkey = (artist+songtitle).lower()
		titlekey = (songtitle+artist).lower()
		songs[indexkey]=[artist,songtitle,lyrics]
		songsbytitle[titlekey]=indexkey

if len(sys.argv)<3: sys.exit("usage: python chordadder.py inputxml.xml outputxml.xml")
xmlfile = sys.argv[1]
outfile = sys.argv[2]
songs = {}
songsbytitle = {}
main= xml.dom.minidom.parse(xmlfile)
readInSongs(main)
print (len(songs), "songs read in")
nonchordwords = [" ","opening","refrain", "n.c.", "solo", "name", "spoken", "ensemble", "bridge", "interlude", "rhythm", "all", "lick","x","nc","riff","break","pause","end","again","play","intro","repeat","banjo","fiddle","chord","and","chorus","verse","over","instrumental","tacet","stop","start","outro","coda"]
countofchords = 0

for song in main.getElementsByTagName("song"):
	songchords=[] #reset at the beginning of every song
	lyrics = getText(song.getElementsByTagName("lyrics")[0].childNodes)

	#first lets deal with chordpro format where the chords are in [square brackets]
	for chord in re.findall("\[.*?\]",lyrics):
		chord=chord.strip('[').strip(']')
		badchord=False
		for filler in nonchordwords:
			if filler in chord.lower():badchord=True
		if not badchord: countofchords+=1
		if (not badchord) and (chord not in songchords): songchords+=[chord]
	
	#now let's look for chords that are not in []s. this bit might get revisited one of these days
	for line in lyrics.split('\n'):
		if len(line)<1:continue
		if float(len(line.replace(" ",'')))/float(len(line))<0.5:#if the line is more than half whitespace
			for chord in line.replace('\\',' ').split(): #fix all the slashes. this is a bad hack and we will fix in the future
				badchord=False
				if ":" in chord: badchord=True
				if "--" in chord: badchord=True #it's a tab line, not a chord
				for punctuationmark in string.punctuation.replace("#","").replace("/"," "): 
					chord=chord.replace(punctuationmark,"")  #let's get rid of punctuation except for those sharps and replaced slashes
				if len(chord)==0:continue
				for filler in nonchordwords:
					if filler in chord.lower():badchord=True 
				if chord[0] not in "ABCDEFG": badchord = True
				if (chord[-1] not in "0123456789mABCDEFGb#"): badchord = True
				if ("sus" in chord) or ("min" in chord) or ("maj" in chord) or ("dim" in chord) or ("aug" in chord) or ("add" in chord): badchord = False #last chance!
				if not badchord: countofchords+=1
				if (not badchord) and (chord not in songchords): songchords+=[chord] #just add it to the list but no dupes
				#we're going to live dangerously and find more chords this way.

	justchords=""
	for item in songchords: 
		justchords+=item+" "
		if item not in allchords: allchords+=[item] #add to the master list
	print(justchords)
	chordtag = main.createElement("chords")
	text = main.createTextNode(justchords)
	chordtag.appendChild(text)
	song.appendChild(chordtag)

with open(outfile,'w') as f:
	main.writexml(f)

print("all the chords i found here:")
print(sorted(allchords))
print("total count of chords: ",countofchords)
