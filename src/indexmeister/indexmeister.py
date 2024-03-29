#! /usr/bin/env python2
# -*- coding: utf-8 -*-


'''Utility to help index Latex books by suggesting possible index terms.
   Copyright 2015-2018 by Kevin A. Straight <longhunt@yahoo.com> under the
   terms of the GNU public license.'''
   
VERSION_CODE = "0.40"       #current version of indexmeister

import string, subprocess, sys, os

#List of the most common words in English books (based on a sample of
#Project Gutenberg texts)
common500 = ["the", "of", "and", "to", "a", "in", "that", "was", "he", 
"i", "it", "his", "is", "with", "as", "for", "had", "you", "be", "on", 
"not", "at", "but", "by", "her", "which", "this", "have", "from", 
"she", "they", "all", "him", "were", "or", "are", "my", "we", "one", 
"so", "their", "an", "me", "there", "no", "said", "when", "who", 
"them", "been", "would", "if", "will", "what", "out", "more", "up", 
"then", "into", "has", "some", "do", "could", "now", "very", "time", 
"man", "its", "your", "our", "than", "about", "upon", "other", "only", 
"any", "little", "like", "these", "two", "may", "did", "after", "see", 
"made", "great", "before", "can", "such", "should", "over", "us", 
"first", "well", "must", "mr", "down", "much", "good", "know", "where", 
"old", "men", "how", "come", "most", "never", "those", "here", "day", 
"came", "way", "own", "go", "life", "long", "through", "many", "being", 
"himself", "even", "shall", "back", "make", "again", "every", "say", 
"too", "might", "without", "while", "same", "am", "new", "think", 
"just", "under", "still", "last", "take", "went", "people", "away", 
"found", "yet", "thought", "place", "hand", "though", "small", "eyes", 
"also", "house", "years", "-", "another", "don't", "young", "three", 
"once", "off", "work", "right", "get", "nothing", "against", "left", 
"ever", "part", "let", "each", "give", "head", "face", "god", "0", 
"between", "world", "few", "put", "saw", "things", "took", "letter", 
"tell", "because", "far", "always", "night", "mrs", "love", "both", 
"sir", "why", "look", "having", "mind", "father", "called", "side", 
"looked", "home", "find", "going", "whole", "seemed", "however", 
"country", "got", "thing", "name", "among", "seen", "heart", "told", 
"done", "king", "water", "asked", "heard", "soon", "whom", "better", 
"something", "knew", "lord", "course", "end", "days", "moment", 
"enough", "almost", "general", "quite", "until", "thus", "hands", 
"nor", "light", "room", "since", "woman", "words", "gave", "b", 
"mother", "set", "white", "taken", "given", "large", "best", "brought", 
"does", "next", "whose", "state", "yes", "oh", "door", "turned", 
"others", "poor", "power", "present", "want", "perhaps", "death", 
"morning", "la", "rather", "word", "miss", "less", "during", "began", 
"themselves", "felt", "half", "lady", "full", "voice", "cannot", 
"feet", "order", "near", "true", "1", "it's", "matter", "stood", 
"together", "year", "used", "war", "till", "use", "thou", "son", 
"high", "round", "above", "certain", "often", "kind", "indeed", "i'm", 
"along", "case", "fact", "myself", "children", "anything", "four", 
"dear", "keep", "nature", "known", "point", "p", "friend", "says", 
"passed", "within", "land", "sent", "church", "believe", "girl", 
"city", "times", "form", "herself", "therefore", "hundred", "john", 
"wife", "fire", "several", "body", "sure", "money", "means", "air", 
"open", "held", "second", "gone", "already", "least", "alone", "hope", 
"thy", "chapter", "whether", "boy", "english", "itself", "2", "women", 
"hear", "cried", "leave", "either", "number", "rest", "child", 
"behind", "read", "lay", "black", "government", "friends", "became", 
"around", "river", "sea", "ground", "help", "c", "i'll", "short", 
"question", "reason", "become", "call", "replied", "town", "family", 
"england", "lost", "speak", "answered", "five", "coming", "possible", 
"making", "hour", "dead", "really", "looking", "law", "captain", 
"different", "manner", "business", "states", "earth", "st", "human", 
"early", "sometimes", "spirit", "care", "sat", "public", "close", 
"towards", "kept", "french", "party", "truth", "line", "strong", 
"book", "able", "later", "return", "hard", "mean", "feel", "story", 
"m", "received", "following", "fell", "wish", "person", "beautiful", 
"seems", "dark", "history", "followed", "subject", "thousand", "ten", 
"returned", "thee", "age", "turn", "fine", "across", "show", "arms", 
"character", "live", "soul", "met", "evening", "die", "common", 
"ready", "suddenly", "doubt", "bring", "ii", "red", "free", "that's", 
"account", "cause", "necessary", "can't", "need", "answer", "miles", 
"carried", "although", "fear", "hold", "interest", "force", 
"illustration", "sight", "act", "master", "ask", "idea", "ye", "sense", 
"an'", "art", "position", "rose", "3", "company", "road", "further", 
"nearly", "table"] 

