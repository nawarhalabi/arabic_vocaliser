#-*- coding: utf-8 -*-
import sys, codecs, os, re
from pyaramorph.pyaramorph import Analyzer
pyaramorph = Analyzer()

def preprocessBeforeBama(ar_text):
    ar_text = re.sub(u"([().,])", u" \\1 ", ar_text)
    ar_text = re.sub(u"\s+", u" ", ar_text)
    return ar_text

def runBama(ar_text):
    #Has to be windows-1256 for BAMA?
    outfh = codecs.open("ptemp0.txt", "w", "windows-1256")
    outfh.write(ar_text)
    outfh.close()

    os.system("./bama/aramorph.sh ptemp0.txt ptemp1.txt 2> /dev/null")

    infh = codecs.open("ptemp1.txt", "r", "utf-8")
    bama_pos = infh.read().strip()
    infh.close()

    return bama_pos

def runPyBama(ar_text):
    bama_pos_list = []
    for ar_word in ar_text.split(u" "):
        bw_word = ar2bw(ar_word)

        results = pyaramorph.analyze(bw_word)
        #print "RESULTS FOR %s: %s" % (bw_word, results)
        if len(results) > 0:
            for res in results:

                print u"RES:", res

                res_lines = res.split(u"\n")
                pos_line = res_lines[1].strip()
                pos_line = re.sub(u"pos:\s+", u"", pos_line)
                bama_pos_list.append(pos_line)
        bama_pos_list.append("") #word separator!

    bama_pos = u"\n".join(bama_pos_list)
    return bama_pos

#Todo: these two should be the same (= the second one), change following to allow
#word+analysis in both cases
def runPyBama2(ar_text):
    bama_pos_list = []
    for ar_word in ar_text.split(u" "):
        bw_word = ar2bw(ar_word)

        #Remove any diacritics before bama lookup
        bw_word = re.sub(u"[FNKauio~]", u"", bw_word)
        print u"bw_word:", bw_word


        bama_pos_list.append(bw_word)

        results = pyaramorph.analyze(bw_word)
        #print "RESULTS FOR %s: %s" % (bw_word, results)
        if len(results) > 0:
            for res in results:

                print u"RES:", res

                res_lines = res.split(u"\n")
                solution_line = res_lines[0].strip()
                m = re.search(u" ([^ \)]+)\)", solution_line)
                vocalised_word = m.group(1)
                pos_line = res_lines[1].strip()
                pos_line = re.sub(u"pos:\s+", u"", pos_line)
                bama_pos_list.append(vocalised_word + u" " + pos_line)
        bama_pos_list.append(u"") #word separator!

    bama_pos = u"\n".join(bama_pos_list)
    return bama_pos


def filterWithPreVocalised(ar_text, bama_pos):

    ar_words = ar_text.split(u" ")


    sentences = re.split(u"\p{P}\¡\n", bama_pos)
    newSentences = []
    for sentence in sentences:
        #sys.stderr.write("SENTENCE: "+sentence+"\n")
        #Double newlines separate words
        words = sentence.split(u"\n\n")
        newWords = []

        i = 0
        while i < len(ar_words):
            ar_word = ar_words[i]
            word = words[i]

            options = word.strip().split(u"\n")
            unvocWord = options[0]
            options = options[1:]
            newOptions = [unvocWord]
            for option in options:
                #print "OPTION:", option
                solution = option.split(u" ")[0]
                if matchVocalisation(ar_word, solution):
                    newOptions.append(option)
            newWord = u"\n".join(newOptions)
            newWords.append(newWord)
            i += 1
        newSentences.append(u"\n\n".join(newWords))
    return u"\p{P}\¡\n".join(newSentences)

def matchVocalisationOLD(ar_word, solution):
    #doesn't work in a case like "sa" "s", they will match
    bw_word = ar2bw(ar_word)
    print u"matchVocalisation", bw_word, solution,
    if not re.search(u"[FNKauio~]", bw_word):
        print "True"
        return True
    else:
        i = 0
        j = 0
        while i < len(solution) and j < len(bw_word):
            cs = solution[i]
            cw = bw_word[j]
            #print "Matching:", cw, cs
            if cw == cs:
                i += 1
                j += 1
            elif i+1 < len(solution) and cs in u"FNKauio" and solution[i+1] == cw:
                i += 2
                j += 1
            elif i+2 < len(solution) and cs == u"~" and solution[i+1] in u"FNKauio" and solution[i+2] == cw:
                i += 3
                j += 1
            else:            
                print "False"
                return False
        print "True"
        return True

