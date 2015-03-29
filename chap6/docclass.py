#!/usr/bin/env python
# -*- encoding=utf-8 -*-

import re
import math
import nn
import sqlite3 as sqlite

def getwords(doc):
    splitter = re.compile('\W*')
    words = [s.lower() for s in splitter.split(doc) if len(s) > 2 and len(s) < 20 ]

    return dict([(w, 1) for w in words])

class classifier:
    def __init__(self, getfeatures, clsifier=None, filename=None):
        # Counts of feature/category combinations
        self.fc = {}
        # Counts of documents in each category 
        self.cc = {}
        self.getfeatures = getfeatures
        self.clsifier = clsifier

    # Increase the count of a feature/category pair
    def incf(self, f, c):
        self.fc.setdefault(f, {})
        self.fc[f].setdefault(c, 0)
        self.fc[f][c] += 1

    # Increase the count of a category
    def incc(self, c):
        self.cc.setdefault(c, 0)
        self.cc[c] += 1

    # The number of times a feature has appeared in a category
    def fcount(self, f, c):
        if f in self.fc and c in self.fc[f]:
            return float(self.fc[f][c])
        return 0.0

    # The numuber of items in a category
    def catcount(self, c):
        if c in self.cc:
            return float(self.cc[c])
        return 0.0

    # The total number of items 
    def totalcount(self):
        return sum(self.cc.values())

    # The list of all categories
    def categories(self):
        return self.cc.keys()

    def train(self, item, cat):
        features = self.getfeatures(item)
        for f in features:
            self.incf(f, cat)
        self.incc(cat)
    
    # Calculate P(feature|category)
    def fprob(self, f, cat):
        if abs(self.catcount(cat)) < 0.000001:
            return 0
        result = self.fcount(f, cat) / self.catcount(cat)
        return result
    
    def weightedprob(self, f, cat, prf, weight=1.0, ap=0.5):
        if self.clsifier != None:
            ap = self.clsifier.weightedprob(f, cat, self.clsifier.fprob)
        # Calculate current probability
        basicprob = prf(f, cat)
        
        totals = sum([self.fcount(f, c) for c in self.categories()])
        bp = ((weight*ap) + (totals*basicprob)) / (weight+totals)
        return bp

class naivebayes(classifier):
    def __init__(self, getfeatures, clsifier=None):
        classifier.__init__(self, getfeatures, clsifier)
        self.thresholds = {}

    def setthreshold(self, cat, t):
        self.threshold[cat] = t

    def getthreshold(self, cat):
        if cat not in self.thresholds:
            return 1.0
        return self.threshold[cat]

    def docprob(self, item, cat):
        features = self.getfeatures(item)

        p = 1
        for f in features:
            p *= self.weightedprob(f, cat, self.fprob)
        return p
   
    # Calculate P(Doc|Cat) * P(Cat)
    def prob(self, item, cat):
        catprob = self.catcount(cat) / self.totalcount()
        docprob = self.docprob(item, cat)
        return catprob * docprob
    
    def classify(self, item, default=None):
        probs = {}
        maxprob = 0.0
        for cat in self.categories():
            probs[cat] = self.prob(item, cat)
            if probs[cat] > maxprob:
                maxprob = probs[cat]
                best = cat

        for cat in probs:
            if cat == best:
                continue
            if probs[best] < self.getthreshold(cat) * probs[cat]:
                return None
        return best

class neuralnetwork(classifier):
    def __init__(self, getfeatures, dbname='classifier.db', netdb='nn.db'):
        classifier.__init__(self, getfeatures)
        self.con = sqlite.connect(dbname)
        self.net = nn.searchnet(netdb)
        self.createtables()
    
    def __del__(self):
        self.con.close()

    def getentryid(self, table, field, value, createnew=True):
        query = "select rowid from %s where %s='%s'" %(table, field, value)
        cur = self.con.execute(query)
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            query = "insert into %s(%s) values ('%s')" %(table, field, value)
            cur = self.con.execute(query)
        return cur.lastrowid 

    def createtables(self):
        self.con.execute('create table if not exists features(feature)')
        self.con.execute('create table if not exists categories(category)')
        self.con.commit()
    
    def train(self, item, c):
        self.incc(c)
        featureids = []
        features = self.getfeatures(item)
        for f in features:
            featureids.append(self.getentryid('features', 'feature', f))

        catids = []
        for cat in self.categories():
            catids.append(self.getentryid('categories', 'category', cat))
        
        catid = self.getentryid('categories', 'category', c)
        self.net.trainquery(featureids, catids, catid)
    
    def classify(self, item):
        featureids = []
        features = self.getfeatures(item)
        for f in features:
            featureids.append(self.getentryid('features', 'feature', f))
        catids = []
        for cat in self.categories():
            catids.append(self.getentryid('categories', 'category', cat))
        nnres = self.net.getresult(featureids, catids)

        maxscore = 0.0
        for i in range(len(nnres)):
            if nnres[i] > maxscore:
                maxscore = nnres[i]
                best = i
        cur = self.con.execute("select category from categories where rowid=%d" % (catids[best])).fetchone()
        if cur != None:
            return cur[0]
        return None


def sampletrain(cl):
    cl.train('Nobody owns the water.','good')
    cl.train('the quick rabbit jumps fences','good')
    cl.train('buy pharmaceuticals now','bad')
    cl.train('make quick money at the online casino','bad')
    cl.train('the quick brown fox jumps','good')

def test():
    cl1 = classifier(getwords)
    sampletrain(cl1)
    print cl1.weightedprob('quick rabbit', 'good', cl1.fprob)
    cl2 = naivebayes(getwords, clsifier=cl1)
    sampletrain(cl2)
    print cl2.weightedprob('quick rabbit', 'good', cl2.prob)
    cl3 = neuralnetwork(getwords)
    sampletrain(cl3)
    print cl3.classify('quick buy')

if __name__ == '__main__':
    test()
