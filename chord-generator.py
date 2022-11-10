import xml.dom.minidom, string, re, os, codecs, sys, math, subprocess, json5, shutil

guitardict = json5.load(open('/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/guitar.json',encoding="UTF-8"))
ukuleledict = json5.load(open("/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/ukulele.json",encoding="UTF-8"))
chorddicts = {'guitar':guitardict, 'ukulele':ukuleledict}
directory = "/Users/jofish/Dropbox/jlaptop/music/diagrams/"


for chorddict in chorddicts:
	for chordinfo in chorddicts[chorddict]['chords']:
		if "copy" in chordinfo:
			shutil.copyfile(directory+chorddict+"/"+chordinfo['copy']+".png",directory+chorddict+"/"+chordinfo['name']+".png")
			continue #and we're done
	
		#adjust the base if we need to 
		myfrets = chordinfo['frets']
		if chordinfo['base']>1:
			print("before fixing: ", myfrets)
			for fret in range(len(myfrets)):
				if myfrets[fret]>-1: myfrets[fret]=myfrets[fret]+chordinfo['base']
			print("after fixing: ", myfrets)

		printlist = ["/usr/bin/python3","thatchord.py",chordinfo['name'],"--instrument",chorddict,"--directory",directory+chorddict,"--output","NONE","--controlfreak",str(myfrets)]
		print (printlist)
		subprocess.run(printlist)