def matchVocalisation(ar_word, solution):
    bw_word = ar2bw(ar_word)
    print "matchVocalisation", bw_word, solution,
    if not re.search(u"[FNKauio~]", bw_word):
        print "True"
        return True
    else:
        s_rest = solution
        w_rest = bw_word

        #normalise order of shadda+other diacritic, shadda should come first! example is التاريخيَّة
        #where it doesn't (taken from web page): bw AltAryxya~p
        w_rest = re.sub(u"([FNKauio])(~)",u"\\2\\1",w_rest)


        while s_rest != u"":
            w_m = re.match(r"^(.)(~?)(%s?)(.*)$" % u"[FNKauio]", w_rest)
            w_letter = w_m.group(1)
            w_shadda = w_m.group(2)
            w_voc = w_m.group(3)

            print "1 Trying %s, %s, %s from %s with %s" % (w_letter,w_shadda,w_voc, w_rest, s_rest)

            w_rest = w_m.group(4)



            s_m = re.match(r"^(%s%s%s)(.*)$" % (w_letter, w_shadda, w_voc), s_rest)
            if not s_m:
                print "False"
                return False                    
            else:
                if w_voc != "":
                    print "1 %s%s%s matches %s" % (w_letter,w_shadda,w_voc,s_m.group(1))
                    s_rest = s_m.group(2)
                else:
                    print "2 Trying %s, %s with %s" % (w_letter, "[FNKauio]", s_rest)
                    s_m2 = re.match("^(%s%s)(.*)$" % (w_letter, "(~?[FNKauio]?)"), s_rest)                    

                    print "2 %s%s%s matches %s" % (w_letter,w_shadda,w_voc,s_m2.group(1))
                    s_rest = s_m2.group(3)
                    print "rest:", s_rest


        print "True"
        return True
            


def convertBamaToSrilm(bama_pos):
    result = []
    #TODO what does this regexp mean?? I have no example at the moment with multiple sentences
    sentences = re.split(u"\p{P}\¡\n", bama_pos)
    for sentence in sentences:
        #sys.stderr.write("SENTENCE: "+sentence+"\n")
        #Double newlines separate words
        words = sentence.split(u"\n\n")

        if len(words) > 0:
            result.append(u"<s> *noevent*\n")
            for word in words:
                word = word.strip()
                #sys.stderr.write("WORD: "+word+"\n")
                #newline separates readings
                options = word.split(u"\n")

                #The first is the unvocalised word (using runPyBama2)
                options = options[1:]

                tagList = convertBAMAtag(options)

                #If there are no tags, i.e unknown word
                if len(tagList) == 0:
                    tagList = [u"P", u"T", u"NDG", u"NDA", u"NDN", u"NUG", u"NUA", u"NUN", u"P+NDG", u"P+NUG", u"VIM", u"VPR", u"VIJ", u"VIS", u"VID"]

                optionsList = []
                for tag in tagList:
                    #Todo higher probability in case of TT and P
                    optionsString = u"%s %.6f" % (tag, 1.0/len(tagList))
                    optionsList.append(optionsString)

                    


                result.append(u"w %s\n" % " ".join(optionsList))
            result.append(u"</s> *noevent*\n")
        #result.append("<s> *noevent*\r\n</s> *noevent*\n")
        #the above is in case there is no word in the sentence?
    resultString = u"".join(result).strip()

    return resultString

