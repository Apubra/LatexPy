#! /usr/bin/env python2

'''Utility to interactively index Latex books 
   Copyright 2015-2018 by Kevin A. Straight <longhunt@yahoo.com> under the
   terms of the GNU public license.'''

VERSION_CODE = "0.40"       #current version of imbrowse

import string
import subprocess
import sys
import os


#OpenSUSE and some others do not install the curses library by default
#so we'd better check that it is there
try:
    import curses
except:
    print ("ERROR: Curses library not found.  Please use your OS's package ")
    print ("manager to install it.  It's probably called 'python-curses'")
    print ("or something similar.")

#get locale info for string encoding
import locale
locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def file_copy(f_from, f_to):
    ''' copies one text file into another
        we have to do this instead of just calling shutil.copy() because Android
        doesn't always let you change/copy file permissions '''

    assert f_from != f_to

    with open(f_from, "r") as f1:
        with open(f_to, "w") as f2:
            f2.write(f1.read())


def log_d (string):
    ''' Just a logger for debugging. '''

    with open("imbrowse.log", "a") as log:
        log.write(str(string)+"\n")


def unique (L):
    ''' returns only unique elements of a list.  I'm pretty sure there is a standard
        library function for this but I can't find it right now. '''

    while max([L.count(x) for x in L]) > 1:
        for l in L:
            if L.count(l) > 1:
                L.remove(l)

    return L


def grep(file_pat, search_pat, recurse=True, max_len=80, exclude=None):
    ''' Kinda like the shell command (but more limited)
        searches for string search_pat within files file_pat

        file_pat can contain shell paterns (*, ?, [])

        if recurse=True will descend into subfolders

        max_len is the maximum length of line to return

        if the argument exclude is given then no line that contains
        that string will be returned.'''

    import glob

    return_list = []


    file_list = glob.glob(file_pat) 
    if recurse:
        file_list += [X for X in 
              glob.glob(file_pat[:file_pat.rfind(".")*file_pat.rfind(".")>0]) if os.path.isdir(X)]

    
    for s_file in file_list:
        if  os.path.isdir(s_file):
            return_list = return_list + grep(s_file +"/"+file_pat, search_pat, max_len=max_len, exclude=search_pat+"\\index")

        else:
            with open (s_file, "r") as f:

                buff = f.readlines()

                for line in buff:
                    if search_pat.lower() in line.lower():
                        if exclude != None:
                            if not (exclude.lower() in line.lower()):
                                return_list.append((s_file, line[:max_len]))
                        else:
                            return_list.append((s_file, line[:max_len]))

    return return_list



def cwin_flow(tstring, win, hilight="-1", w=None):
    ''' "flows" a text string into a curses window '''

    from math import floor

    rows, cols = win.getmaxyx()

    tstring = tstring.replace('\n', ' ')
    tstring = tstring.replace('\r', ' ')
    tstring = tstring.replace('\t', ' ')

    offset = len(tstring) - len(tstring[tstring.find(" "):].lstrip())
    tstring = tstring[tstring.find(" "):].lstrip()

    if len(tstring) > rows*cols:
        tstring = tstring[:rows*cols]
    while len(tstring) < rows*cols:
        tstring = tstring+' '

    for i in range(rows-1):
        win.addstr(i,0,tstring[i*cols:i*cols+cols])

    if hilight != -1 and w != None:
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        h0 = hilight - offset
        try:
            win.addstr(int(floor(float(h0)/cols)), h0 % cols, w, curses.A_BOLD | curses.color_pair(4))
        except:
            pass

def i_write_changes(t, tf):
    ''' back up the old .tex file and write the new one after index tags have been inserted '''

    #back-up the old file
    if not os.path.exists(t+"."+str(os.getpid())+".bu"):
        file_copy(t, t+"."+str(os.getpid())+".bu")

    with open(t, 'w') as tfileout:
        tfileout.write(tf)


def detex(a, tag):
    '''removes a given LaTex tag and its contents from a string'''

    if tag == "glossary":
        if a.find("\\glossary") == -1:
            return a

        while a.find("\\glossary") != -1:
            b, c  = a.split("\\glossary", 1)
            a = b + string.join(c.split("}",2)[2:], " ").replace("{", "")

    return a


