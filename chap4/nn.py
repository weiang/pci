#!/usr/bin/env python
# -*- encoding=utf-8 -*-

from math import tanh
import sqlite3 as sqlite

def dtanh(y):
    return 1.0-y*y

class searchnet:
    def __init__(self, dbname):
        self.con = sqlite.connect(dbname)

    def __del__(self):
        self.con.close()

    def maketables(self):
        self.con.execute('create table hiddennode(create_key)')
        self.con.execute('create table wordhidden(fromid, toid, strength)')
        self.con.execute('create table hiddenurl(fromid, toid, strength)')
        self.con.commit()

    def getstrength(self, fromid, toid, layer):
        if layer == 0:
            table = 'wordhidden'
        else:
            table = 'hiddenurl'

        res = self.con.execute('select strength from %s where fromid=%d and toid=%d' % (table, fromid, toid)).fetchone()
        if res == None:
            if layer == 0:
                return -0.2
            else:
                return 0
        return res[0]

    def setstrength(self, fromid, toid, layer, strength):
        if layer == 0:
            table = 'wordhidden'
        else:
            table = 'hiddenurl'

        res = self.con.execute('select rowid from %s where fromid=%d and toid=%d' % (table, fromid, toid)).fetchone()
        if res == None:
            query = 'insert into %s(fromid, toid, strength) values (%d, %d, %f)' % (table, fromid, toid, strength)
        else:
            rowid = res[0]
            query = 'update %s set strength=%f where rowid=%d' % (table, strength, rowid)
        self.con.execute(query)

    def generatehiddennode(self, wordids, urls):
        if len(wordids) > 3:
            return None
        createkey = '_'.join(sorted([str(wi) for wi in wordids]))
        query = "select rowid from hiddennode where create_key='%s'" % (createkey)
        res = self.con.execute(query).fetchone()
        if res == None:
            query = "insert into hiddennode(create_key) values ('%s')" % (createkey)
            cur = self.con.execute(query)
            hiddenid = cur.lastrowid
            for wordid in wordids:
                self.setstrength(wordid, hiddenid, 0, 1.0/len(wordids))
            for urlid in urls:
                self.setstrength(hiddenid, urlid, 1, 0.1)

            self.con.commit()
            
    def getallhiddenids(self, wordids, urlids):
        l1 = {}
        for wordid in wordids:
            query = "select toid from wordhidden where fromid=%d" % (wordid)
            cur = self.con.execute(query)
            for c in cur:
                l1[c[0]] = 1
        for urlid in urlids:
            query = "select fromid from hiddenurl where toid=%d" % (urlid)
            cur = self.con.execute(query)
            for c in cur:
                l1[c[0]] = 1

        return l1.keys()

    def setupnetwork(self, wordids, urlids):
        self.wordids = wordids
        self.urlids = urlids
        self.hiddenids = self.getallhiddenids(wordids, urlids)
        
        # node outputs
        self.ai = [1.0] * len(self.wordids)
        self.ah = [1.0] * len(self.hiddenids)
        self.ao = [1.0] * len(self.urlids)

        # create weights matrix
        self.wi = [[self.getstrength(fromid, toid, 0) for toid in self.hiddenids] for fromid in self.wordids]
        self.wo = [[self.getstrength(fromid, toid, 1) for toid in self.urlids] for fromid in self.hiddenids]

    def feedforward(self):
        # the only input are the query words
        for i in range(len(self.wordids)):
            self.ai[i] = 1.0

        # hidden activations
        for j in range(len(self.hiddenids)):
            sum = 0.0
            for i in range(len(self.wordids)):
                sum += self.ai[i] * self.wi[i][j]
            self.ah[j] = tanh(sum)
        
        # output activations
        for k in range(len(self.urlids)):
            sum = 0.0
            for j in range(len(self.hiddenids)):
                sum += self.ah[j] * self.wo[j][k]
            self.ao[k] = tanh(sum)

        return self.ao[:]

    def getresult(self, wordids, urlids):
        self.setupnetwork(wordids, urlids)
        return self.feedforward()

    def backPropagate(self, targets, N=0.5):
        # calculate errors for output
        output_deltas = [0.0] * len(self.urlids)
        for k in range(len(self.urlids)):
            error = targets[k] - self.ao[k]
            output_deltas[k] = dtanh(self.ao[k]) * error

        # calculate errors for hidden layer
        hidden_deltas = [0.0] * len(self.hiddenids)
        for j in range(len(self.hiddenids)):
            error = .0
            for k in range(len(self.urlids)):
                error += output_deltas[k] * self.wo[j][k]
            hidden_deltas[j] = dtanh(self.ah[j]) * error

        # update output weights
        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                change = output_deltas[k] * self.ah[j]
                self.wo[j][k] += N * change

        # update input weights
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                change = hidden_deltas[j] * self.ai[i]
                self.wi[i][j] += N * change

    def trainquery(self, wordids, urlids, selectedurl):
        # generate a hidden node if necessary
        self.generatehiddennode(wordids, urlids)

        self.setupnetwork(wordids, urlids)
        self.feedforward()
        targets = [0.0] * len(urlids)
        targets[urlids.index(selectedurl)] = 1.0
        error = self.backPropagate(targets)
        self.updatedatabase()
    
    def updatedatabase(self):
        for i in range(len(self.wordids)):
            for j in range(len(self.hiddenids)):
                self.setstrength(self.wordids[i], self.hiddenids[j], 0, self.wi[i][j])

        for j in range(len(self.hiddenids)):
            for k in range(len(self.urlids)):
                self.setstrength(self.hiddenids[j], self.urlids[k], 1, self.wo[j][k])
        self.con.commit()
def test():
    mynet = searchnet('nn.db')
#    mynet.maketables()
    wWorld, wRiver, wBank = 101, 102, 103
    uWorldBank, uRiver, uEarth = 201, 202, 203
    mynet.generatehiddennode([wWorld, wBank], [uWorldBank, uRiver, uEarth])
    for c in mynet.con.execute('select * from wordhidden'):
        print c
    for c in mynet.con.execute('select * from hiddenurl'):
        print c
    print mynet.getresult([wWorld, wBank], [uWorldBank, uRiver, uEarth])
    mynet.trainquery([wWorld, wBank], [uWorldBank, uRiver, uEarth], uWorldBank)
    print mynet.getresult([wWorld, wBank], [uWorldBank, uRiver, uEarth])

if __name__ == '__main__':
    test()