def convertBAMAtag(options):

    optionsList = []

    for option in options:
        sys.stderr.write(u"OPTION: %s, type: %s\n" % (option, type(option)))

        #using runPyBama2 there is "word analysis" in each, only the analysis is wanted here
        if u" " in option:
            option = option.split(u" ")[1]

        P = False
        N = False
        D = False
        V = False
        I = False
        T = False
        A = False
        C = False
        DP = False

        BAMATags = option.split(u"+")
        for BAMATag in BAMATags:

            #sys.stderr.write("BAMATag: "+BAMATag+"\n")

            #If there is no bama tag at all
            #TODO mark this in some way, it means a words should be added to the dictionary
            if not u"/" in BAMATag:
                continue

            curTag = BAMATag.split(u"/")[1]

            if curTag == u"P" or curTag == u"PREP":
                P = True
            elif curTag == u"N" or curTag == u"ADJ" or curTag == u"NOUN" or curTag == u"NOUN_PROP" or curTag == u"PROP_NOUN":
                N = True
            elif curTag == u"VPR" or curTag == u"VERB_PERFECT":
                V = True
            elif curTag == u"VI" or curTag == u"VERB_IMPERFECT":
                V = True
                I = True
            elif curTag == u"VIM" or curTag == u"VERB_IMPERATIVE":
                I = True
            elif curTag == u"D" or curTag == u"DET":
                D = True
            elif curTag == u"ABBREV":
                A = True
            elif curTag == u"CONJ":
                C = True
            else:
                T = True
            
        if N:
            if D:
                if P:
                    optionsList.append(u"P+NDG")
                else:
                    optionsList.append(u"NDG")
                    optionsList.append(u"NDN")
                    optionsList.append(u"NDA")
            else:
                if P:
                    optionsList.append(u"P+NUG")
                else:
                    optionsList.append(u"NUG")
                    optionsList.append(u"NUN")
                    optionsList.append(u"NUA")
        elif V:
            if I:
                optionsList.append(u"VIJ")
                optionsList.append(u"VIS")
                optionsList.append(u"VID")
            else:
                optionsList.append(u"VPR")
        elif I:
            optionsList.append(u"VIM")
        elif P:
            if T:
                optionsList.append(u"P")
            else:
                #optionsList.append("TT") error?? TT is not in POSNgrams/vocab
                optionsList.append(u"T")
        elif A:
            optionsList.append(u"A")
        else:
            optionsList.append(u"T")

        #sys.stderr.write("OPTIONSLIST: "+str(optionsList)+"\n")

    if u"A" in optionsList and not u"P" in optionsList:
        optionsList.append(u"T")

    #remove duplicates
    optionsList = list(set(optionsList))
    if u"A" in optionsList:
        optionsList.remove(u"A")

    return optionsList


def runSRILM(srilm_pos):
    outfh = codecs.open("ptemp2.txt", "w", "utf-8")
    outfh.write(srilm_pos)
    outfh.close()

	os.system("./ngram/hidden-ngram -lm ngram/POSNgrams/taggerNgram4.txt -order 4 -text-map ptemp2.txt -hidden-vocab ngram/POSNgrams/vocab.txt > ptemp2a.txt")

    infh = codecs.open("ptemp2a.txt","r", "utf-8")
    srilm_pos = infh.read()
    infh.close()
    return srilm_pos

def removeSentenceBoundaries(res):
    res = re.sub(u"</s>", u"", res).strip()
    res = re.sub(u"<s>", u"", res)
    res = re.sub(u"\n", u"*noevent*", res)
    res = re.sub(u" +", u" ", res).strip()
    res = re.sub(u"w ", u"", res).strip()

    outfh = codecs.open("ptemp3.txt", "w", "utf-8")
    outfh.write(res)
    outfh.close()

    return res;

def runBamaWithTags(ar_text):
    #Has to be windows-1256 for BAMA
    outfh = codecs.open("ptemp4.txt","w","windows-1256")
    outfh.write(ar_text)
    outfh.close()

    os.system("./bama/aramorphWithTags.sh ptemp4.txt ptemp5.txt 2> /dev/null")

    infh = codecs.open("ptemp5.txt", "r", "utf-8")
    bama_pos = infh.read()
    infh.close()

    return bama_pos