def occurences(w, i, idx_wrds, stdscr):
    '''find all the occurences of a word, but ignore any that are inside a '\glossary{}' tag'''
    oc  = grep("*.tex", w, max_len=255, exclude=w+"\\index")

    oc = [o for o in oc if w in detex(o[1], "glossary")]

    return oc


def index_the_term(stdscr, fwin,  idx_wrds, w, w_entry, i, cursor=0):
    ''' for the current term, goes to each occurance in the .tex files and asks if they
        want to inset an index tag.  '''

    rows, cols = stdscr.getmaxyx()
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)

    iwin = curses.newwin(rows-3, cols-2, 2, 1)
    iwin.addstr(1,1,"Existing Text:",curses.A_BOLD)
    iwin.addstr(7,1,"Proposed Text:",curses.A_BOLD)
    iwin.addstr(13,(cols-2)/2-26, "(a)ccept", curses.A_REVERSE); iwin.addstr("  ")
    iwin.addstr("s(k)ip", curses.A_REVERSE); iwin.addstr("  ")
    iwin.addstr("(c)hange index entry", curses.A_REVERSE); iwin.addstr("  ")
    iwin.addstr("back to (m)enu", curses.A_REVERSE)
    iwin.addstr(14, (cols-2)/2-8, "(o)pen in editor", curses.A_REVERSE)

    iwin.refresh()

    ioldwin = curses.newwin(4,cols-6,5,3)
    ipropwin = curses.newwin(4,cols-6,11,3)

    snip_bytes = int(4*(cols-4) * .8)   # Conservative estimate of how big a snippet we can do


    tfiles = unique([X[0] for X in occurences(w, i, idx_wrds, stdscr)])

    for t in tfiles:

        iwin.insstr(1,50, t.rjust(max([20,cols-53])), curses.color_pair(3))
        iwin.refresh()

        snippet_s = 0
        snippet_e = 0

        tf_buff = " "                   #init this in case the file IO chokes
        with open(t, 'r') as tf_in:
            tf_buff = tf_in.read()
        if cursor == 0:
            cursor = tf_buff.lower().find(w.lower())
        if tf_buff.lower()[cursor:].startswith(w.lower()+"\\index"):
            cursor = 1+tf_buff.find("}", cursor)
            cursor = tf_buff.lower().find(w.lower(), cursor)


        while cursor != -1:

            snippet_s = max(0, cursor - (snip_bytes + len(w))/2)
            snippet_e = min(len(tf_buff)-1, cursor + (snip_bytes + len(w))/2)

            snippet = tf_buff[snippet_s: snippet_e]
            hilight = cursor - snippet_s
            cwin_flow(snippet, ioldwin, hilight=hilight, w=w)

            new_snippet = tf_buff[snippet_s: cursor+len(w)] + "\\index{" + w_entry + "}"
            new_snippet += tf_buff[cursor+len(w):snippet_e]
            cwin_flow(new_snippet, ipropwin, hilight=hilight, w=(w+"\\index{"+w_entry+"}"))

            ioldwin.refresh()
            ipropwin.refresh()



            while True:
                c = ioldwin.getch()

                # Change the entry for the index
                if c == ord('c'):

                    cwin = curses.newwin(4, cols-2, 8, 1)
                    cwin.addstr(2,2,"New entry: ")
                    cwin.refresh()
                    curses.curs_set(1)
                    curses.echo()
                    w_entry = cwin.getstr(2,2+len("New entry: "), cols-17)
                    curses.curs_set(0)
                    curses.noecho()
                    cwin.clear()
                    cwin.bkgd('.', curses.A_REVERSE)
                    cwin.refresh()
                    fwin.addstr(2,2,"Index entry: "+w_entry.strip())

                    w_entry = index_the_term(stdscr, fwin,  idx_wrds, w, w_entry, i, cursor=cursor)

                    break

                # Accept the tag for this occurence
                if c == ord('a'):

                    tf_buff = tf_buff[:snippet_s] + new_snippet + tf_buff[snippet_e:]
                    cursor += (len(new_snippet) - len(snippet))
                    cursor = tf_buff.lower().find(w.lower(), cursor+1)
                    while "\\glossary" in tf_buff[cursor-12:cursor]:
                        cursor = tf_buff.lower().find(w.lower(), cursor+1)

                    while tf_buff.lower()[cursor:].startswith(w.lower()+"\\index"):
                        cursor = 1+tf_buff.find("}", cursor)
                        cursor = tf_buff.lower().find(w.lower(), cursor)


                    break

                # Skip this occurance
                if c == ord('k'):

                    cursor = tf_buff.lower().find(w.lower(), cursor+1)
                    if cursor == -1:
                        break
                    while "\\glossary" in tf_buff[cursor-12:cursor]:
                        cursor = tf_buff.lower().find(w.lower(), cursor+1)

                    while tf_buff.lower()[cursor:].startswith(w.lower()+"\\index"):
                        cursor = 1+tf_buff.find("}", cursor)
                        cursor = tf_buff.lower().find(w.lower(), cursor)


                    break

                # Go back up to the main menu
                if c == ord('m'):

                    # Here write the changes we've made so far
                    i_write_changes(t, tf_buff)

                    i = sur_terms(i, idx_wrds, stdscr)
                    i = top_menu(i, stdscr, idx_wrds, w_entry=w_entry)

                    break

                # Open in editor
                if c == ord('o'):

                    #Figure out what line of the buffer we're on
                    edit_line = len(tf_buff[:cursor].splitlines())

                    i_write_changes(t, tf_buff)
                    result = subprocess.call("nano +"+str(edit_line)+" "+t, shell=True)  #FIXME - let them specify editor in a 
                                                                                         # config file
                                                                                        # FIXME - exception handle this

                    curses.noecho()

                    stdscr.clear()

                    header_str = '>>>  INDEXMEISTER BROWSER v'+VERSION_CODE+'  <<<'
                    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE) 
                    stdscr.addstr(0, (cols-len(header_str))/2, header_str, curses.color_pair(1) | curses.A_BOLD)

                    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
                    stdscr.addstr(0,0,str(i+1)+" / "+str(len(idx_wrds)), curses.color_pair(3))

                    stdscr.refresh()

                    w_entry = index_the_term(stdscr, fwin,  idx_wrds, w, w_entry, i, cursor=cursor)

                    break

    i_write_changes(t, tf_buff)

    return w_entry