#This is he ratio between the number of occurences of the 500th most
#common word in a large text sample and the occurences of the most
#common word in the sample.  Determined empiracly from a sample of 
#37,358 PG texts.
w_threshold = 0.0028429284   #Normalized word frequency threshold
w_sensitivity = 5


#See if we're running Windoze and, if so, issue a warning.
if sys.platform == 'win32':
    print ("WARNING:  This program is untested--and most likely doesn't work--")
    print ("\ton Windows.  If you would like to help add Windows" )
    print ("\tcompatibility please get in touch with Kevin.")

#Make sure either pandoc or detex is installed on the path
try:
    subprocess.check_output(['pandoc', '/dev/null'])
    
    usePandoc = True
except:
    usePandoc = False
    
if not usePandoc:
    
    try:
    
        result = subprocess.call(['detex', '/dev/null'])
        
            
    except Exception as e:
        print( e )
        print ("ERROR: either 'detex' or 'pandoc' is required and does not seem to be" )
        print ("properly installed.")
        print ("\t'detex' is available in most LaTex distributions.  Check with your" )
        print ("SysAdmin.")
        quit()  


#process command line options
a = sys.argv
if len(a)<2:
    print ("Indexmeister v"+VERSION_CODE)
    print ("Copyright 2015-2018 by Kevin A. Straight <longhunt@yahoo.com>")
    print ("under the terms of the GNU Public License")
    print ("Usage:  "+a[0]+" filename.tex [options]")
    print
    print ("Options:")
    print ("\t-d\tSuggest terms that don't occur in system dictionary")
    print ("\t-f\tSuggest words based on frequency of occurence")
    print ("\t\t\t\t\t(experimental)")
    print ("\t-x\tUse Detex as a back-end even if Pandoc is available")
    print ("\t-E\tDo NOT include words that are in LaTex '\emph{}' tags")
    print
    print ("Remember to spell-check your file before running!")

    