def filterBamaWithTags(bama_pos, srilm_pos, addCaseEndings):

    #What is right? It sounds odd to me with case endings but who am I to judge..
    addCaseEndings = False

    taggedBAMA = bama_pos.split(u"\n\n")
    taggedWords = srilm_pos.split(u" ")
    i = 0
    res = []

    #Punctuation can affect this
    #    while i < len(taggedBAMA):
    while i < len(taggedWords):
        options = taggedBAMA[i].strip().split(u"\n")
        pos = taggedWords[i]

        #sys.stderr.write(options[0]+" "+pos+"\n")

        #unvocalised word
        res.append(options[0])

        for option in options[1:]:
            (voc, bama_tag) = option.split(u" ")
            sys.stderr.write(u"V: %s, T: %s\n" % (voc, bama_tag))
            tags = convertBAMAtag([bama_tag])
            sys.stderr.write(u"Word: %s, Tags: %s, Pos: %s\n" % (voc, tags, pos))
            #add the vocalised form if the tag matches
            if pos in tags:
                #TODO also add stuff to do with gemination after Al, and case endings

                # ktb #unvocalised word above
                # kataba #I don't think they should appear twice?
                # kataba
                # kutiba
                # kutiba
                
                # AlTfl
                # AlT~ifolu
                # AlT~ifol
                # AlT~afalu
                # AlT~afal
                
                # AlwZyfp
                # AlowaZiyfapu
                # AlowaZiyfap


                #If it's a definite noun
                sun_letters = u"tTdDsSzZlrn\$\*"
                if u"ND" in pos:
                    #can there be an l before the def art l? preposition!

                    if re.search(u"^([^l]+)l([" + sun_letters + u"])(.+)$", voc):
                        #def.art + sun letter
                        #AlTifol -> AlT~ifol
                        newVoc = re.sub(u"^([^l]+)l([" + sun_letters + u"])(.+)$", u"\\1l\\2~\\3", voc)
                        sys.stderr.write(u"newVoc (sun): " + newVoc + u"\n")
                    else:
                        #def.art + moon letter
                        newVoc = re.sub(u"^([^l]+)l(.)(.+)$", u"\\1lo\\2\\3", voc)
                        sys.stderr.write(u"newVoc (moon): " + newVoc + u"\n")

                    if addCaseEndings:
                        if u"NDG" in pos:
                            #genitive, add -i
                            res.append(newVoc + u"i")
                        elif u"NDA" in pos:
                            #accusative, add -a
                            res.append(newVoc + u"a")
                        elif u"NDN" in pos:
                            #nominative, add -u
                            res.append(newVoc + u"u")

                    #adding newVoc after inflected, to get same output as FinalDiacritizer
                    res.append(newVoc)



                
                elif u"NU" in pos:
                    if addCaseEndings:
                        if u"NUG" in pos:
                            #genitive, add -i
                            res.append(voc + u"i")
                        elif u"NUA" in pos:
                            #accusative, add -a
                            res.append(voc + u"a")
                        elif u"NUN" in pos:
                            #nominative, add -u
                            res.append(voc + u"u")
                    res.append(voc)
                    
                else:
                    #if it's not a noun
                    res.append(voc)
                

            else:
                sys.stderr.write("REMOVING %s %s - does not match %s\n" % (voc, tags, pos))
        res.append("")


        i += 1
        
    outfh = codecs.open("ptemp6.txt", "w", "utf-8")
    outfh.write(u"\n".join(res).strip())
    outfh.close()

    return u"\n".join(res).strip()



transliterate = {}

#transliterate["{"] = u"ا" #//letter hamza al wasel


transliterate[u"'"] = u"ء"
transliterate[u"|"] = u"آ"
transliterate[u">"] = u"أ"
transliterate[u"&"] = u"ؤ"
transliterate[u"<"] = u"إ"
transliterate[u"}"] = u"ئ"
transliterate[u"A"] = u"ا"
transliterate[u"b"] = u"ب"
transliterate[u"p"] = u"ة"
transliterate[u"t"] = u"ت"
transliterate[u"v"] = u"ث"
transliterate[u"j"] = u"ج"
transliterate[u"H"] = u"ح"
transliterate[u"x"] = u"خ"
transliterate[u"d"] = u"د"
transliterate[u"*"] = u"ذ"
transliterate[u"r"] = u"ر"
transliterate[u"z"] = u"ز"
transliterate[u"s"] = u"س"
transliterate[u"$"] = u"ش"
transliterate[u"S"] = u"ص"
transliterate[u"D"] = u"ض"
transliterate[u"T"] = u"ط"
transliterate[u"Z"] = u"ظ"
transliterate[u"E"] = u"ع"
transliterate[u"g"] = u"غ"
transliterate[u"f"] = u"ف"
transliterate[u"q"] = u"ق"
transliterate[u"k"] = u"ك"
transliterate[u"l"] = u"ل"
transliterate[u"m"] = u"م"
transliterate[u"n"] = u"ن"
transliterate[u"h"] = u"ه"
transliterate[u"w"] = u"و"
transliterate[u"Y"] = u"ى"
transliterate[u"y"] = u"ي"
transliterate[u"P"] = u"ب"
transliterate[u"J"] = u"ج"
transliterate[u"V"] = u"ف"
transliterate[u"G"] = u"ق"
transliterate[u"-"] = u"-"