def top_menu(i, stdscr, idx_wrds, w_entry=""):
    ''' Top level menu '''

    rows, cols = stdscr.getmaxyx()

    w = idx_wrds[i].replace("\n", "")

    if w_entry == "":
        w_entry = w

    header_str = '>>>  INDEXMEISTER BROWSER v'+VERSION_CODE+'  <<<'
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLUE)    
    stdscr.addstr(0, (cols-len(header_str))/2, header_str, curses.color_pair(1) | curses.A_BOLD)

    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    stdscr.addstr(0,0,str(i+1)+" / "+str(len(idx_wrds)), curses.color_pair(3))

    bwin = curses.newwin(rows-2, cols, 1,0)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_WHITE)
    bwin.bkgd('.', curses.color_pair(2))
    bwin.refresh()

    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    fwin=curses.newwin(6,cols-2,2,1)
    fwin.addstr(1,2,"Suggested index term: "); fwin.addstr(w, curses.color_pair(4) | curses.A_BOLD)
    fwin.addstr(2,2,"Index entry: ") ; fwin.addstr(w_entry, curses.color_pair(4))
    fwin.addstr(3,2,"(s)how occurences  (c)hange index entry  (d)elete  s(k)ip\n")
    fwin.addstr(4,2,"(b)ack  (i)ndex  (q)uit and save progress  aba(n)don changes\n")
    curses.curs_set(0)
    bwin.refresh()
    fwin.refresh()

    while True:
        c = stdscr.getch()

        # Show Occurances
        if c == ord('s'):
            stdscr.addstr('\r')
            try:
                results = grep("*.tex", w.replace("\n", ""), max_len=cols, exclude=w+"\\index")
            except:
                results = []

            gwin_length = min(rows-9, len(results))
            gwin = curses.newwin(gwin_length, cols-2, 8, 1)

            maxr = min(len(results), gwin_length)
            max_file_nm_len = max([len(x[0]) for x in results])

            for idx in range(maxr):

                gwin.addstr(idx, 2, results[idx][0].ljust(max_file_nm_len)+'  ')
                ww = cols-4-3-max_file_nm_len-20
                gwin.insstr(idx, 4+max_file_nm_len, results[idx][1][:ww])

                first_part = results[idx][1].lower().find(w.replace("\n", "").lower())
                hi_lit_part = results[idx][1][first_part:first_part + len(w.replace("\n", ""))]
                gwin.addstr(idx, 4+max_file_nm_len+first_part, hi_lit_part, curses.A_STANDOUT)

            gwin.refresh()


        # Change index entry
        if c == ord('c'):
            cwin = curses.newwin(4, cols-2, 8, 1)
            cwin.addstr(2,2,"New entry: ")
            cwin.refresh()
            curses.curs_set(1)
            curses.echo()
            w_entry = cwin.getstr(2,2+len("New entry: "), cols-17)
            curses.curs_set(0)
            curses.noecho()
            cwin.clear()
            cwin.bkgd('.', curses.A_REVERSE)
            cwin.refresh()
            fwin.addstr(2,2,"Index entry: "+w_entry.strip())

            i = sur_terms(i, idx_wrds, stdscr)
            i = top_menu(i, stdscr, idx_wrds, w_entry=w_entry)

            break


        # Delete this term
        if c == ord('d'):
            idx_wrds.remove(w+"\n")

            i = sur_terms(i, idx_wrds, stdscr)
            i = top_menu(i, stdscr, idx_wrds)

            break

        # Save and quit
        if c == ord('q'):

            with open(idx_wrds_path, 'w') as idx_wrds_file:
                idx_wrds_file.writelines(idx_wrds)

            # Neaten up bu files
            pid_str = str(os.getpid())
            top_dir = os.getcwd()

            file_lists = [x for x in os.walk(top_dir)]

            for dfl in file_lists:

                fwpid = [dfl[0]+os.sep+x for x in dfl[2] if pid_str in x]
                for file in fwpid:
                    os.rename (file, file.replace("."+pid_str+".bu", ".bu"))


            quit()

        # Skip to next term
        if c == ord('k'):
            i += 1
            if i > len(idx_wrds) - 1:
                i = 0

            i = sur_terms(i, idx_wrds, stdscr)
            i = top_menu(i, stdscr, idx_wrds)

            break

        # Back to previous term
        if c ==ord('b'):
            i -= 1
            if i < 0:
                i = len(idx_wrds) - 1

            i = sur_terms(i, idx_wrds, stdscr)
            i = top_menu(i, stdscr, idx_wrds)

            break

        # Abandon changes and exit
        if c == ord('n'):

            if really_abandon(stdscr):

                # Roll back changes of tex files
                pid_str = str(os.getpid())
                top_dir = os.getcwd()

                file_lists = [x for x in os.walk(top_dir)]

                for dfl in file_lists:

                    fwpid = [dfl[0]+os.sep+x for x in dfl[2] if pid_str in x]
                    for file in fwpid:
                        os.rename (file, file.replace("."+pid_str+".bu", ""))
                quit()

            else:
                i = sur_terms(i, idx_wrds, stdscr)
                i = top_menu(i, stdscr, idx_wrds)

        # Index this term
        if c == ord('i'):

            w_entry = index_the_term(stdscr, fwin, idx_wrds, w, w_entry, i)

            i = sur_terms(i, idx_wrds, stdscr)
            i = top_menu(i, stdscr, idx_wrds)

            break

    return i