else:
    output_words = []

    if (len(a) == 2) or ('E' not in a[2]):
        #find terms that are contained in LaTex 'emph' tags
        with open(a[1], 'r') as rf:
            rawtex = rf.read()
    
        i = 0
        while i > -1:
            i = rawtex.find("\emph{", i)+6
            if i != 5:
                j = rawtex.find("}", i)
                w = rawtex[i:j]
                if w not in output_words:
                    output_words.append(w.title())
                
            else:
                i = -1            

    if len(a) > 2:  a[2]=' '.join(a[2:])    

    if len(a)>2:
        if 'x' in a[2]:
            #force use of Detex even if Pandoc is installed
            usePandoc = False
            
        if 'd' in a[2]:
            #use aspell to find words not in the dicitionary
            try:
                if usePandoc:
                    try:
                	    wordlist = subprocess.check_output("pandoc -t plain "+a[1]+" | aspell list", shell=True, stderr="/dev/null").split()
                    except:
                        wordlist = subprocess.check_output("pandoc -t plain "+a[1]+" | hunspell -l", shell=True, stderr="/dev/null").split()
                else:
                    try:
                        wordlist = subprocess.check_output("detex "+a[1]+" | aspell list", shell=True, stderr="/dev/null").split()
                    except:
                        wordlist = subprocess.check_output("detex "+a[1]+" | hunspell -l", shell=True, stderr="/dev/null").split()

                #find unique words
                unique_words = []
                for w in wordlist:
                    if w not in unique_words: unique_words.append(w)
                    
                output_words=output_words+unique_words
            except:
                pass #skip this step if can't find aspell
                
    #find capitalized words and phrases and phrases that don't start a sentence
                        
    if usePandoc:
        
            rawtexfile = subprocess.check_output(
                        "pandoc -t plain "+a[1],
                        shell=True).replace('—', '; ').replace('–',': ').replace('’', '')


    else:
        rawtexfile = subprocess.check_output(["detex", 
                        a[1]]).replace('---', '; ').replace('--',' ')
                        
    

    
    rawtexfile = rawtexfile.split()                    
 
    for j in range(len(rawtexfile)):
        w = rawtexfile[j]
    
        if '-' in w:
            i = w.rfind('-')
            if i < (len(w)-1):
                if w[i].islower():
                    rawtexfile[j] = w[:i]
    
    
    #exclude junk text that Detex leaves in (user modifiable)
    try:
        with open('/home/'+os.getlogin()+'/.indexmeister-exclude', 'r') as efile:
            ex_stuff = [x[:-1] for x in efile.readlines() if x[0] != '#']
    except:
        ex_stuff = []
    
    texfile=[]
    for i in range(len(rawtexfile)):
        for x in ex_stuff:
            rawtexfile[i] = rawtexfile[i].replace(x, '')
        if len(rawtexfile[i]) > 0:
            texfile.append(rawtexfile[i])
                
    
    j=0
    for i in range(1, len(texfile)-1):
        if j>0:
            j-=1
        else:
            if texfile[i][0].isupper():
                if not texfile[i-1].endswith('.'):
                    t = texfile[i]
                    j=1
                    while t[len(t)-1] not in '.;:,-"!?)_' and texfile[i+j][0].isupper():
                        t=t+' '+texfile[i+j]
                        j+=1
                        
                    #get rid of terminal punctuation    
                    while t[len(t)-1] in '.;:,-"!?)': 
                        t = t[:len(t)-1]
                    while t[len(t)-1] in "'": 
                        t = t[:len(t)-1]    
                        
                    #get rid of possessive
                    if t.endswith("'s"):
                        t = t[:len(t)-2]
                        
                                            
                    if t not in output_words:  
                        if t.endswith('s'):     #get rid of regular 
                                                #plurals (doesn't always work)
                            if t[:len(t)-1] in output_words:
                                pass
                        else:
                            if t not in 'AI':   
                                output_words.append(t)
                            
                else: j=0
    
    
    
    
    #Find words that occur more frequently in this file than they do in
    #most books.
    if (len(a)>2) and 'f' in a[2]:
        
        wordcounts = {}
        
        for w in texfile:
            w2 = string.join([c for c in w if c not in string.punctuation], '').lower() 
            if w2 not in common500:
                if w2 not in wordcounts:  
                    wordcounts[w2] = 1.0
                else:
                    wordcounts[w2] += 1.0
                        
        for w2 in wordcounts:
            if wordcounts[w2]/max(wordcounts.values()) > w_threshold*w_sensitivity:
                if wordcounts[w2] > 5 and wordcounts[w2] < 50:
                    if w2.capitalize() not in output_words:
                        output_words.append(w2)
                            
    output_words.sort()
    
    for u in output_words: 
        if u.lower() not in common500:  #Try to eliminate "stop words" 
            pass
            print (u)