transliterate[u"_"] = u""#//not a letter

transliterate[u"F"] = u"ً" #an
transliterate[u"N"] = u"ٌ" #un
transliterate[u"K"] = u"ٍ" #in
#transliterate["a"] = u"َ " #a (broken)
transliterate[u"a"] = u"َ" #a 
transliterate[u"u"] = u"ُ" #u
transliterate[u"i"] = u"ِ" #i
transliterate[u"~"] = u"ّ" #
transliterate[u"o"] = u"ْ" #

ar2bw_map = {}
for bw in transliterate.keys():
    ar = transliterate[bw]
    #print "%s -> %s" % (ar, bw)
    ar2bw_map[ar] = bw

#?? ar2bw_map["."] = "."

if u"ك" not in ar2bw_map:
    print "aaaaaaaaaaaaaaaaaaaaaaaaa"
    sys.exit()

def bw2ar(bw):

    ar_list = []
    for c in bw:
        if re.match(u"[0-9]", c):
            ar_list.append(c)
        elif c in transliterate:
            ar_list.append(transliterate[c])
        else:
            sys.stderr.write("WARNING: bw2ar %s not found, replacing with dash\n" % c)
            ar_list.append(u"-")
    ar = u"".join(ar_list)
    #sys.stderr.write("bw2ar: %s -> %s\n" % (bw,ar))
    return ar


def ar2bw(ar):
    bw_list = []
    for c in ar:
        if re.match(u"[0-9]", c):
            bw_list.append(c)
        elif c in ar2bw_map:
            bw_list.append(ar2bw_map[c])
        else:
            sys.stderr.write("WARNING: ar2bw %s not found, replacing with dash\n" % c)
            bw_list.append(u"-")

    bw = u"".join(bw_list)
    #sys.stderr.write("ar2bw: %s -> %s\n" % (ar,bw))
    return bw


def createBAMAMap(bama_filtered, ar_text):

    bw_words = []
    for ar_word in ar_text.split(u" "):
        bw_words.append(ar2bw(ar_word))


    
    ar_list = []
    for c in bama_filtered:
        if c == u" " or c == u"\n":
            ar_list.append(c)
        else:
            ar_list.append(bw2ar(c))

    #text = "".join(ar_list)
    text = bama_filtered

    res = []
    res.append(u"<s> *noevent*")

    entries = text.split(u"\n\n")
    e = 0
    while e < len(entries):
        entry = entries[e]
        bw_word = bw_words[e]
        e += 1

        options = entry.split(u"\n")
        #options[0] is the unvocalised input, the rest are vocalised alternatives
        unvoc = options[0]
        options = options[1:]
        alts = []
        for char in unvoc:
            alts.append([])

        #If there are no options, means that the word was not given
        #any analysis by BAMA.
        #Add all possible alternatives to every letter and hope for the best
        #If there are any diacritics in the input text, use them!
        if len(options) == 0:
            i = 0
            j = 1
            while i < len(unvoc):
                char = unvoc[i]
                alt = alts[i]

                #If there is shadda+other diacritic in the input
                if j+1 < len(bw_word) and bw_word[j] == u"~" and bw_word[j+1] in u"FNKauio":
                    diacritics = [u"~"+bw_word[j+1]]
                    j += 2

                #If there is a diacritic in the input
                elif j < len(bw_word) and bw_word[j] in u"FNKauio~":
                    diacritics = [bw_word[j]]
                    j += 1
                    
                elif char in [u"A"]:
                    diacritics = [u"None"]
                else:
                    diacritics = [u"None", u"F", u"N", u"K", u"a", u"u", u"i", u"o", u"~a", u"~u", u"~i"]
                for diacritic in diacritics:
                    alt.append(diacritic)
                i += 1
                j += 1

        for option in options:
            #sys.stderr.write(unvoc+" "+option+"\n")
            i = 0
            j = 1
            while i < len(unvoc):
                unvoc_char = unvoc[i]
                #sys.stderr.write("unvoc_char: "+unvoc_char+"\n")
                if j < len(option):
                    voc_char = option[j]
                    #sys.stderr.write("voc_char: "+voc_char+"\n")
                    #In Form1.cs in some cases all possible diacritics are appended.
                    #Why is that? In the example that happens for the first l in
                    #AlTfl, and for y in AlwZyfp
                    #Is it correct? It looks odd.
                    if voc_char in u"FNKauio":                        
                        alts[i].append(voc_char)
                        j += 1
                    elif voc_char == u"~":                        
                        #If shadda: look at following char too
                        #alts[i].append(voc_char)
                        j += 1
                        if j < len(option): 
                            next_voc_char = option[j]
                            if next_voc_char in u"FNKauio":                        
                                alts[i].append(u"%s%s" % (voc_char,next_voc_char))
                                j += 1
                            else:
                                alts[i].append(voc_char)
                        else:
                            alts[i].append(voc_char)

                    else:
                        alts[i].append(u"None")
                        
                    j += 1
                else:
                    alts[i].append(u"None")

                i += 1

                
        #remove duplicates
        uniq_alts = []
        for alt in alts:
            alt = list(set(alt))
            uniq_alts.append(alt)
        alts = uniq_alts

        #sys.stderr.write(alts)


        #build result list..

        i = 0
        while i < len(unvoc):
            #sys.stderr.write("Char: "+unvoc[i]+"\n")
            #sys.stderr.write("DAlts: "+alts[i]+"\n")
            srilm_data = []
            srilm_data.append(bw2ar(unvoc[i]))
            for alt in alts[i]:
                if alt == u"None":
                    srilm_data.append(u"<%s>" % u"u")
                else:
                    srilm_data.append(u"<%s>" % bw2ar(alt) )

                srilm_data.append(u"%f" % float(1.0/len(alts[i])) )
            #sys.stderr.write(" ".join(srilm_data))

            res.append(" ".join(srilm_data))
            i += 1

        res.append(u"s *noevent*")

    res.append(u"</s> *noevent*")

    outfh = codecs.open("ptemp7.txt","w", "utf-8")
    outfh.write(u"\n".join(res))
    outfh.close()

    return u"\n".join(res)