def all_done(stdscr):
    ''' clean exit when we run out of terms '''
    rows, cols = stdscr.getmaxyx()

    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    ad_win = curses.newwin(3, cols-12, 9, 6)
    ad_win.insstr(1,1,"Finished indexing all terms.  Press any key to exit.".center(cols-14),
                        curses.color_pair(3) | curses.A_BOLD)

    with open(idx_wrds_path, 'w') as f:
        f.write("")

    c = ""
    while c == "":
        c = ad_win.getch()

    quit()

def really_abandon(stdscr):
    ''' prompts to see if they're sure they want to ditch '''

    rows, cols = stdscr.getmaxyx()

    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)
    ad_win = curses.newwin(3, cols-12, 9, 6)
    ad_win.insstr(1,1,"Really exit and abandon all changes? (Y/n)".center(cols-14),
                        curses.color_pair(3) | curses.A_BOLD)

    c = ""
    while c == "":
        c = ad_win.getch()
        if c == ord('y') or c == ord('Y'):
            return True

    return False


def sur_terms(i, idx_wrds, stdscr):
    ''' show surrounding terms at bottom of window '''

    if len(idx_wrds) < 1:      # Exit Cleanly when we run out of terms
        all_done(stdscr)

    rows, cols = stdscr.getmaxyx()
    if i > len(idx_wrds)-1:
        i = len(idx_wrds)-1
    w = idx_wrds[i].replace("\n", "")


    oc = occurences(w, i, idx_wrds, stdscr)  # If we can't find any of this word then skip it
    # If nothing comes up it means we're done with this term
    if len(oc) == 0:
        try:
            idx_wrds.remove(w+"\n")
        except:
            pass

        if i > len(idx_wrds)-1:
            i = len(idx_wrds)-1
        w = idx_wrds[i].replace("\n", "")

    stdscr.clear()
    stdscr.refresh()


    word_ind = [i-1, i, i+1, i+2]

    # handle wrapping back around
    if i == 0 or i == len(idx_wrds):
        i = 0
        word_ind = [-1,0,1,2]
    if i == -1 or i == len(idx_wrds)-1:
        i = len(idx_wrds)-1
        word_ind = [i-1,i,0,1]
    if i == -2 or i == len(idx_wrds)-2:
        i = len(idx_wrds)-2
        word_ind = [i-1,i,i+1,0]

    # handle when we have less than three terms left
    if len(idx_wrds) == 2:
        nterms = idx_wrds[word_ind[2]][:-1]+" -- "+idx_wrds[i][:-1]+" -- "+idx_wrds[word_ind[2]][:-1]
    elif len(idx_wrds) == 1:
        nterms = idx_wrds[i][:-1]
    else:
        nterms = idx_wrds[word_ind[0]][:-1]+" -- "+idx_wrds[i][:-1]+" -- "+idx_wrds[word_ind[2]][:-1]+" -- "+idx_wrds[word_ind[3]][:-1]

    #if this display string is too long then create a shorter one
    if len(nterms) > cols-2:
        nterms = idx_wrds[word_ind[0]][:-1]+" -- "+idx_wrds[i][:-1]+" -- "+idx_wrds[word_ind[2]][:-1]

    while len(nterms) > cols-2:
        if nterms.find("--") != -1:
            x1 = nterms.find(" -- ")
            nterms = nterms[:x1-1]+nterms[x1:-1]
        else:
            nterms = nterms[:cols-2]

    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    stdscr.addstr(rows-1,(cols-len(nterms))/2,nterms)
    stdscr.addstr(rows-1, (cols-len(nterms))/2+string.find(nterms,w), w, curses.A_BOLD | curses.color_pair(4))

    return i


