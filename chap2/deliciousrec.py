#!/usr/bin/env python
# -*- encoding=utf-8 -*-

import time
import random
from recommendations import *
from pydelicious import *

def initializeUserDict(tag, count=5):
    user_dict = {}
    
    for p1 in get_popular(tag=tag)[0:count]:
        for p2 in get_urlposts(p1['url']):
            user_dict[p2['user']] = {}
    return user_dict

def fillItems(user_dict):
    all_items = {}

    for user in user_dict:
        posts = []
        for i in range(3):
            try:
                posts = get_userposts(user)
                break
            except:
                print "Failed user "+user+", retrying"
                time.sleep(4)

        for p in posts:
            url = p['url']
            user_dict[user][url] = 1.0
            all_items[url] = 1

    for user in user_dict:
        for item in all_items:
            if item not in user_dict[user]:
                user_dict[user][item] = .0

def test():
    delusers = initializeUserDict('programming')
    fillItems(delusers)
    user = delusers.keys()[random.randint(0, len(delusers)-1)]
    print topMatches(delusers, user)
    print getRecommendations(delusers, user)[0:10]