def runSRILMdiacritics(bama_map):
    outfh = codecs.open("ptemp7.txt", "w", "utf-8")
    outfh.write(bama_map)
    outfh.close()

    os.system("./ngram/hidden-ngram -lm ./ngram/DiacNgrams/ngram5.txt -order 5 -text-map ptemp7.txt -hidden-vocab ./ngram/DiacNgrams/vocab.txt > ptemp8.txt")

    infh = codecs.open("ptemp8.txt", "r", "utf-8")
    srilm_diacritics = infh.read()
    infh.close()
    return srilm_diacritics


def cleanOutput(srilm_diacritics):
    #Trivial processing of the SRILM n-gram output.
    output = srilm_diacritics

    sys.stderr.write(u"BEFORE: " + output + u"\n")

    output = re.sub(u"<s> ", u"", output)
    output = re.sub(u" </s>", u"", output)
    #output = re.sub("</s>", "", output)
    #output = re.sub(@"[\s]", "", output)
    output = re.sub(u"\s", u"", output)
    output = re.sub(u"s", u" ", output)
    output = re.sub(u"<u>", u"", output)
    #output = re.sub("(.noevent.)", "", output)
    #output = re.sub("([\w])<([\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670]+)>", "$1$2", output)

    output = re.sub(u"(.)<([^>]+)>", u"\\1\\2", output)

    #For punctuation
    #sys.stderr.write("BEFORE: "+output+"\n")
    output = re.sub(u"unk<[^>]+>", u",", output)
    output = re.sub(u"unk", u",", output)


    sys.stderr.write(u"AFTER:  " + output + u"\n")

    #output = re.sub("[\\s]*(\\p{P})[\\s]*", " \1 ", output)
    output = re.sub(u"\s+", u" ", output)

    outfh = codecs.open("ptemp9.txt", "w", "utf-8")
    outfh.write(output)
    outfh.close()

    return output;





###########################################################################