def main_script(args):

    stdscr = curses.initscr()
    rows, cols = stdscr.getmaxyx()

    curses.start_color()

    if not os.path.exists(idx_wrds_path+".bu"):
        try:
            file_copy(idx_wrds_path, idx_wrds_path+".bu")

        except:
            pass

    with open(idx_wrds_path, 'r') as idx_wrds_file:
        idx_wrds = idx_wrds_file.readlines()

    i = 0
    while True:
        i = sur_terms(i, idx_wrds, stdscr)

        i = top_menu(i, stdscr, idx_wrds)

    with open(idx_wrds_path, 'w') as idx_wrds_file:
        idx_wrds_file.writelines(idx_wrds)

def unit_test():
    ''' A very minimal test suite, but for something like this we don't need much. 
        raises AssertionError and program won't run if any of these functions are
        broken '''


    # unique()
    c = unique(list("kevin straight is cool"))
    assert(c == ['k', 'e', 'v', 'n', 'r', 'a', 'g', 'h', 't', 'i', 's', ' ', 'c', 'o', 'l'])

    # detex()
    d = "The quick brown fox\\glossary{fox}{a small red dog} jumped the fence"
    assert(detex(d, "glossary") == "The quick brown fox jumped the fence")

    f = "You are a major tool\\glossary{tool}{another name for hoser}.  Also a hoser\\glossary{hoser}{what you are}."
    assert(detex(f, "glossary") == "You are a major tool.  Also a hoser.")


