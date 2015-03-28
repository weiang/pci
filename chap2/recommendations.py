#!/usr/bin/env python
# -*- encoding=utf-8 -*-

import math

critics={'Lisa Rose': {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.5,
     'Just My Luck': 3.0, 'Superman Returns': 3.5, 'You, Me and Dupree': 2.5,
      'The Night Listener': 3.0},
      'Gene Seymour': {'Lady in the Water': 3.0, 'Snakes on a Plane': 3.5,
           'Just My Luck': 1.5, 'Superman Returns': 5.0, 'The Night Listener': 3.0,
            'You, Me and Dupree': 3.5},
      'Michael Phillips': {'Lady in the Water': 2.5, 'Snakes on a Plane': 3.0,
           'Superman Returns': 3.5, 'The Night Listener': 4.0},
      'Claudia Puig': {'Snakes on a Plane': 3.5, 'Just My Luck': 3.0,
           'The Night Listener': 4.5, 'Superman Returns': 4.0,
            'You, Me and Dupree': 2.5},
      'Mick LaSalle': {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
           'Just My Luck': 2.0, 'Superman Returns': 3.0, 'The Night Listener': 3.0,
            'You, Me and Dupree': 2.0},
      'Jack Matthews': {'Lady in the Water': 3.0, 'Snakes on a Plane': 4.0,
           'The Night Listener': 3.0, 'Superman Returns': 5.0, 'You, Me and Dupree': 3.5},
      'Toby': {'Snakes on a Plane':4.5,'You, Me and Dupree':1.0,'Superman Returns':4.0}}

def sim_distance(prefs, person1, person2):
    si = {}
    for item in prefs[person1]:
        if item in prefs[person2]:
            si[item] = 1

    if len(si) == 0:
        return 0

    sum_of_squares = sum([math.pow(prefs[person1][item]-prefs[person2][item], 2) for item in si])

    return 1 / (1 + math.sqrt(sum_of_squares))

def sim_pearson(prefs, p1, p2):
    si = {}
    for item in prefs[p1]:
        if item in prefs[p2]:
            si[item] = 1
    n = len(si)
    if n == 0:
        return 1

    sum1 = sum([prefs[p1][item] for item in si])
    sum2 = sum([prefs[p2][item] for item in si])
    sum1Sq = sum([math.pow(prefs[p1][item], 2) for item in si])
    sum2Sq = sum([math.pow(prefs[p2][item], 2) for item in si])
    pSum = sum([prefs[p1][item] * prefs[p2][item] for item in si])

    num = pSum - sum1 * sum2 / n
    den = math.sqrt((sum1Sq - math.pow(sum1, 2) / n) * (sum2Sq - math.pow(sum2, 2) / n))
    if abs(den) < 0.000001:
        return 0
    r = num / den
    return r

def topMatches(prefs, person, n=5, similarity=sim_pearson):
    scores = [(similarity(prefs, person, other), other) for other in prefs if other != person]

    scores.sort()
    scores.reverse()
    return scores[0:n]

def getRecommendations(prefs, person, similarity=sim_pearson):
    totals = {}
    simSums = {}
    
    simPeople = topMatches(prefs, person, similarity=similarity)
    for sim, p in simPeople:
        for item in prefs[p]:
            if item not in prefs[person] or prefs[person][item] == 0:
                totals.setdefault(item, 0)
                totals[item] += sim * prefs[p][item]
                simSums.setdefault(item, 0)
                simSums[item] += sim

    average_rate = [(totals[item] / simSums[item], item) for item in totals]
    average_rate.sort()
    average_rate.reverse()
    return average_rate

def transformPrefs(prefs):
    result = {}
    for person in prefs:
        for item in prefs[person]:
            result.setdefault(item, {})
            result[item][person] = prefs[person][item]
    return result

def calculateSimilarItems(prefs, n=10):
    result = {}

    itemPrefs = transformPrefs(prefs)
    c = 0
    for item in itemPrefs:
        c += 1
        if c % 100 == 0:
            print "%d / %d" %(c, len(itemPrefs))
        scores = topMatches(itemPrefs, item, n=n, similarity=sim_distance)
        result[item] = scores
    return result

def getRecommendedItems(prefs, itemMatch, user):
    userRatings = prefs[user]
    scores = {}
    totalSim = {}

    for item in userRatings:
        for (sim, relatedItem) in itemMatch[item]:
            if relatedItem in userRatings:
                continue
            scores.setdefault(relatedItem, 0)
            scores[relatedItem] += userRatings[item] * sim
            totalSim.setdefault(relatedItem, 0)
            totalSim[relatedItem] += sim

    rankings = [(scores[item] / totalSim[item], item) for item in totalSim]

    rankings.sort()
    rankings.reverse()
    return rankings

def loadMovieLens(path='.'):
    movies = {}
    for line in open(path+'/u.item'):
        (id, title) = line.split('|')[0:2]
        movies[id] = title

    prefs = {}
    for line in open(path+'/u.data'):
        (user, movieid, rating, ts) = line.split('\t')
        prefs.setdefault(user, {})
        prefs[user][movies[movieid]] = float(rating)
    return prefs
    
def test():
#    print sim_distance(critics, 'Lisa Rose', 'Gene Seymour')
#    print sim_pearson(critics, 'Lisa Rose', 'Gene Seymour')
#    print topMatches(critics, 'Toby', n=3)
#    print getRecommendations(critics, 'Toby')
#    print getRecommendations(critics, 'Toby', similarity=sim_distance)
#    movies = transformPrefs(critics)
#    print movies
#    print topMatches(movies, 'Superman Returns')
#    print getRecommendations(movies, 'Just My Luck')
    itemsim = calculateSimilarItems(critics)
    print itemsim
    print ''
    print getRecommendedItems(critics, itemsim, 'Toby')

def testMovieLens():
    prefs = loadMovieLens()
    print prefs['87']
    print getRecommendations(prefs, '87')[0:30]
    itemsim = calculateSimilarItems(prefs, n=50)
    print getRecommendedItems(prefs, itemsim, '87')[0:30]

if __name__ == '__main__':
    test()
    testMovieLens()