def vocalise(ar_text, addCaseEndings):
    # 1a) preprocessBeforeBama > temp0.txt
    # 1) Run BAMA to get postags (In: arabic (w1256), Out: bw (w1252) (Det måste tydligen vara windows-1256 för att Bama ska fungera..)
    # aramorph.sh temp0.txt temp1.txt

    ar_text = preprocessBeforeBama(ar_text)
    #bama_pos = runBama(ar_text)
    bama_pos = runPyBama2(ar_text)
    sys.stderr.write("------BAMA output-----\n")
    sys.stderr.write(bama_pos)
    sys.stderr.write("\n----------------------\n")


    bama_pos = filterWithPreVocalised(ar_text, bama_pos)
    sys.stderr.write("---- After filtering ---\n")
    sys.stderr.write(bama_pos)
    sys.stderr.write("\n----------------------\n")

    #sys.exit()


    # 2a) convert format for srilm > temp2.txt
    # 2) run the hmm tagger "hidden-ngram.exe" to get the most likely sequence of tags
    # hidden-ngram_hb -lm POSNgrams/taggerNgram4.txt -order 4 -text-map temp2.txt -hidden-vocab POSNgrams/vocab.txt
    # 2b) removeSentenceBoundaries > temp3.txt
    
    srilm_pos = convertBamaToSrilm(bama_pos)
    sys.stderr.write("-----SRILM input------\n")
    sys.stderr.write(srilm_pos)
    sys.stderr.write("\n----------------------\n")
    
    srilm_pos = runSRILM(srilm_pos)
    #sys.stderr.write("-----SRILM output-----\n")
    #sys.stderr.write(srilm_pos)
    #sys.stderr.write("\n----------------------\n")
    
    srilm_pos = removeSentenceBoundaries(srilm_pos)
    sys.stderr.write("-----SRILM output-----\n")
    sys.stderr.write(srilm_pos)
    sys.stderr.write("\n----------------------\n")
    
    # 3a) preprocessBeforeBama > temp4.txt 
    # 3) Run BAMA again now with the tags (vad är det för skillnad mot 1? temp0 och temp4 är likadana. temp1 och temp5 är lite olika, men samma innehåll egentligen)
    # aramorphWithTags.sh temp4.txt temp5.txt
    # 3b) temp5+temp3 > temp6 (behåll bara rätt tag enligt temp3)
    
    #HB I don't see an important difference between aramorph.pl and aramorphWithTags.pl?
    #Trying to run the same again here. If it works, no need to run it twice?
    #No, ok now, but clean it up TODO
    #bama_pos = runBamaWithTags(ar_text)
    #bama_pos = runPyBama2(ar_text)
    sys.stderr.write("----- Bama output (2) -----\n")
    sys.stderr.write(bama_pos)
    sys.stderr.write("\n-------------------------\n")

    bama_filtered = filterBamaWithTags(bama_pos, srilm_pos, addCaseEndings)
    sys.stderr.write("-----Filtered output-----\n")
    sys.stderr.write(bama_filtered)
    sys.stderr.write("\n-------------------------\n")
    
    # 4a) createBAMAMap temp6 > temp7
    # 4) run diacritics ngram.
    # hidden-ngram_hb -lm DiacNgrams/ngram5.txt -order 5 -text-map temp7.txt -hidden-vocab DiacNgrams/vocab.txt
    # > temp8
    # 4b) mergeOutput (rensar utdata på taggar osv så bara vokaliserad text blir kvar)
    # > temp9
    
    bama_map = createBAMAMap(bama_filtered, ar_text)
    sys.stderr.write("----- Srilm input   -----\n")
    sys.stderr.write(bama_map)
    sys.stderr.write("\n-------------------------\n")
    
    srilm_diacritics = runSRILMdiacritics(bama_map)
    only_vocalised = cleanOutput(srilm_diacritics)
    return only_vocalised


################################################################



if len(sys.argv) > 1 and sys.argv[1] == "server":
    print "hejsan"
    from flask import Flask, request
    app = Flask(__name__)

    @app.route("/vocalise", methods=['GET'])
    def voc():
        ar_text = request.args.get('text', '')
        print "INPUT TEXT:", ar_text
#        if "o" in ar_text:
#            return ar_text
        res = []
        for ar_sent in ar_text.split(u"."):
            res.append(vocalise(ar_sent.strip(), True))
        return ". ".join(res)

    if __name__ == "__main__":
        app.run(debug=True, port=8080)

#else:
    #ar_text = u"كتب الطفل الوظيفة"
    #ar_text = sys.stdin.read()
    #ar_text = codecs.getreader("utf-8")(sys.stdin).read().strip()
    #vocalised = vocalise(ar_text, True)
    #print vocalised

