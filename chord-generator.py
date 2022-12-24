import xml.dom.minidom, string, re, os, codecs, sys, math, subprocess, json5, shutil

#guitardict = json5.load(open('/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/guitar.json',encoding="UTF-8"))
#ukuleledict = json5.load(open("/Users/jofish/Dropbox/jlaptop/music/chordpro/lib/App/Music/ChordPro/res/config/ukulele.json",encoding="UTF-8"))
#chorddicts = {'guitar':guitardict, 'ukulele':ukuleledict}
directory = "/Users/jofish/Dropbox/jlaptop/music/diagrams/"

chorddicts = {'guitar': ['Amaj9', 'Dmin#5', 'Bb5', 'C5', 'F5', 'G5', 'C5', 'D5', 'E5', 'F5', 'B5', 'D/F', 'C/G', 'G7/6', 'Dm6', 'F1', 'C8', 'Am5', 'Dm5', 'D300', 'E3', 'Cadd2', 'F5', 'A5', 'E5', 'D5', 'Ab5', 'C5', 'G5', 'D7sus', 'G7sus', 'C5', 'FB', 'A7sus4', 'Cmaj', 'A7sus9', 'conversation', 'BmMaj7', 'Asus9', 'Bmsus9', 'Bmsus4', 'E13', 'A13', 'Dmaj4', 'Em9', 'D13', 'Bm9', 'E7sus4', 'A7sus4', 'Dm6', 'C7b9', 'C7b9', 'C5', 'E5', 'A7sus4', 'Coda', 'A7sus', 'G/D', 'A/D', 'C/E', 'B/A', 'C/A', 'D/A', 'Bm/A', 'Em9', 'CDE', 'CD', 'F5', 'A5'], 'ukulele': ['C#', 'Esus4', 'Amaj9', 'C#m7', 'Dmin#5', 'Bmin', 'F#min', 'Emin', 'your', 'Bb5', 'C5', 'F5', 'G5', 'C5', 'D5', 'E5', 'F5', 'B5', 'D4', 'Am6', 'Am6', 'D/F', 'C/G', 'G7/6', 'Dm6', 'F1', 'C8', 'Am5', 'Dm5', 'A4', 'D300', 'E3', 'Cadd2', 'F5', 'A5', 'E5', 'D5', 'Ab5', 'C5', 'G5', 'D7sus', 'G7sus', 'Em6', 'C#m', 'G#m', 'C5', 'Bbdim7', 'Gm6', 'FB', 'Esus', 'A7sus4', 'Dsus', 'D11', 'Cmaj', 'A7sus9', 'conversation', 'BmMaj7', 'Asus9', 'Bmsus9', 'Bmsus4', 'E13', 'A13', 'Dmaj4', 'Em9', 'D13', 'Bm9', 'E7sus4', 'A7sus4', 'Em6', 'Dsus', 'Dm6', 'Fdim7', 'C7b9', 'Fdim7', 'C7b9', 'C5', 'E5', 'A7sus4', 'Coda', 'A7sus', 'G/D', 'A/D', 'C/E', 'Esus4', 'N.C.', 'B/A', 'C/A', 'D/A', 'Bm/A', 'Em9', 'CDE', 'CD', 'Bmin', 'F5', 'Bbsus4', 'A5', 'Gmin'], 'banjo': []}

for chorddict in chorddicts:
	for chordinfo in chorddicts[chorddict]:
# 		if "copy" in chordinfo:
# 			shutil.copyfile(directory+chorddict+"/"+chordinfo['copy']+".png",directory+chorddict+"/"+chordinfo['name']+".png")
# 			continue #and we're done
# 	
# 		#adjust the base if we need to 
# 		myfrets = chordinfo['frets']
# 		if chordinfo['base']>1:
# 			print("before fixing: ", myfrets)
# 			for fret in range(len(myfrets)):
# 				if myfrets[fret]>-1: myfrets[fret]=myfrets[fret]+chordinfo['base']
# 			print("after fixing: ", myfrets)

		#printlist = ["/usr/bin/python3","thatchord.py",chordinfo['name'],"--instrument",chorddict,"--directory",directory+chorddict,"--output","NONE","--controlfreak",str(myfrets)]
		printlist = ["/usr/bin/python3","thatchord.py",chordinfo,"--instrument",chorddict,"--directory",directory+chorddict+"-truechord","--output","NONE"]

		print (printlist)
		subprocess.run(printlist)

