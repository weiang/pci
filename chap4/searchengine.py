#!/usr/bin/env python
# -*- encoding=utf-8 -*-

import re
import urllib2
from BeautifulSoup import *
from urlparse import urljoin
import sqlite3 as sqlite

ignorewords = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])

class crawler:
    # Initialize the crawler with the name of database
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def dbcommit(self):
        self.con.commit()

    def getentryid(self, table, field, value, createnew=True):
        query = "select rowid from %s where %s='%s'" %(table, field, value)
#        print "Query:" + query
        cur = self.con.execute(query)
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            query = "insert into %s(%s) values ('%s')" %(table, field, value)
            cur = self.con.execute(query)
            # print "Rowid:%d" % cur.lastrowid
            return cur.lastrowid 

    # Index an individual page
    def addtoindex(self, url, soup):
        if self.isindexed(url):
            return
        print 'Indexing ' + url

        text = self.gettextonly(soup)
        words = self.separatewords(text)

        urlid = self.getentryid('urllist', 'url', url)

        for i in range(len(words)):
            word = words[i]
            # print "Word: " + word
            wordid = self.getentryid('wordlist', 'word', word)
            query = "insert into wordlocation(urlid, wordid, location) values (%d, %d, %d)" %(urlid, wordid, i)
            self.con.execute(query)

    def gettextonly(self, soup):
        v = soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += (subtext + '\n')
            return resulttext
        else:
            return v.strip()

    def separatewords(self, text):
        splitter = re.compile(r'\W*')
        result = [s.lower() for s in splitter.split(text) if s != '']
        return result

    def isindexed(self, url):
        query = "select rowid from urllist where url='%s'" %(url)
        result = self.con.execute(query).fetchone()
        if result != None:
            query = "select * from wordlocation where urlid='%d'" %(result[0])
            result = self.con.execute(query).fetchone()
            if result != None:
                return True
        return False

    def addlinkref(self, urlFrom, urlTo, linkText):
        fromid = self.getentryid('urllist', 'url', urlFrom)
        toid = self.getentryid('urllist', 'url', urlTo)
        if fromid == toid:
            return
        cur = self.con.execute("insert into link(fromid, toid) values (%d, %d)" %(fromid, toid))
        linkid = cur.lastrowid

        words = self.separatewords(linkText)
        for word in words:
            if word in ignorewords:
                continue
            wordid = self.getentryid('wordlist', 'word', word)
            self.con.execute("insert into linkwords(linkid, wordid) values (%d, %d)" %(linkid, wordid))

    def crawl(self,pages,depth=2):
        for i in range(depth):
            newpages=set()
            for page in pages:
                try:
                    c=urllib2.urlopen(page)
                except:
                    print "Could not open %s" % page
                    continue
                soup=BeautifulSoup(c.read())
                self.addtoindex(page,soup)
                links=soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url=urljoin(page,link['href'])
                        if url.find("'")!=-1: continue
                        url=url.split('#')[0] # remove location portion
                        if url[0:4]=='http' and not self.isindexed(url):
                            newpages.add(url)
                            linkText=self.gettextonly(link)
                            self.addlinkref(page,url,linkText)
                self.dbcommit()
            pages = newpages


    def createindextables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid, wordid, location)')
        self.con.execute('create table link(fromid integer, toid integer)')
        self.con.execute('create table linkwords(wordid, linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.dbcommit()

class searcher:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()
    
    def dbcommit(self):
        self.con.commit()

    def getmatchrows(self, q):
        fieldlist = 'w0.urlid'
        tablelist = ''
        clauselist = ''
        wordids = []
        tablenumber = 0

        words = q.split(' ')
        # print words
        for word in words:
            query = "select rowid from wordlist where word='%s'" % (word)
            wordrow = self.con.execute(query).fetchone()
            if wordrow == None:
                continue
            wordid = wordrow[0]
            wordids.append(wordid)
            if tablenumber > 0:
                tablelist += ','
                clauselist += 'and w%d.urlid=w%d.urlid and ' % (tablenumber-1, tablenumber)

            fieldlist += ', w%d.location' % (tablenumber)
            tablelist += ' wordlocation w%d' % (tablenumber)
            clauselist += 'w%d.wordid=%d ' %(tablenumber, wordid)
            tablenumber += 1
        fullquery = 'select %s from %s where %s' % (fieldlist, tablelist, clauselist)
        print fullquery
        cur = self.con.execute(fullquery)
        rows = [row for row in cur]

        return rows, wordids

    def getscoredlist(self, rows, wordids):
        totalscores = dict([(row[0], 0) for row in rows])

        weights = [(1.0, self.frequencyscore(rows)), 
                   (1.5, self.locationscore(rows)),
                   (1.0, self.distancescore(rows)),
                   (1.5, self.inboundlinkscore(rows))]

        for (weight, scores) in weights:
            for url in totalscores:
                totalscores[url] += weight * scores[url]

        return totalscores

    def geturlname(self, id):
        q = "select url from urllist where rowid=%d" % (id)
        cur = self.con.execute(q).fetchone()
        return cur[0]

    def query(self, q):
        rows, wordids = self.getmatchrows(q)
        scores = self.getscoredlist(rows, wordids)
        rankedscores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
        for (urlid, score) in rankedscores[0:10]:
            print '%s\t%f' % (self.geturlname(urlid), score)

    def normalizescores(self, scores, smallIsBetter=False):
        vsmall = 0.00001
        if smallIsBetter:
            minscore = min(scores.values())
            result = [(key, float(minscore)/max(value, vsmall)) for (key, value) in scores.items()]
            return dict(result)
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            result = [(key, float(value)/maxscore) for (key, value) in scores.items()]
            return dict(result)
    
    def frequencyscore(self, rows):
        counts = dict([(row[0], 0) for row in rows])

        for row in rows:
            counts[row[0]] += 1
        return self.normalizescores(counts)
    
    def locationscore(self, rows):
        locations = dict([(row[0], 100000) for row in rows])

        for row in rows:
            loc = sum(row[1:])
            if loc < locations[row[0]]:
                locations[row[0]] = loc
        return self.normalizescores(locations, smallIsBetter=True)

    def distancescore(self, rows):
        if len(rows[0]) <= 2:
            return dict([(row[0], 1.0) for row in rows])

        mindistance = dict([(row[0], 100000) for row in rows])

        for row in rows:
            dist = sum([abs(row[i] - row[i-1]) for i in range(2, len(row))])
            if dist < mindistance[row[0]]:
                mindistance[row[0]] = dist
        return self.normalizescores(mindistance, smallIsBetter=True)
    
    def inboundlinkscore(self, rows):
        uniqueurls = set([row[0] for row in rows])

        inboundcount = {}
        for urlid in uniqueurls:
            query = "select count(*) from link where toid=%d" % (urlid)
            cur = self.con.execute(query).fetchone()
            inboundcount[urlid] = cur[0]
        return self.normalizescores(inboundcount)
    
    def calculatepagerank(self, iterations=20):
        self.con.execute('drop table if exists pagerank')
        self.con.execute('create table pagerank(urlid primary key, score)')

        self.con.execute('insert into pagerank select rowid, 1.0 from urllist')
        self.dbcommit()
        
        for i in range(iterations):
            print "Iteration %d" % (i)
            for (urlid,) in self.con.execute('select rowid from urllist'):
                pr = 0.15
                for (linker,) in self.con.execute('select fromid from link where toid=%d' % (urlid)):
                    score = self.con.execute('select score from pagerank where urlid=%d' % (linker)).fetchone()[0]
                    linkcount = self.con.execute('select count(*) from link where fromid=%d' % (linker)).fetchone()[0]
                    pr += 0.85 * score / linkcount
                self.con.execute('update pagerank set score=%f where urlid=%d' % (pr, urlid))
            self.dbcommit()

def init_sqlite():
    pagelist = ["https://www.haskell.org/", "http://en.wikipedia.org/wiki/Haskell", "http://en.wikipedia.org/wiki/Functional_programming"]
    c = crawler('searchindex.db')
    c.crawl(pagelist)
    e = searcher('searchindex.db')
    e.calculatepagerank()

def test():
    # init_sqlite()
    e = searcher('searchindex.db')
    print e.query('functional programming')

if __name__ == '__main__':
    test()
