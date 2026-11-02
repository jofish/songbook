import xml.dom.minidom, string, re, os, codecs, sys, math, subprocess, json5, shutil

guitardict = json5.load(open('/path/to/your/music/chordpro/lib/App/Music/ChordPro/res/config/guitar.json',encoding="UTF-8"))
ukuleledict = json5.load(open("/path/to/your/music/chordpro/lib/App/Music/ChordPro/res/config/ukulele.json",encoding="UTF-8"))
chorddicts = {'banjo':guitardict}
directory = "/path/to/your/music/diagrams/"

for chorddict in chorddicts:
	for chordinfo in chorddicts[chorddict]['chords']:
		if 'sus9' in chordinfo['name']: continue

		if "copy" in chordinfo:
			shutil.copyfile(directory+chorddict+"/"+chordinfo['copy']+".png",directory+chorddict+"/"+chordinfo['name']+".png")
			continue #and we're done
		
		printlist = ["/usr/bin/python3","thatchord.py",chordinfo['name'],"--instrument",chorddict,"--directory",directory+chorddict,"--output","NONE"]
		print (printlist)
		subprocess.run(printlist)