unit_test()    


    
#See if we're running Windoze and, if so, issue a warning.
if sys.platform == 'win32':
    print ("WARNING:  This program is untested--and most likely doesn't work--")
    print ("\ton Windows.  If you would like to help add Windows" )
    print ("\tcompatibility please get in touch with Kevin.")
    print
    raw_input("<ENTER> to continue...")
    
#process command line options
a = sys.argv

if len(a) > 1:
    if a[1] in ['help', '-h', '--help']:
        print ("Indexmeister Browser v"+VERSION_CODE+" - Interactive Indexer")
        print ("Copyright 2015-2018 by Kevin A. Straight <longhunt@yahoo.com>")
        print ("under the terms of the GNU Public License.")
        print
        print ("Usage:", a[0], "[text file]")
        print ("where [text file] is a list of possible index terms, one per line.")
        print
        print ("Invoke without any arguments to enter an interactive menu to")
        print ("index LaTex files.")
        print 
        
        quit()
    else:
        idx_wrds_path = a[1]
else:
    print ("Indexmeister Browser v"+VERSION_CODE+" - Interactive Indexer")
    print ("Copyright 2015-2018 by Kevin A. Straight <longhunt@yahoo.com>")
    print ("under the terms of the GNU Public License.")
    print
    print ("i - input a list if (i)ndex terms as a text file")
    print ("s - (s)can a LaTex file for suggested index terms")
    print ("q - (q)uit")
    c = ' '
    while c not in ['i','s','q']:
        c = raw_input('>').replace('\n', '')
        
    if c == 'q':
        quit()
        
    if c =='i':
        idx_wrds_path = raw_input('File name> ').replace('\n', '')
        
    if c == 's':
        texfile = raw_input('File name> ').replace('\n', '')
        print 
        print ('Capitalized phrases (i.e. proper nouns) will authomatically be detected.')
        print ("Do you also want to scan for terms that don't occur in the system dictionary")
        print ("(e.g. foreign and scientific words)?")
        dopt = raw_input("(y/N) >").replace('\n', '')
        print ("Do you also want to try to find words based on word frequency analysis?")
        fopt = raw_input("(y/N) >").replace('\n', '')
        
        optionstr = ' '
        if dopt in ['y', 'Y']:  optionstr = optionstr+'-d'
        if fopt in ['y', 'Y']:  optionstr = optionstr+'f'

        
        try:
            subprocess.call(['indexmeister '+texfile+optionstr+'> im_termlist.txt'], 
                        shell=True)
        except:
            try:
                subprocess.call(['./indexmeister '+texfile+optionstr+'> im_termlist.txt'], 
                        shell=True)
            except:
                print ("ERROR: Could not call indexmeister.  Please verify your installation.")
                quit()
    
        try:
            wc_str = subprocess.check_output(['wc -l im_termlist.txt'], shell=True)
            wc_str = wc_str[:string.find(wc_str, ' ')]
            print (wc_str, 'possible terms found.')
            
            if int(wc_str) < 1:
                print ("ERROR:  No index terms found in this file.")
                quit()

        except:
            pass
    
        print ("List of terms saved as im_termlist.txt")
        idx_wrds_path = 'im_termlist.txt'


curses.wrapper(main_script)
